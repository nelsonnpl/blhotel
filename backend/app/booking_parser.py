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

        price = _parse_price(price_text)
        price_per_night = round(price / nights, 2) if price is not None and nights else None
        pax = _parse_pax(pax_text)
        price_per_person_night = round(price_per_night / pax, 2) if price_per_night is not None and pax else None

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
            )
        )
    return rows


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
    adults = re.search(r"(\d+)\s+adultos?", text, flags=re.I)
    children = re.search(r"(\d+)\s+niñ(?:o|os|a|as)", text, flags=re.I)
    total = (int(adults.group(1)) if adults else 0) + (int(children.group(1)) if children else 0)
    return total or None


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
