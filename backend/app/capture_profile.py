"""Explicit request parameters and provenance for manually captured market photos."""
from datetime import date, timedelta
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HotelCaptureProfile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    checkIn: date
    nights: int = Field(default=7, ge=1, le=30)
    adults: int = Field(default=2, ge=1, le=10)
    rooms: Literal[1] = 1  # Public room/night metrics currently support one room.
    children: Literal[0] = 0  # Child ages are not supported by this form yet.
    currency: Literal['EUR'] = 'EUR'
    board: Literal['all_inclusive', 'saved_filters'] = 'all_inclusive'


def effective_search_url(source_url, profile=None):
    url = urlsplit(source_url)
    host = (url.hostname or '').lower()
    if url.scheme not in ('https', 'http') or not (host == 'booking.com' or host.endswith('.booking.com')) or url.username or url.password:
        raise ValueError('La captura requiere una URL de búsqueda de Booking.com.')
    params = parse_qs(url.query, keep_blank_values=True)
    # Both backends receive exactly the URL that is saved in the photo.
    params['selected_currency'] = ['EUR']
    if profile is not None:
        if profile.checkIn < date.today():
            raise ValueError('La fecha de entrada no puede estar en el pasado.')
        params.update(checkin=[profile.checkIn.isoformat()],
                      checkout=[(profile.checkIn + timedelta(days=profile.nights)).isoformat()],
                      group_adults=[str(profile.adults)], group_children=['0'], no_rooms=[str(profile.rooms)])
        params.pop('age', None)
        if profile.board == 'all_inclusive':
            filters = [f for value in params.get('nflt', []) for f in value.split(';') if f and not f.startswith('mealplan=')]
            params['nflt'] = [';'.join(filters + ['mealplan=4'])]
    return urlunsplit((url.scheme, url.netloc, url.path, urlencode(params, doseq=True), ''))


def profile_from_url(source_url, *, origin='legacy_url'):
    """Describe recorded parameters; absent parameters remain unknown."""
    params = parse_qs(urlsplit(source_url).query)
    def one(key):
        values = params.get(key, [])
        return values[0] if len(values) == 1 else None
    def integer(key):
        try:
            return int(one(key))
        except (ValueError, TypeError):
            return None
    checkin, checkout = one('checkin'), one('checkout')
    try:
        nights = (date.fromisoformat(checkout) - date.fromisoformat(checkin)).days
    except (ValueError, TypeError):
        nights = None
    return dict(origin=origin, checkIn=checkin, checkOut=checkout, nights=nights,
                adults=integer('group_adults'), children=integer('group_children'), rooms=integer('no_rooms'),
                currency=one('selected_currency'), filters=params.get('nflt', []), childAges=params.get('age', []))
