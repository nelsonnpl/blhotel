from __future__ import annotations

from datetime import date
import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from .models import MarketHotelRow


def parse_booking_search_results(html: str, source_url: str) -> list[MarketHotelRow]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[data-testid='property-card']")
    check_in, check_out, nights = _extract_dates(source_url)
    coord_index = _build_coord_index(html)

    rows: list[MarketHotelRow] = []
    for index, card in enumerate(cards, start=1):
        title = _clean(_first_text(card, "[data-testid='title']")) or "Hotel sin nombre"
        detail_href = _first_attr(card, "[data-testid='title-link']", "href")
        detail_url = _normalize_booking_url(detail_href, source_url) or source_url
        price_text = _clean(_first_text(card, "[data-testid='price-and-discounted-price']")) or _clean(
            _first_text(card, "[data-testid='price-for-x-nights']")
        )
        room_type = _clean(_first_text(card, "[data-testid='recommended-units']"))
        rating_text = _clean(_first_text(card, "[data-testid='review-score']"))
        pax_text = _clean(_first_text(card, "[data-testid='price-for-x-nights']")) or room_type

        card_text = card.get_text(" ", strip=True)
        price = _parse_price(price_text)
        price_per_night = round(price / nights, 2) if price is not None and nights else None
        pax = _parse_pax(pax_text) or _parse_pax(card_text)
        price_per_person_night = round(price_per_night / pax, 2) if price_per_night is not None and pax else None
        latitude, longitude = coord_index.get(_slug_from_url(detail_url) or "", (None, None))
        if latitude is None:
            latitude, longitude = _card_lat_lng(card)

        rows.append(
            MarketHotelRow(
                hotelKey=_hotel_key(detail_url or f"{title}-{index}"),
                hotelName=title,
                detailUrl=detail_url,
                roomType=room_type,
                rating=_parse_decimal(rating_text),
                price=price,
                priceText=price_text,
                currency=_parse_currency(price_text),
                pax=pax,
                checkIn=check_in,
                checkOut=check_out,
                nights=nights,
                pricePerNight=price_per_night,
                pricePerPersonPerNight=price_per_person_night,
                position=index,
                latitude=latitude,
                longitude=longitude,
                board=_parse_board(card_text),
                reviewCount=_parse_review_count(rating_text or card_text),
                freeCancellation=_parse_free_cancellation(card_text),
            )
        )
    return rows


_BOARD_PATTERNS = [
    (r"todo incluido|all[\s-]?inclusive", "Todo incluido"),
    (r"pensi[oó]n completa|full board", "Pensión completa"),
    (r"media pensi[oó]n|half board", "Media pensión"),
    (r"desayuno incluido|incluye desayuno|breakfast included", "Desayuno incluido"),
    (r"solo alojamiento|room only|sin comidas", "Solo alojamiento"),
]


def _parse_board(card_text: str | None) -> str | None:
    if not card_text:
        return None
    low = card_text.lower()
    for pattern, label in _BOARD_PATTERNS:
        if re.search(pattern, low):
            return label
    return None


def _parse_review_count(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"([\d.,]+)\s*(?:comentarios|opiniones|valoraciones|reviews|ratings|bewertungen|avis)", text, flags=re.I)
    if not match:
        return None
    digits = re.sub(r"[^\d]", "", match.group(1))
    return int(digits) if digits else None


def _parse_free_cancellation(card_text: str | None) -> bool | None:
    if not card_text:
        return None
    if re.search(r"cancelaci[oó]n gratis|free cancellation|kostenlose stornierung|annulation gratuite", card_text, flags=re.I):
        return True
    return None


_COORD_INDEX_RE = re.compile(
    r'"latitude":\s*(-?\d+\.\d+),\s*"longitude":\s*(-?\d+\.\d+)\},\s*"pageName":\s*"([^"]+)"'
)


def _build_coord_index(html: str) -> dict[str, tuple[float, float]]:
    """Booking embeds each hotel's coordinates in a page-level JSON blob keyed by its
    `pageName` (the detail-URL slug). Mapping these per card removes the need for a
    separate detail-page request per hotel (the dominant scraping cost)."""
    index: dict[str, tuple[float, float]] = {}
    for match in _COORD_INDEX_RE.finditer(html):
        index[match.group(3)] = (float(match.group(1)), float(match.group(2)))
    return index


def _slug_from_url(url: str | None) -> str | None:
    match = re.search(r"/hotel/[a-z]{2}/([^/.?#]+)", url or "")
    return match.group(1) if match else None


def _card_lat_lng(card) -> tuple[float | None, float | None]:
    """Coordinates embedded in the search card itself (Booking exposes them as
    `data-atlas-latlng="lat,lng"`). Avoids a separate detail-page request per hotel."""
    raw = card.get("data-atlas-latlng")
    if not raw:
        node = card.select_one("[data-atlas-latlng]")
        raw = node.get("data-atlas-latlng") if node else None
    if not raw or "," not in raw:
        return None, None
    try:
        lat_str, lng_str = raw.split(",", 1)
        return float(lat_str.strip()), float(lng_str.strip())
    except ValueError:
        return None, None


def parse_booking_location(html: str) -> dict[str, float | str | None]:
    pair = _match_lat_lng(html)
    return {
        "latitude": pair[0] if pair else None,
        "longitude": pair[1] if pair else None,
        "address": _match_address(html),
    }


def _first_text(node, selector: str) -> str | None:
    found = node.select_one(selector)
    return found.get_text(" ", strip=True) if found else None


def _first_attr(node, selector: str, attr: str) -> str | None:
    found = node.select_one(selector)
    return found.get(attr) if found else None


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def _parse_price(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"(\d[\d.,']*)", text)
    if not match:
        return None
    value = match.group(1).replace("'", "")
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".") if value.rfind(",") > value.rfind(".") else value.replace(",", "")
    elif "," in value:
        parts = value.split(",")
        value = f"{''.join(parts[:-1])}.{parts[-1]}" if len(parts[-1]) <= 2 else "".join(parts)
    elif "." in value:
        parts = value.split(".")
        value = f"{''.join(parts[:-1])}.{parts[-1]}" if len(parts[-1]) <= 2 else "".join(parts)
    try:
        return float(value)
    except ValueError:
        return None


def _parse_currency(text: str | None) -> str | None:
    if not text:
        return None
    if "€" in text:
        return "EUR"
    if "$" in text:
        return "USD"
    if "£" in text:
        return "GBP"
    match = re.search(r"\b([A-Z]{3})\b", text)
    return match.group(1) if match else None


def _parse_decimal(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"(\d+[,.]\d+)", text)
    return float(match.group(1).replace(",", ".")) if match else None


def _parse_pax(text: str | None) -> int | None:
    if not text:
        return None
    adults = re.search(r"(\d+)\s+(?:adultos?|adults?)", text, flags=re.I)
    children = re.search(r"(\d+)\s+(?:niñ(?:o|os|a|as)|child(?:ren)?|kids?)", text, flags=re.I)
    total = (int(adults.group(1)) if adults else 0) + (int(children.group(1)) if children else 0)
    if total:
        return total
    guests = re.search(r"(\d+)\s+(?:hu[eé]spedes?|guests?|personas?|people)", text, flags=re.I)
    return int(guests.group(1)) if guests else None


def _normalize_booking_url(input_url: str | None, source_url: str) -> str | None:
    if not input_url:
        return None
    parsed = urljoin(source_url, input_url)
    parts = urlparse(parsed)
    return parts._replace(fragment="").geturl()


def _hotel_key(detail_url: str) -> str:
    try:
        parsed = urlparse(detail_url)
        path = parsed.path.rstrip("/").lower()
        return re.sub(r"[^a-z0-9/.-]", "_", path)
    except Exception:
        return re.sub(r"[^a-z0-9/.-]", "_", detail_url.lower())


def _extract_dates(raw_url: str) -> tuple[str | None, str | None, int | None]:
    parsed = urlparse(raw_url)
    query = parse_qs(parsed.query)
    check_in = _first_query(query, "checkin") or _build_date(query, "checkin")
    check_out = _first_query(query, "checkout") or _build_date(query, "checkout")
    nights = _calculate_nights(check_in, check_out)
    return check_in, check_out, nights


def _first_query(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def _build_date(query: dict[str, list[str]], prefix: str) -> str | None:
    year = _first_query(query, f"{prefix}_year")
    month = _first_query(query, f"{prefix}_month")
    day = _first_query(query, f"{prefix}_monthday")
    if not (year and month and day):
        return None
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def _calculate_nights(check_in: str | None, check_out: str | None) -> int | None:
    if not check_in or not check_out:
        return None
    try:
        start = date.fromisoformat(check_in)
        end = date.fromisoformat(check_out)
        days = (end - start).days
        return days if days > 0 else None
    except ValueError:
        return None


def _match_lat_lng(html: str) -> tuple[float, float] | None:
    patterns = [
        r'data-atlas-latlng="(-?\d+\.\d+),(-?\d+\.\d+)"',
        r'"latitude"\s*:\s*(-?\d+\.\d+)\s*,\s*"longitude"\s*:\s*(-?\d+\.\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I)
        if match:
            return float(match.group(1)), float(match.group(2))

    lat = re.search(r"(?:b_map_center_latitude|latitude)\s*=\s*(-?\d+\.\d+)", html, flags=re.I)
    lng = re.search(r"(?:b_map_center_longitude|longitude)\s*=\s*(-?\d+\.\d+)", html, flags=re.I)
    if lat and lng:
        return float(lat.group(1)), float(lng.group(1))
    return None


def _match_address(html: str) -> str | None:
    match = re.search(r'"formattedAddress"\s*:\s*"([^"]+)"', html, flags=re.I)
    if not match:
        return None
    return match.group(1).encode().decode("unicode_escape").replace("\\/", "/")
