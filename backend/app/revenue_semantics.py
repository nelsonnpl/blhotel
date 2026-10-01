"""Read-only rules for observed rates; no PMS metrics are inferred here."""
from datetime import date, datetime, timezone
import math


def product_signature(row):
    """Return an observed product identity, or None when it cannot be verified.

    Taxes, customer eligibility and payment deadlines are not captured uniformly.
    Matching these fields is therefore observed equivalence, not full rate parity.
    """
    get = row.get if isinstance(row, dict) else lambda key: getattr(row, key, None)
    norm = lambda value: str(value).strip().casefold() if value is not None else ""
    signature = (
        norm(get("hotelKey")), norm(get("checkIn")), norm(get("checkOut")),
        get("nights"), get("pax"), norm(get("roomType")), norm(get("board")),
        norm(get("currency")), get("freeCancellation"),
    )
    if any(value is None or value == "" for value in signature):
        return None
    try:
        nights = (date.fromisoformat(signature[2]) - date.fromisoformat(signature[1])).days
        if nights <= 0 or nights != signature[3] or signature[4] <= 0:
            return None
        price = get("pricePerNight")
        if price is None:
            price = get("price") / nights
        if not math.isfinite(price) or price <= 0:
            return None
    except (TypeError, ValueError):
        return None
    return signature


def unique_products(rows):
    """Exclude ambiguous duplicate products rather than choosing an arbitrary row."""
    result, duplicates = {}, set()
    for row in rows:
        signature = product_signature(row)
        if signature is None:
            continue
        if signature in result:
            duplicates.add(signature)
        result[signature] = row
    return {key: row for key, row in result.items() if key not in duplicates}


def freshness(raw, now=None):
    if not raw:
        return {"estado": "sin_fecha", "etiqueta": "Sin fecha verificable", "scrapedAt": None}
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age = ((now or datetime.now(timezone.utc)) - parsed).total_seconds() / 3600
        if age < 0:
            raise ValueError("Future observation")
    except (TypeError, ValueError):
        return {"estado": "revisar", "etiqueta": "Fecha no verificable", "scrapedAt": str(raw)}
    state, label = ("caducado", "Caducado") if age > 72 else (("revisar", "Revisar vigencia") if age > 24 else ("actualizado", "Actualizado"))
    return {"estado": state, "etiqueta": label, "scrapedAt": str(raw), "edadHoras": round(age, 2)}
