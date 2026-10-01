"""Motor de scraping vía la API GraphQL interna de Booking ("FullSearch").

En vez de simular scroll infinito con un navegador headless (lento, frágil,
depende de clases CSS que Booking cambia constantemente), este módulo ataca
directamente la API GraphQL interna que Booking usa para paginar resultados
(`https://www.booking.com/dml/graphql`). Solo se necesita un navegador
(Playwright) UNA vez, para cargar la página inicial, resolver el reto
anti-bot y obtener cookies de sesión; el resto de páginas se piden como
peticiones HTTP ligeras reutilizando esa misma sesión.

QUÉ HACER SI BOOKING CAMBIA SU API (mantenimiento): ver el docstring de
`booking.py` en la raíz del proyecto (procedimiento de re-captura del
payload GraphQL vía F12 -> Network).
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass
from datetime import date, timedelta

from playwright.async_api import (
    async_playwright,
    BrowserContext,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)

from .browser import new_context
from .config import (
    DELAY_BETWEEN_REQUESTS,
    MAX_CONCURRENT_REQUESTS,
    MAX_RETRIES,
    RESULTS_PER_PAGE,
)
from .helpers import cupos_from_message, to_float, to_int
from .models import Hotel, SearchContext
from .query import ACCOMMODATION_TYPES, GRAPHQL_QUERY
from .url_utils import normalize_search_url, with_dates

log = logging.getLogger("booking")


class PageResponse(tuple):
    """Respuesta de una página que conserva el motivo si se descarta.

    Sigue desempaquetándose como ``(offset, search)`` para no romper los
    consumidores existentes, pero permite al orquestador publicar diagnóstico
    estructurado sin mezclarlo con las filas comerciales.
    """

    def __new__(cls, offset: int, search: dict | None, failure_reason: str | None = None):
        value = super().__new__(cls, (offset, search))
        value.failure_reason = failure_reason
        return value


@dataclass(frozen=True)
class SearchDiagnostics:
    pages_requested: int
    pages_received: int
    failed_pages: tuple[dict[str, object], ...]
    hotels_before_dedupe: int
    hotels_after_dedupe: int
    termination_reason: str
    block_detected: bool


class SearchPagesResult(tuple):
    """(hoteles, total) con diagnóstico opcional y desempaquetado compatible."""

    def __new__(cls, hotels: list[Hotel], total: int, diagnostics: SearchDiagnostics | None = None):
        value = super().__new__(cls, (hotels, total))
        value.diagnostics = diagnostics
        return value


# --------------------------------------------------------------------------
# 1) Cargar la página inicial con un navegador real (resuelve anti-bot)
# --------------------------------------------------------------------------

async def fetch_graphql_input(context: BrowserContext, search_url: str) -> dict:
    """Abre la página de búsqueda con un navegador real y extrae el objeto
    `input` de GraphQL embebido en el HTML (Apollo cache). Esto nos da los
    mismos filtros/destino/fechas que la URL, en formato que la API espera.
    """
    page = await context.new_page()
    try:
        await page.goto(search_url, wait_until="networkidle", timeout=60_000)
        # Espera a que el bloque de resultados exista (señal de que pasó el
        # posible reto anti-bot / captcha de Booking).
        # state="attached": es una etiqueta <script>, nunca será "visible"
        # (que es el estado por defecto que espera Playwright).
        try:
            await page.wait_for_selector(
                "script[data-capla-store-data='apollo']",
                state="attached",
                timeout=30_000,
            )
        except PlaywrightTimeoutError:
            raise RuntimeError(
                "No apareció el bloque de datos de Booking en 30s. Lo más "
                "probable es un reto anti-bot / captcha. Reintenta con el "
                "navegador visible para resolverlo a mano: --no-headless"
            ) from None
        script_content = await page.locator(
            "script[data-capla-store-data='apollo']"
        ).text_content()
    finally:
        await page.close()

    if not script_content:
        raise RuntimeError("El bloque Apollo estaba vacío; la página no cargó bien.")

    apollo_data = json.loads(script_content)
    try:
        search_queries = apollo_data["ROOT_QUERY"]["searchQueries"]
    except (KeyError, TypeError):
        raise RuntimeError(
            "La estructura del Apollo cache cambió (falta ROOT_QUERY/"
            "searchQueries). Re-captura el payload siguiendo el docstring."
        ) from None

    # la primera key suele ser breadcrumbs/autocomplete; la búsqueda completa
    # es la que empieza por "search("
    search_key = next(
        (k for k in search_queries if k.startswith("search(")), None
    )
    if search_key is None:
        raise RuntimeError(
            "No se encontró la clave 'search(...)' en el Apollo cache. "
            "La estructura de Booking cambió; re-captura el payload."
        )
    raw_input = search_key[len("search("):-1]
    return json.loads(raw_input)["input"]


# --------------------------------------------------------------------------
# 2) Pedir cada página de resultados vía GraphQL (rápido, sin navegador)
# --------------------------------------------------------------------------

async def request_page(
    context: BrowserContext,
    search_url: str,
    graphql_input: dict,
    offset: int,
    lang: str,
    semaphore: asyncio.Semaphore,
) -> PageResponse:
    """Pide una página de resultados (offset dado). Devuelve (offset, search)
    donde `search` es el objeto GraphQL, o (offset, None) si la página falla
    tras agotar reintentos. NO lanza: así un fallo puntual de una página no
    tira toda la búsqueda (clave para barridos largos de revenue).
    Reintenta ante errores HTTP, de red y respuestas vacías/con errores.
    """
    body = {
        "operationName": "FullSearch",
        "variables": {
            "input": {
                **graphql_input,
                "pagination": {
                    **(graphql_input.get("pagination") or {}),
                    "offset": offset,
                },
            },
        },
        "extensions": {},
        "query": GRAPHQL_QUERY,
    }

    async with semaphore:
        last_error = "desconocido"
        for attempt in range(1, MAX_RETRIES + 1):
            await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
            try:
                response = await context.request.post(
                    f"https://www.booking.com/dml/graphql?lang={lang}",
                    data=json.dumps(body),
                    headers={
                        "accept": "*/*",
                        "content-type": "application/json",
                        "origin": "https://www.booking.com",
                        "referer": search_url,
                    },
                )
            except PlaywrightError as exc:
                last_error = f"excepción de red: {exc!r}"
                log.warning(
                    "offset=%s -> %s (intento %d/%d)",
                    offset, last_error, attempt, MAX_RETRIES,
                )
                await asyncio.sleep(2 * attempt)
                continue

            if not response.ok:
                last_error = f"HTTP {response.status}"
                log.warning(
                    "offset=%s -> %s (intento %d/%d)",
                    offset, last_error, attempt, MAX_RETRIES,
                )
                await asyncio.sleep(2 * attempt)
                continue

            payload = await response.json()
            data = payload.get("data") or {}
            search_result = (data.get("searchQueries") or {}).get("search")
            if search_result is not None:
                return PageResponse(offset, search_result)

            # HTTP 200 pero sin datos: normalmente trae un array `errors`
            # (ver debug_respuesta.json). Reintentamos por si es transitorio.
            last_error = f"respuesta sin datos; errors={payload.get('errors')}"
            log.warning(
                "offset=%s -> %s (intento %d/%d)",
                offset, last_error, attempt, MAX_RETRIES,
            )
            await asyncio.sleep(2 * attempt)

        # Agotados los reintentos: NO lanzamos, devolvemos None y seguimos.
        log.error(
            "offset=%s DESCARTADO tras %d intentos. Último error: %s",
            offset, MAX_RETRIES, last_error,
        )
        return PageResponse(offset, None, last_error)


# --------------------------------------------------------------------------
# 3) Parsear un resultado crudo -> Hotel
# --------------------------------------------------------------------------

def parse_result(item: dict, ctx: SearchContext, posicion: int | None = None) -> Hotel:
    basic = item.get("basicPropertyData") or {}
    location = item.get("location") or {}
    review = basic.get("reviewScore") or {}
    star = basic.get("starRating") or {}
    price_info = (item.get("priceDisplayInfoIrene") or {}).get("displayPrice") or {}
    amount_per_stay = price_info.get("amountPerStay") or {}
    blocks = item.get("blocks") or []
    first_block = blocks[0] if blocks else {}
    policies = item.get("policies") or {}
    meal = item.get("mealPlanIncluded") or {}
    matching_unit_configs = item.get("matchingUnitConfigurations") or {}
    room_type = None

    # 1. Intentar obtener desde commonConfiguration
    common_config = matching_unit_configs.get("commonConfiguration") or {}
    if common_config:
        names = common_config.get("unitTypeNames") or []
        if names and names[0].get("translation"):
            room_type = names[0].get("translation")
        if not room_type:
            room_type = common_config.get("name")

    # 2. Si no hay configuración común, solo usar una configuración de unidad
    # cuando sea unívoca. Elegir la primera de varias habitaciones mezcla la
    # identidad de la habitación con el precio destacado.
    if not room_type:
        unit_configs = matching_unit_configs.get("unitConfigurations") or []
        candidates: list[str] = []
        for config in unit_configs:
            names = config.get("unitTypeNames") or []
            value = names[0].get("translation") if names else None
            value = value or config.get("name")
            if value and value not in candidates:
                candidates.append(str(value))
        if len(candidates) == 1:
            room_type = candidates[0]

    display_price = to_float(amount_per_stay.get("amount"))
    display_currency = amount_per_stay.get("currency")
    block_final = first_block.get("finalPrice") or {}
    block_price = to_float(block_final.get("amount"))
    block_currency = block_final.get("currency")

    # The highlighted search price and the first block are not guaranteed to
    # describe the same product. Keep the highlighted value for the market
    # card, but only attach a reference/original price when the source block
    # agrees with it. This prevents a discount from being calculated across
    # two different room, board or eligibility combinations.
    price = display_price if display_price is not None else block_price
    currency = display_currency or block_currency
    same_displayed_block = (
        display_price is None
        or block_price is None
        or abs(display_price - block_price) <= 0.01
    ) and (
        not display_currency
        or not block_currency
        or display_currency == block_currency
    )

    precio_noche = None
    if price is not None and ctx.noches:
        precio_noche = round(price / ctx.noches, 2)

    # El precio de referencia solo es atribuible si el bloque coincide con el
    # precio que se muestra en la tarjeta. Si no, se conserva como desconocido
    # en lugar de llamarlo rack/BAR o fabricar un descuento.
    orig_price = (
        to_float((first_block.get("originalPrice") or {}).get("amount"))
        if same_displayed_block else None
    )
    descuento_pct = None
    if orig_price and price is not None and orig_price > price:
        descuento_pct = round((orig_price - price) / orig_price * 100, 1)

    # La ausencia de precio no demuestra agotamiento: también puede ser una
    # respuesta parcial, un cambio de esquema o un precio que no se pudo
    # interpretar. Solo afirmar sold-out cuando la fuente lo marque
    # explícitamente; en cualquier otro caso queda desconocido.
    cerrado = basic.get("isClosed")
    disponible = price is not None
    sold_out_raw = item.get("isSoldOut")
    if sold_out_raw is None:
        sold_out_raw = basic.get("isSoldOut")
    sold_out = bool(sold_out_raw) if sold_out_raw is not None else None
    raw_price_values = [amount_per_stay.get("amount"), block_final.get("amount")]
    if price is not None:
        observation_status = "available"
    elif sold_out is True:
        observation_status = "unavailable_for_query"
    elif cerrado is True:
        observation_status = "closed"
    elif any(value not in (None, "") for value in raw_price_values):
        observation_status = "parse_error"
    else:
        observation_status = "unknown"

    cancelacion_hasta = first_block.get("freeCancellationUntil")
    cupos_restantes = cupos_from_message(first_block)
    ocupacion_tarifa = to_int((first_block.get("blockId") or {}).get("occupancy"))
    tpi = (first_block.get("thirdPartyInventoryContext") or {}).get("isTpiBlock")
    tarifa_terceros = bool(tpi) if tpi is not None else None

    ubicacion_top = location.get("isWithinBestLocationScoreArea")
    distrito_popular = location.get("popularFreeDistrictName")
    ninos_gratis_raw = (first_block.get("blockMatchTags") or {}).get("childStaysForFree")
    tiene_cuna_raw = first_block.get("hasCrib")

    accommodation_type_id = to_int(basic.get("accommodationTypeId"))
    accommodation_type = (
        ACCOMMODATION_TYPES.get(accommodation_type_id)
        if accommodation_type_id is not None
        else None
    )
    if accommodation_type_id is not None and accommodation_type is None:
        accommodation_type = f"Otro (ht_id={accommodation_type_id})"

    basic_location = basic.get("location") or {}
    country_code = basic_location.get("countryCode")
    latitud = to_float(basic_location.get("latitude"))
    longitud = to_float(basic_location.get("longitude"))
    page_name = basic.get("pageName")
    hotel_url = (
        f"https://www.booking.com/hotel/{country_code}/{page_name}.html"
        if country_code and page_name
        else None
    )

    photo = ((basic.get("photos") or {}).get("main") or {}).get("highResUrl", {}).get("relativeUrl")
    description = (item.get("description") or {}).get("text")
    if not description:
        description = (basic.get("description") or {}).get("text")
    score_tag = review.get("totalScoreTextTag") or {}
    score_text = score_tag.get("translation") if isinstance(score_tag, dict) else score_tag
    nearby_beaches_raw = location.get("nearbyBeachNames") or []
    nearby_beaches: list[str] = []
    for beach in nearby_beaches_raw:
        if isinstance(beach, str):
            nearby_beaches.append(beach)
        elif isinstance(beach, dict):
            value = beach.get("translation") or beach.get("name") or beach.get("text")
            if value:
                nearby_beaches.append(str(value))

    return Hotel(
        id=str(basic.get("id")) if basic.get("id") is not None else None,
        nombre=(item.get("displayName") or {}).get("text"),
        posicion=posicion,
        precio=price,
        precio_noche=precio_noche,
        precio_original=orig_price,
        descuento_pct=descuento_pct,
        moneda=currency,
        disponible=disponible,
        sold_out=sold_out,
        observation_status=observation_status,
        cerrado=bool(cerrado) if cerrado is not None else None,
        cupos_restantes=cupos_restantes,
        ocupacion_tarifa=ocupacion_tarifa,
        tarifa_terceros=tarifa_terceros,
        tipo_alojamiento=accommodation_type,
        tipo_habitacion=room_type,
        puntuacion=to_float(review.get("score")),
        num_resenas=to_int(review.get("reviewCount")),
        estrellas=to_float(star.get("value")),
        regimen=meal.get("text"),
        cancelacion_gratis=policies.get("showFreeCancellation"),
        cancelacion_hasta=cancelacion_hasta,
        direccion=basic_location.get("address"),
        ubicacion=location.get("displayLocation"),
        descripcion=description,
        ciudad=basic_location.get("city"),
        pais_code=country_code,
        distancia_principal=location.get("mainDistance"),
        playas_cercanas=nearby_beaches,
        puntuacion_texto=score_text,
        sin_prepago=(policies.get("showNoPrepayment")),
        ufi=str(basic.get("ufi")) if basic.get("ufi") is not None else None,
        latitud=latitud,
        longitud=longitud,
        distancia_playa=location.get("beachDistance"),
        ubicacion_top=bool(ubicacion_top) if ubicacion_top is not None else None,
        distrito_popular=distrito_popular,
        ninos_gratis=bool(ninos_gratis_raw) if ninos_gratis_raw is not None else None,
        tiene_cuna=bool(tiene_cuna_raw) if tiene_cuna_raw is not None else None,
        url=hotel_url,
        foto=f"https://cf.bstatic.com{photo}" if photo else None,
        checkin=ctx.checkin,
        checkout=ctx.checkout,
        noches=ctx.noches,
        adultos=ctx.adultos,
        ninos=ctx.ninos,
        habitaciones=ctx.habitaciones,
        fecha_scrape=ctx.fecha_scrape,
        destino=ctx.destino,
        dest_id=ctx.dest_id,
        dest_type=ctx.dest_type,
        divisa_solicitada=ctx.divisa_solicitada,
        filtro_regimen=ctx.filtro_regimen,
    )


# --------------------------------------------------------------------------
# 4) Orquestación completa
# --------------------------------------------------------------------------

async def _scrape_single_search(
    context: BrowserContext,
    search_url: str,
    max_pages: int | None,
    *,
    return_total: bool = False,
) -> list[Hotel] | tuple[list[Hotel], int]:
    """Ejecuta UNA búsqueda completa (todas sus páginas) reutilizando un
    `context` de navegador ya abierto. No lanza ni cierra el navegador, así
    que se puede llamar varias veces seguidas (p.ej. una vez por semana en
    el barrido semanal) sin pagar el coste de relanzar Chromium cada vez.
    """
    clean_url, params = normalize_search_url(search_url)
    lang = params.get("lang", "es")
    ctx = SearchContext.from_params(params)

    log.info(
        "Cargando página inicial (checkin=%s, checkout=%s)...",
        ctx.checkin, ctx.checkout,
    )
    graphql_input = await fetch_graphql_input(context, clean_url)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    log.info("Pidiendo primera página de resultados (offset=0)...")
    first_response = await request_page(
        context, clean_url, graphql_input, 0, lang, semaphore
    )
    _, first_page = first_response
    if first_page is None:
        raise RuntimeError(
            "La primera página (offset=0) falló tras los reintentos. "
            f"Motivo: {first_response.failure_reason or 'desconocido'}. "
            "Probable bloqueo anti-bot; reintenta con --no-headless."
        )

    # Guardamos los resultados por offset para poder ordenarlos por ranking
    # aunque las páginas lleguen desordenadas (as_completed).
    pages_by_offset: dict[int, list[dict]] = {0: list(first_page.get("results") or [])}

    pagination = first_page.get("pagination") or {}
    total_results = to_int(pagination.get("nbResultsTotal"))
    if not total_results:
        log.warning("No se pudo leer nbResultsTotal; uso solo la primera página.")
        total_results = len(pages_by_offset[0])
    log.info("Total de propiedades encontradas: %s", total_results)

    remaining_offsets = list(range(RESULTS_PER_PAGE, total_results, RESULTS_PER_PAGE))
    if max_pages is not None:
        # max_pages incluye la primera página ya pedida
        remaining_offsets = remaining_offsets[: max(0, max_pages - 1)]
    log.info("Pidiendo %d páginas adicionales...", len(remaining_offsets))

    tasks = [
        request_page(context, clean_url, graphql_input, offset, lang, semaphore)
        for offset in remaining_offsets
    ]
    failed_pages: list[dict[str, object]] = []
    for i, coro in enumerate(asyncio.as_completed(tasks), start=1):
        page_response = await coro
        offset, page_result = page_response
        if page_result is None:
            failed_pages.append({
                "offset": offset,
                "reason": (page_response.failure_reason or "desconocido")[:240],
            })
            continue
        pages_by_offset[offset] = list(page_result.get("results") or [])
        log.info("  ...página %d/%d recibida (offset=%d)", i, len(remaining_offsets), offset)

    if failed_pages:
        log.warning(
            "%d de %d páginas se descartaron; el resultado es PARCIAL.",
            len(failed_pages), len(remaining_offsets) + 1,
        )

    # Aplanar en orden de ranking: offset ascendente + orden dentro de la página.
    # posicion = offset + índice dentro de la página + 1 (1 = primero de todo).
    hotels: list[Hotel] = []
    for offset in sorted(pages_by_offset):
        for idx, item in enumerate(pages_by_offset[offset]):
            hotels.append(parse_result(item, ctx, posicion=offset + idx + 1))

    # quitar duplicados por id (Booking a veces repite resultados patrocinados)
    # OJO: el dedupe es solo dentro de ESTA búsqueda; en el barrido semanal
    # cada semana se dedupea por separado para no perder filas de semanas
    # distintas que comparten hotel.
    seen: set[str] = set()
    unique_hotels: list[Hotel] = []
    for h in hotels:
        key = h.id or h.nombre
        if key is None:
            # sin identificador fiable: lo conservamos para no perder datos
            unique_hotels.append(h)
            continue
        if key not in seen:
            seen.add(key)
            unique_hotels.append(h)
    expected_page_count = max(1, (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
    page_cap_applied = max_pages is not None and len(remaining_offsets) + 1 < expected_page_count
    if failed_pages:
        termination_reason = "partial_page_failures"
    elif page_cap_applied:
        termination_reason = "page_cap"
    else:
        termination_reason = "provider_exhausted"
    diagnostics = SearchDiagnostics(
        pages_requested=len(remaining_offsets) + 1,
        pages_received=len(pages_by_offset),
        failed_pages=tuple(failed_pages),
        hotels_before_dedupe=len(hotels),
        hotels_after_dedupe=len(unique_hotels),
        termination_reason=termination_reason,
        block_detected=any(
            any(token in str(item.get("reason", "")).lower() for token in ("403", "429", "captcha", "anti-bot", "bloqueo"))
            for item in failed_pages
        ),
    )
    if return_total:
        return SearchPagesResult(unique_hotels, total_results, diagnostics)
    return unique_hotels


async def scrape_all_pages(
    search_url: str,
    headless: bool = True,
    max_pages: int | None = None,
) -> list[Hotel]:
    """Búsqueda única: lanza el navegador, scrapea todas las páginas de
    `search_url` y lo cierra."""
    _, params = normalize_search_url(search_url)
    lang = params.get("lang", "es")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await new_context(browser, lang)
        try:
            return await _scrape_single_search(context, search_url, max_pages)
        finally:
            await context.close()
            await browser.close()


async def scrape_all_pages_with_meta(
    search_url: str,
    headless: bool = True,
    max_pages: int | None = None,
) -> tuple[list[Hotel], int]:
    """Variant used by the web capture: keeps the real Booking total even
    when the UI asks for a smaller sample or a page cap is configured."""
    _, params = normalize_search_url(search_url)
    lang = params.get("lang", "es")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await new_context(browser, lang)
        try:
            result = await _scrape_single_search(
                context, search_url, max_pages, return_total=True
            )
            return result
        finally:
            await context.close()
            await browser.close()


async def scrape_weekly(
    base_url: str,
    start_date: date,
    nights: int = 7,
    weeks: int = 1,
    headless: bool = True,
    max_pages: int | None = None,
) -> list[Hotel]:
    """Repite la búsqueda de `base_url` una vez por semana durante `weeks`
    semanas, empezando en `start_date` y desplazando el checkin 7 días en
    cada iteración. Cada búsqueda dura `nights` noches (por defecto 7).

    El resto de filtros de `base_url` (destino, adultos, régimen, estrellas,
    etc.) se mantiene igual en todas las semanas; solo cambian checkin y
    checkout. Reutiliza un único navegador para las `weeks` búsquedas.

    Útil para ver cómo varía el precio de una MISMA estancia según en qué
    semana del año se reserva.
    """
    clean_base, base_params = normalize_search_url(base_url)
    lang = base_params.get("lang", "es")

    all_hotels: list[Hotel] = []
    semanas_ok = 0
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await new_context(browser, lang)
        try:
            for week in range(weeks):
                checkin = start_date + timedelta(days=7 * week)
                checkout = checkin + timedelta(days=nights)
                week_url = with_dates(clean_base, checkin, checkout)

                log.info(
                    "=== Semana %d/%d: %s -> %s (%d noches) ===",
                    week + 1, weeks, checkin.isoformat(), checkout.isoformat(), nights,
                )
                # Resiliencia: una semana que falle (bloqueo puntual, timeout)
                # NO debe tirar el barrido entero. Se registra y se continúa.
                try:
                    hotels = await _scrape_single_search(context, week_url, max_pages)
                    log.info("  %d hoteles encontrados esta semana.", len(hotels))
                    all_hotels.extend(hotels)
                    semanas_ok += 1
                except (RuntimeError, PlaywrightError) as exc:
                    log.error(
                        "  Semana %d (%s) DESCARTADA: %s",
                        week + 1, checkin.isoformat(), exc,
                    )

                if week < weeks - 1:
                    # pausa entre semanas: mismo espíritu que DELAY_BETWEEN_REQUESTS
                    # pero a nivel de búsqueda completa, no de página individual.
                    await asyncio.sleep(random.uniform(3.0, 6.0))
        finally:
            await context.close()
            await browser.close()

    log.info("Barrido completado: %d/%d semanas con datos.", semanas_ok, weeks)
    return all_hotels
