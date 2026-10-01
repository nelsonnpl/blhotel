"""Motor de scraping de Booking.com vía su API GraphQL interna.

Sustituye la extracción por proxy (Decodo, ver `backend/app/decodo.py`) como
vía principal: ataca directamente `/dml/graphql` (operación "FullSearch")
en vez de pedir HTML renderizado, lo que da un schema más estable y mucha
más señal (precio rack, descuento, sold-out, cupos restantes, tipo de
alojamiento, distancia a playa...). Solo se abre un navegador (Playwright)
una vez, para resolver el anti-bot y obtener cookies de sesión.

Usado tanto por el CLI (`booking.py`, raíz del proyecto) como por el backend
web (`backend/app/graphql_scraper.py`). Decodo se mantiene en el repo sin
usarse por defecto (ver `backend/app/config.py`, SCRAPER_BACKEND).
"""

from .client import (
    fetch_graphql_input,
    parse_result,
    request_page,
    scrape_all_pages,
    scrape_all_pages_with_meta,
    scrape_weekly,
)
from .detail import scrape_detail_for_hotels, scrape_hotel_detail
from .models import Hotel, SearchContext, TarifaDetalle
from .url_utils import normalize_search_url, with_dates

__all__ = [
    "Hotel",
    "SearchContext",
    "TarifaDetalle",
    "fetch_graphql_input",
    "parse_result",
    "request_page",
    "scrape_all_pages",
    "scrape_all_pages_with_meta",
    "scrape_weekly",
    "scrape_detail_for_hotels",
    "scrape_hotel_detail",
    "normalize_search_url",
    "with_dates",
]
