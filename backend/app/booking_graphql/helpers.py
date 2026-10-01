"""Helpers de conversión: Booking a veces devuelve números como strings, y
las tablas de precio del modo --detalle vienen renderizadas como texto en
español."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any


def currency_from_price_text(*values: str | None) -> str | None:
    """Returns only currencies explicitly visible in the observed text."""
    text = " ".join(str(value or "") for value in values).upper()
    if "EUR" in text or "€" in text:
        return "EUR"
    if "USD" in text or "$" in text:
        return "USD"
    if "GBP" in text or "£" in text:
        return "GBP"
    return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    f = to_float(value)
    return int(f) if f is not None else None


def cupos_from_message(block: dict) -> int | None:
    """Extrae el nº de 'Nos quedan N a este precio' (onlyXLeftMessage).
    Señal de escasez/urgencia que Booking muestra cuando queda poco stock."""
    msg = (block.get("onlyXLeftMessage") or {}).get("translation")
    if not msg:
        return None
    m = re.search(r"\d+", msg)
    return int(m.group()) if m else None


def num_noches(checkin: str | None, checkout: str | None) -> int | None:
    if not checkin or not checkout:
        return None
    try:
        d1 = date.fromisoformat(checkin)
        d2 = date.fromisoformat(checkout)
    except ValueError:
        return None
    noches = (d2 - d1).days
    return noches if noches > 0 else None


def parse_date_safe(value: str | None) -> date | None:
    """checkin/checkout se guardan como 'YYYY-MM-DD'. Los convierte a
    `date` real para que Excel los reconozca como fecha (no texto)."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_datetime_safe(value: str | None) -> datetime | None:
    """fecha_scrape se guarda como 'YYYY-MM-DD HH:MM:SS'. Los convierte a
    `datetime` real para que Excel lo reconozca como fecha/hora."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def parse_price_es(text: str | None) -> float | None:
    """Parsea precios tal como los renderiza Booking en español, p.ej.
    '€ 2.562' (2562, sin decimales, '.' = separador de miles) o
    '€ 365,98' (365.98, ',' = separador decimal, sin miles en este caso).
    Acepta también el formato internacional (`EUR 123.45`). Cuando no hay
    coma, un único punto seguido de una o dos cifras se interpreta como
    decimal; una agrupación de tres cifras sigue siendo separador de miles.
    Si el formato es ambiguo, conserva el valor más conservador y no inventa
    decimales.
    """
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return None
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        dot_parts = cleaned.split(".")
        if len(dot_parts) == 2 and len(dot_parts[1]) in (1, 2):
            cleaned = ".".join(dot_parts)
        else:
            cleaned = cleaned.replace(".", "")
    try:
        return float(cleaned)
    except ValueError:
        return None
