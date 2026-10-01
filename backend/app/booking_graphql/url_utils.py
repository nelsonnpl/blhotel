"""Preparar la URL de búsqueda: normalización (clavar divisa) y sustitución
de fechas para el barrido semanal."""

from __future__ import annotations

from datetime import date
from urllib.parse import urlparse, parse_qs, urlencode

from .config import MONEDA


def normalize_search_url(source_url: str) -> tuple[str, dict[str, str]]:
    """Toma la URL de búsqueda tal cual la pega el usuario (copiada del
    navegador) y devuelve (url_limpia, params) listos para reutilizar en
    las peticiones GraphQL.
    """
    parsed = urlparse(source_url)
    if parsed.scheme not in ("http", "https") or "booking.com" not in parsed.netloc:
        raise ValueError(
            f"La URL no parece de Booking.com: {source_url!r}\n"
            "Pega una URL de búsqueda copiada del navegador "
            "(https://www.booking.com/searchresults...)."
        )
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    # Clavar la divisa: imprescindible para que las series sean comparables.
    params["selected_currency"] = MONEDA
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params)}"
    return clean_url, params


def with_dates(clean_url: str, checkin: date, checkout: date) -> str:
    """Devuelve `clean_url` (ya normalizada por normalize_search_url) con
    los parámetros checkin/checkout sustituidos. El resto de filtros
    (destino, adultos, mealplan, estrellas...) se mantienen tal cual.
    Se usa para generar una variante de la búsqueda por cada semana en el
    barrido semanal (--semanas).
    """
    parsed = urlparse(clean_url)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    params["checkin"] = checkin.isoformat()
    params["checkout"] = checkout.isoformat()
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params)}"
