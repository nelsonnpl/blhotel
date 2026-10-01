"""Adaptador entre el motor de scraping GraphQL (`backend/app/booking_graphql/`)
y el modelo de datos de la web (`MarketHotelRow`).

Backend de extracción por defecto (ver `SCRAPER_BACKEND` en config.py):
ataca la API GraphQL interna de Booking en vez de pedir HTML vía proxy
(Decodo, ver `backend/app/decodo.py` + `booking_parser.py`, mantenidos
aparte como alternativa). Ventajas frente a Decodo:

  - Las coordenadas vienen en la propia respuesta GraphQL -> no hace falta
    una petición extra por hotel para geolocalizar (`_enrich_locations` en
    services.py no aplica a este backend).
  - Señal adicional: precio rack + % de descuento, sold-out/cerrado, cupos
    restantes, tipo de alojamiento, distancia a playa, Genius...
"""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlparse

from datetime import datetime, timezone

from .booking_graphql import Hotel, TarifaDetalle, scrape_all_pages_with_meta, scrape_detail_for_hotels
from .models import HotelRateDetailRow, MarketHotelRow

RESULTS_PER_PAGE = 25
MAX_PAGES_HARD_CAP = 20
MAX_DETAIL_HOTELS_PER_REQUEST = 15

_HOTEL_URL_RE = re.compile(r"/hotel/([a-z]{2})/([^/.?#]+)", re.IGNORECASE)


class ScrapeSearchResult(tuple):
    """Resultado de búsqueda desempaquetable como las tres tuplas históricas.

    `diagnostics` viaja como atributo para que el servicio pueda persistir la
    cobertura sin romper adaptadores o tests que siguen devolviendo una tupla
    normal de `(rows, raw_hash, available_results)`.
    """

    def __new__(cls, rows: list[MarketHotelRow], raw_hash: str, available_results: int, diagnostics: dict | None = None):
        value = super().__new__(cls, (rows, raw_hash, available_results))
        value.diagnostics = diagnostics
        return value


def hotel_key_from_url(detail_url: str | None, fallback: str) -> str:
    """Misma convención de clave que el parser de Decodo (slug de la URL de
    ficha: /hotel/<país>/<pagename>), para que el histórico de precios de
    un hotel sea el mismo independientemente del backend de scraping usado.
    """
    target = detail_url or fallback
    parsed = urlparse(target)
    path = parsed.path.rstrip("/").lower()
    key = re.sub(r"[^a-z0-9/.-]", "_", path)
    return key or re.sub(r"[^a-z0-9/.-]", "_", target.lower())


def _hotel_to_row(hotel: Hotel, source_url: str, position: int) -> MarketHotelRow:
    detail_url = hotel.url or source_url

    pax = None
    if hotel.adultos is not None or hotel.ninos is not None:
        pax = (hotel.adultos or 0) + (hotel.ninos or 0) or None

    price_per_person_night = (
        round(hotel.precio_noche / pax, 2)
        if hotel.precio_noche is not None and pax
        else None
    )
    price_text = (
        f"{hotel.precio:,.2f} {hotel.moneda}"
        if hotel.precio is not None and hotel.moneda
        else None
    )
    ready = hotel.latitud is not None and hotel.longitud is not None

    return MarketHotelRow(
        hotelKey=hotel_key_from_url(detail_url, source_url),
        hotelName=hotel.nombre or "Hotel sin nombre",
        detailUrl=detail_url,
        roomType=hotel.tipo_habitacion,
        rating=hotel.puntuacion,
        price=hotel.precio,
        priceText=price_text,
        currency=hotel.moneda,
        pax=pax,
        checkIn=hotel.checkin,
        checkOut=hotel.checkout,
        nights=hotel.noches,
        pricePerNight=hotel.precio_noche,
        pricePerPersonPerNight=price_per_person_night,
        position=position,
        locationStatus="ready" if ready else "location_pending",
        latitude=hotel.latitud,
        longitude=hotel.longitud,
        address=hotel.direccion,
        board=hotel.regimen,
        reviewCount=hotel.num_resenas,
        freeCancellation=hotel.cancelacion_gratis,
        hotelId=hotel.id,
        priceOriginal=hotel.precio_original,
        discountPct=hotel.descuento_pct,
        soldOut=hotel.sold_out,
        observationStatus=hotel.observation_status,
        closed=hotel.cerrado,
        unitsLeft=hotel.cupos_restantes,
        accommodationType=hotel.tipo_alojamiento,
        beachDistance=hotel.distancia_playa,
        topLocation=hotel.ubicacion_top,
        popularDistrict=hotel.distrito_popular,
        childrenFree=hotel.ninos_gratis,
        thirdParty=hotel.tarifa_terceros,
        occupancyRate=hotel.ocupacion_tarifa,
        description=hotel.descripcion,
        stars=hotel.estrellas,
        city=hotel.ciudad,
        countryCode=hotel.pais_code,
        ufi=hotel.ufi,
        displayLocation=hotel.ubicacion,
        mainDistance=hotel.distancia_principal,
        nearbyBeachNames=hotel.playas_cercanas or [],
        photoUrl=hotel.foto,
        reviewScoreText=hotel.puntuacion_texto,
        noPrepayment=hotel.sin_prepago,
    )


async def scrape_search_graphql(
    source_url: str, limit: int, *, headless: bool = True
) -> tuple[list[MarketHotelRow], str, int]:
    """Ejecuta una búsqueda completa vía GraphQL y devuelve
    (filas recortadas a `limit`, hash de auditoría de los datos crudos,
    total de propiedades disponibles antes de recortar). No necesita
    enriquecimiento de ubicación aparte: las coordenadas vienen ya
    incluidas en la respuesta GraphQL.
    """
    max_pages = max(1, min(MAX_PAGES_HARD_CAP, -(-limit // RESULTS_PER_PAGE)))
    page_result = await scrape_all_pages_with_meta(
        source_url, headless=headless, max_pages=max_pages
    )
    hotels, available_results = page_result

    hash_accumulator = hashlib.sha256()
    for hotel in hotels:
        hash_accumulator.update(json.dumps(hotel.as_row(), sort_keys=True, default=str).encode())

    rows = [
        _hotel_to_row(hotel, source_url, position=idx + 1)
        for idx, hotel in enumerate(hotels[:limit])
    ]
    diagnostics = getattr(page_result, "diagnostics", None)
    diagnostics_dict = None
    if diagnostics is not None:
        diagnostics_dict = {
            "pagesRequested": diagnostics.pages_requested,
            "pagesReceived": diagnostics.pages_received,
            "pagesFailed": len(diagnostics.failed_pages),
            "failedPages": [dict(item) for item in diagnostics.failed_pages],
            "hotelsBeforeDedupe": diagnostics.hotels_before_dedupe,
            "hotelsAfterDedupe": diagnostics.hotels_after_dedupe,
            "terminationReason": diagnostics.termination_reason,
            "blockDetected": diagnostics.block_detected,
        }
    return ScrapeSearchResult(rows, hash_accumulator.hexdigest(), available_results, diagnostics_dict)


def parse_hotel_url(detail_url: str | None) -> tuple[str, str] | None:
    """Extrae (country_code, pagename) de una URL de ficha de Booking
    (https://www.booking.com/hotel/<cc>/<pagename>.html...), tal como los
    necesita el modo detalle (`--hoteles` en booking.py). None si la URL no
    tiene ese formato."""
    if not detail_url:
        return None
    match = _HOTEL_URL_RE.search(detail_url)
    if not match:
        return None
    return match.group(1).lower(), match.group(2)


def _tarifa_to_row(
    tarifa: TarifaDetalle,
    target_id: int,
    hotel_key: str,
    hotel_name: str | None,
    captured_at: str,
    snapshot_id: int | None = None,
) -> HotelRateDetailRow:
    return HotelRateDetailRow(
        snapshotId=snapshot_id,
        targetId=target_id,
        hotelKey=hotel_key,
        hotelName=tarifa.hotel_nombre or hotel_name,
        hotelPagename=tarifa.hotel_pagename,
        roomType=tarifa.tipo_habitacion,
        maxOccupancy=tarifa.ocupacion_max,
        priceOriginal=tarifa.precio_original,
        priceFinal=tarifa.precio_final,
        currency=tarifa.moneda,
        board=tarifa.regimen,
        prepaymentText=tarifa.prepago_texto,
        program=tarifa.programa,
        cancellationText=tarifa.cancelacion_texto,
        freeCancellation=tarifa.cancelacion_gratis,
        unitsLeft=tarifa.cupos_restantes,
        blockUid=tarifa.blockuid,
        soldOut=tarifa.sold_out_ficha,
        genius=tarifa.genius,
        breakfastScore=tarifa.breakfast_score,
        breakfastTypeId=tarifa.breakfast_type_id,
        bedComfortScore=tarifa.bed_comfort_score,
        bedComfortReviews=tarifa.bed_comfort_resenas,
        stars=tarifa.estrellas,
        checkIn=tarifa.checkin,
        checkOut=tarifa.checkout,
        adults=tarifa.adultos,
        children=tarifa.ninos,
        rooms=tarifa.habitaciones,
        capturedAt=captured_at,
    )


async def scrape_rate_details(
    target_id: int,
    hotels: list[dict],
    checkin: str,
    checkout: str,
    adults: int = 2,
    children: int = 0,
    rooms: int = 1,
    headless: bool = True,
    snapshot_id: int | None = None,
) -> list[HotelRateDetailRow]:
    """Modo detalle: abre la FICHA de cada hotel de `hotels`
    ([{"hotelKey": ..., "detailUrl": ..., "hotelName": ...}, ...]) y extrae
    TODAS sus tarifas (habitación x régimen x cupos). A diferencia de la
    búsqueda GraphQL, esto es HTML server-side (más lento y frágil) -> se usa
    para un comp-set pequeño elegido a mano por el usuario, no para el
    mercado completo. Tope duro de MAX_DETAIL_HOTELS_PER_REQUEST por
    petición para no disparar el tiempo de captura.
    """
    hotels = hotels[:MAX_DETAIL_HOTELS_PER_REQUEST]

    pagename_to_hotel: dict[str, dict] = {}
    pairs: list[tuple[str, str]] = []
    for item in hotels:
        parsed = parse_hotel_url(item.get("detailUrl"))
        if parsed is None:
            continue
        _, pagename = parsed
        pagename_to_hotel[pagename] = item
        pairs.append(parsed)

    if not pairs:
        return []

    tarifas = await scrape_detail_for_hotels(
        pairs, checkin=checkin, checkout=checkout,
        adults=adults, children=children, rooms=rooms, headless=headless,
    )

    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rows: list[HotelRateDetailRow] = []
    for tarifa in tarifas:
        source = pagename_to_hotel.get(tarifa.hotel_pagename or "")
        hotel_key = (source or {}).get("hotelKey") or tarifa.hotel_pagename or ""
        hotel_name = (source or {}).get("hotelName")
        rows.append(_tarifa_to_row(tarifa, target_id, hotel_key, hotel_name, captured_at, snapshot_id))
    return rows
