"""Grid COMPLETO de tarifas de un hotel (modo --detalle).

A diferencia del resto del motor, esto NO es GraphQL: el grid de
habitaciones (#hprt-table) se renderiza server-side en HTML. Es la parte
frágil del tool -> si Booking cambia estas clases, hay que re-mapear
selectores abriendo una ficha real y repitiendo la captura (ver README de
mantenimiento en el docstring de `booking.py`, raíz del proyecto). Las
señales de hotel (Genius, desayuno, confort de cama, sold-out) sí son
GraphQL, en el Apollo cache bajo la clave `roomTable(...)`.

Selectores verificados en vivo (11-jul-2026) contra una ficha real:
  tr.js-rt-block-row              -> una fila = una tarifa
  .hprt-table-cell-roomtype       -> nombre habitación (con rowspan: no
                                     todas las filas lo repiten, hereda
                                     de la fila anterior con nombre)
  .hprt-table-cell-occupancy      -> "Máximo de personas: N"
  .bui-price-display__original    -> precio tachado (rack)
  .bui-price-display__value       -> precio final
  .e2e-cancellation               -> texto completo de cancelación (hook
                                     de test de Booking, más estable que
                                     una clase CSS normal)
  .bui-list__description          -> [régimen, "Nos quedan N"] (orden variable)
  [class*="blockuid-"]            -> id único de esa tarifa concreta
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timezone

from playwright.async_api import (
    BrowserContext,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)

from .config import DELAY_BETWEEN_REQUESTS, MAX_RETRIES, MONEDA
from .helpers import currency_from_price_text, to_float, to_int, parse_price_es
from .models import TarifaDetalle


def _free_cancellation_from_text(text: str | None) -> bool | None:
    """Clasifica solo afirmaciones explícitas de cancelación gratuita."""
    if not text:
        return None
    value = " ".join(text.casefold().split())
    negative = (
        "no es gratis", "no gratuita", "no gratuito", "no reembolsable",
        "non-refundable", "non refundable", "no admite cancelación",
        "no admite cancelacion",
    )
    if any(marker in value for marker in negative):
        return False
    positive = (
        "cancelación gratuita", "cancelacion gratuita", "cancelación gratis",
        "cancelacion gratis", "free cancellation", "gratuitamente cancelable",
    )
    if any(marker in value for marker in positive):
        return True
    return None

log = logging.getLogger("booking")

# Selectores centralizados en un solo sitio (SEL) para que, cuando Booking
# cambie el HTML, solo haya que tocar este objeto. Además devolvemos un bloque
# `diag` con cuántas veces casó cada selector clave: si la tabla existe pero
# `diag` sale a 0, sabemos que se rompió un selector (no que el hotel esté
# sold-out) y `_warn_selector_health()` lo grita en el log -> detección
# temprana en vez de datasets vacíos en silencio.
_HPRT_EXTRACT_JS = r"""
() => {
  const SEL = {
    table: '#hprt-table',
    row: 'tr.js-rt-block-row',
    roomType: '.hprt-table-cell-roomtype',
    roomName: '.hprt-roomtype-icon-link',
    priceCell: '.hprt-table-cell-price',
    priceOriginal: '.bui-price-display__original',
    priceValue: '.bui-price-display__value',
    occupancy: '.hprt-table-cell-occupancy',
    conditions: '.hprt-table-cell-conditions',
    cancellation: '.e2e-cancellation',
    description: '.bui-list__description',
  };
  const table = document.querySelector(SEL.table);
  const rows = document.querySelectorAll(SEL.table + ' ' + SEL.row);
  const out = [];
  let lastRoomName = null;
  let lastOccupancy = null;
  let nameHits = 0, priceHits = 0;
  rows.forEach((row) => {
    const roomTypeCell = row.querySelector(SEL.roomType);
    const nameEl = roomTypeCell ? roomTypeCell.querySelector(SEL.roomName) : null;
    if (nameEl) {
      lastRoomName = nameEl.textContent.trim();
      lastOccupancy = null;
      nameHits++;
    }

    const priceCell = row.querySelector(SEL.priceCell);
    const origEl = priceCell ? priceCell.querySelector(SEL.priceOriginal) : null;
    const valEl = priceCell ? priceCell.querySelector(SEL.priceValue) : null;
    if (valEl) priceHits++;

    const occEl = row.querySelector(SEL.occupancy);
    const occMatch = occEl ? occEl.textContent.match(/(\d+)/) : null;
    if (occMatch) { lastOccupancy = occMatch[1]; }

    const cond = row.querySelector(SEL.conditions);
    const cancelEl = cond ? cond.querySelector(SEL.cancellation) : null;
    const descs = cond ? Array.from(cond.querySelectorAll(SEL.description)).map(d => d.textContent.trim()) : [];
    const cuposDesc = descs.find(d => /qued(?:a|an)\s+\d+/i.test(d));
    const cuposMatch = cuposDesc ? cuposDesc.match(/(\d+)/) : null;
    const regimen = descs.find(d => /desayuno|media pensi[oó]n|todo incluido|solo alojamiento|solo habitaci[oó]n|room only|half board|full board|all inclusive/i.test(d)) || null;
    const prepayment = descs.find(d => /pago por adelantado|prepago|prepayment|pay now|pay at/i.test(d)) || null;
    const rowText = row.textContent.replace(/\s+/g, ' ').trim();
    const programMatch = rowText.match(/\b(genius(?:\s+(?:discount|descuento))?|oferta\s+m[oó]vil|mobile\s+rate)\b/i);

    const blockuidEl = row.querySelector('[class*="blockuid-"]');
    const blockuidCls = blockuidEl ? [...blockuidEl.classList].find(c => c.startsWith('blockuid-')) : null;

    out.push({
      nombre: lastRoomName,
      ocupacion_max: lastOccupancy,
      precio_original: origEl ? origEl.textContent.trim() : null,
      precio_final: valEl ? valEl.textContent.trim() : null,
      regimen,
      prepago_texto: prepayment,
      programa: programMatch ? programMatch[0] : null,
      cancelacion_texto: cancelEl ? cancelEl.textContent.trim().replace(/\s+/g, ' ') : null,
      cupos_restantes: cuposMatch ? cuposMatch[1] : null,
      blockuid: blockuidCls,
    });
  });
  return {
    rows: out,
    diag: {
      tableFound: !!table,
      rowCount: rows.length,
      nameHits: nameHits,
      priceHits: priceHits,
    },
  };
}
"""


def _extract_hotel_flags(context_data: dict) -> dict:
    """Lee del Apollo cache de la ficha (clave `roomTable(...)`) las señales
    de hotel que sí vienen limpias por GraphQL: id, nombre, sold-out, Genius,
    desayuno, confort de cama, estrellas. Devuelve dict vacío si no se
    encuentran (no rompe el resto del parseo).

    `hotelId`/`propertyName` viven en este MISMO nodo (verificado en vivo,
    12-jul-2026) -> más fiables que el selector DOM `[data-hotelid]`, que en
    fichas reales no siempre casa (JSON estructurado de la API interna, no
    HTML que Booking pueda reestilar sin avisar).

    OJO: `breakfastScore` es una REFERENCIA Apollo a otro nodo (no un
    número plano) y `bedComfortReviewScore` viene como objeto inline
    {score, reviewsCount} -> ambos hay que desanidarlos, no leerlos directo
    (verificado en vivo: un primer intento los leyó mal, ver histórico).
    """
    try:
        root_query = context_data["ROOT_QUERY"]
        key = next(k for k in root_query if k.startswith("roomTable("))
        ref = root_query[key]["__ref"]
        node = context_data[ref]
    except (KeyError, StopIteration, TypeError):
        return {}

    breakfast_score = None
    bs = node.get("breakfastScore")
    if isinstance(bs, dict):
        bs_node = context_data.get(bs["__ref"], {}) if "__ref" in bs else bs
        breakfast_score = to_float(bs_node.get("score"))

    bed_comfort = node.get("bedComfortReviewScore")
    bed_comfort_score = None
    bed_comfort_resenas = None
    if isinstance(bed_comfort, dict):
        bc_node = context_data.get(bed_comfort["__ref"], {}) if "__ref" in bed_comfort else bed_comfort
        bed_comfort_score = to_float(bc_node.get("score"))
        bed_comfort_resenas = to_int(bc_node.get("reviewsCount"))

    hotel_id = node.get("hotelId")
    return {
        "hotel_id": str(hotel_id) if hotel_id is not None else None,
        "hotel_nombre": node.get("propertyName"),
        "sold_out_ficha": node.get("isSoldOut"),
        "genius": bool(node.get("genius")) if node.get("genius") is not None else None,
        "breakfast_score": breakfast_score,
        "breakfast_type_id": to_int(node.get("breakfastType")),
        "bed_comfort_score": bed_comfort_score,
        "bed_comfort_resenas": bed_comfort_resenas,
        "estrellas": to_float(node.get("stars")),
    }


def _warn_selector_health(
    country_code: str, pagename: str, diag: dict, sold_out: bool | None
) -> None:
    """Grita en el log si la tabla de tarifas existe pero los selectores no
    casaron nada -> señal de que Booking cambió el HTML (no de que el hotel
    esté sold-out). Distingue el sold-out legítimo (0 filas + isSoldOut) de la
    rotura silenciosa (0 filas SIN sold-out), para no llenar el dataset de
    filas vacías sin que nadie se entere. `sold_out` es None si no se pudo
    leer el flag del Apollo cache; solo avisamos cuando es explícitamente
    False (sabemos que hay disponibilidad pero no la vemos)."""
    if not diag:
        return
    tag = f"[{country_code}/{pagename}]"
    if not diag.get("tableFound"):
        if sold_out is False:
            log.warning(
                "%s sin #hprt-table y la ficha NO está sold-out: posible "
                "cambio de layout de Booking -> revisa el selector 'table' en "
                "_HPRT_EXTRACT_JS.", tag,
            )
        return
    if diag.get("rowCount", 0) == 0:
        if sold_out is not True:
            log.warning(
                "%s #hprt-table presente pero 0 filas (tr.js-rt-block-row) y la "
                "ficha no está marcada sold-out: probable cambio de layout -> "
                "revisa el selector 'row' en _HPRT_EXTRACT_JS.", tag,
            )
        return
    n = diag["rowCount"]
    if diag.get("priceHits", 0) == 0:
        log.warning(
            "%s %d filas pero 0 precios (.bui-price-display__value): el selector "
            "de precio pudo cambiar -> revisa 'priceValue' en _HPRT_EXTRACT_JS.",
            tag, n,
        )
    if diag.get("nameHits", 0) == 0:
        log.warning(
            "%s %d filas pero 0 nombres de habitación (.hprt-roomtype-icon-link): "
            "el selector de nombre pudo cambiar -> revisa 'roomName' en "
            "_HPRT_EXTRACT_JS.", tag, n,
        )


async def scrape_hotel_detail(
    context: BrowserContext,
    country_code: str,
    pagename: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    children: int = 0,
    rooms: int = 1,
    lang: str = "es",
) -> list[TarifaDetalle]:
    """Abre la FICHA de un hotel concreto y extrae TODAS sus tarifas
    (habitación x régimen x condiciones), no solo la tarifa "cabecera" que
    da la búsqueda. Reutiliza el `context` (misma sesión/cookies) para no
    pagar el coste de un nuevo reto anti-bot por hotel.

    Resiliencia:
      - La navegación se reintenta hasta MAX_RETRIES con backoff (un timeout
        puntual ya no descarta el hotel al primer intento, igual que en el
        modo búsqueda GraphQL).
      - Tras extraer, `_warn_selector_health()` distingue sold-out legítimo de
        selectores rotos y lo avisa en el log (fail-loud, no en silencio).
      - El hecho de que no aparezca #hprt-table NO se reintenta: suele ser un
        sold-out real y reintentarlo solo dobla el tiempo en tiradas grandes.
    """
    hotel_url = (
        f"https://www.booking.com/hotel/{country_code}/{pagename}.{lang}.html"
        f"?checkin={checkin}&checkout={checkout}"
        f"&group_adults={adults}&group_children={children}&no_rooms={rooms}"
        f"&selected_currency={MONEDA}&lang={lang}"
    )
    fecha_scrape = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    raw_rows: list[dict] = []
    diag: dict = {}
    flags: dict = {}
    last_error: str | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        page = await context.new_page()
        try:
            try:
                await page.goto(
                    hotel_url, wait_until="domcontentloaded", timeout=45_000
                )
            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                # Fallo de navegación (timeout / reset de red): transitorio,
                # reintentamos. El finally cierra la página.
                last_error = f"navegación falló: {exc}"
                log.warning(
                    "  [%s/%s] %s (intento %d/%d)",
                    country_code, pagename, last_error, attempt, MAX_RETRIES,
                )
                await asyncio.sleep(2 * attempt)
                continue

            try:
                await page.wait_for_selector("#hprt-table", timeout=20_000)
            except PlaywrightTimeoutError:
                log.warning(
                    "  [%s/%s] sin tabla de tarifas (probable sold-out o layout distinto)",
                    country_code, pagename,
                )
                # aun así, intentar leer isSoldOut/flags del hotel antes de desistir
                raw_rows = []
                diag = {"tableFound": False, "rowCount": 0, "nameHits": 0, "priceHits": 0}
            else:
                result = await page.evaluate(_HPRT_EXTRACT_JS)
                raw_rows = result.get("rows") or []
                diag = result.get("diag") or {}

            # señales de hotel desde el Apollo cache (best-effort). Incluye
            # hotel_id y hotel_nombre (nodo roomTable -> hotelId/propertyName),
            # más fiables que el selector DOM [data-hotelid] que usábamos
            # antes (no siempre casaba en fichas reales).
            try:
                script = await page.locator(
                    "script[data-capla-store-data='apollo']"
                ).text_content(timeout=5_000)
                if script:
                    flags = _extract_hotel_flags(json.loads(script))
            except (PlaywrightTimeoutError, json.JSONDecodeError):
                pass

            # Booking renders hotel-level loyalty participation in the visible
            # copy. Keep only the hotel flag; it is not a benefit of every
            # individual rate and must not be copied into `programa`.
            try:
                body_text = await page.locator("body").inner_text(timeout=5_000)
                normalized_body = " ".join(body_text.split()).casefold()
                if "programa de fidelización genius" in normalized_body or "programa de fidelizacion genius" in normalized_body:
                    flags["genius"] = True
                elif "oferta móvil" in normalized_body or "oferta movil" in normalized_body or "mobile rate" in normalized_body:
                    pass
            except PlaywrightTimeoutError:
                pass

            break  # navegación OK (aunque sea sold-out): no reintentar
        finally:
            if not page.is_closed():
                await page.close()
    else:
        # agotados los reintentos de navegación: devolvemos lista vacía (el
        # caller la trata como hotel descartado y sigue con el resto).
        log.error(
            "  [%s/%s] DESCARTADO tras %d intentos de navegación. Último error: %s",
            country_code, pagename, MAX_RETRIES, last_error,
        )
        return []

    # fail-loud: ¿0 filas por sold-out real o porque un selector se rompió?
    _warn_selector_health(country_code, pagename, diag, flags.get("sold_out_ficha"))
    tarifas: list[TarifaDetalle] = []
    for row in raw_rows:
        cancel_texto = row.get("cancelacion_texto")
        tarifas.append(TarifaDetalle(
            hotel_pagename=pagename,
            tipo_habitacion=row.get("nombre"),
            ocupacion_max=to_int(row.get("ocupacion_max")),
            precio_original=parse_price_es(row.get("precio_original")),
            precio_final=parse_price_es(row.get("precio_final")),
            moneda=currency_from_price_text(row.get("precio_final"), row.get("precio_original")),
            regimen=row.get("regimen"),
            prepago_texto=row.get("prepago_texto"),
            programa=row.get("programa"),
            cancelacion_texto=cancel_texto,
            cancelacion_gratis=_free_cancellation_from_text(cancel_texto),
            cupos_restantes=to_int(row.get("cupos_restantes")),
            blockuid=row.get("blockuid"),
            checkin=checkin,
            checkout=checkout,
            adultos=adults,
            ninos=children,
            habitaciones=rooms,
            fecha_scrape=fecha_scrape,
            **flags,
        ))

    if not tarifas:
        # ficha sin filas de tarifa (sold-out / layout distinto): igual
        # guardamos una fila "vacía" con los flags de hotel, para no perder
        # la observación de sold-out en el histórico.
        tarifas.append(TarifaDetalle(
            hotel_pagename=pagename,
            checkin=checkin, checkout=checkout,
            adultos=adults, ninos=children, habitaciones=rooms,
            fecha_scrape=fecha_scrape,
            **flags,
        ))

    return tarifas


async def scrape_detail_for_hotels(
    hoteles: list[tuple[str, str]],
    checkin: str,
    checkout: str,
    adults: int = 2,
    children: int = 0,
    rooms: int = 1,
    lang: str = "es",
    headless: bool = True,
) -> list[TarifaDetalle]:
    """Orquesta scrape_hotel_detail para una lista de hoteles
    [(country_code, pagename), ...] reutilizando un único navegador.
    Resiliente: un hotel que falle se descarta y se continúa con el resto.
    """
    from playwright.async_api import async_playwright

    from .browser import new_context

    all_tarifas: list[TarifaDetalle] = []
    ok = 0
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await new_context(browser, lang)
        try:
            for i, (country_code, pagename) in enumerate(hoteles, start=1):
                log.info("=== Detalle %d/%d: %s/%s ===", i, len(hoteles), country_code, pagename)
                try:
                    tarifas = await scrape_hotel_detail(
                        context, country_code, pagename, checkin, checkout,
                        adults=adults, children=children, rooms=rooms, lang=lang,
                    )
                    if tarifas:
                        log.info("  %d tarifas encontradas.", len(tarifas))
                        all_tarifas.extend(tarifas)
                        ok += 1
                    else:
                        # navegación agotó reintentos (ya logueó el error dentro):
                        # no hay datos, no cuenta como hotel con datos.
                        log.warning("  %s/%s sin datos.", country_code, pagename)
                except (RuntimeError, PlaywrightError) as exc:
                    log.error("  %s/%s DESCARTADO: %s", country_code, pagename, exc)

                if i < len(hoteles):
                    await asyncio.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
        finally:
            await context.close()
            await browser.close()

    log.info("Detalle completado: %d/%d hoteles con datos.", ok, len(hoteles))
    return all_tarifas
