"""
booking_scraper.py
===================

Scraper de resultados de búsqueda de Booking.com (open source).

FILOSOFÍA / POR QUÉ ES MANTENIBLE
----------------------------------
En vez de simular scroll infinito con un navegador headless (lento, frágil,
depende de clases CSS que Booking cambia constantemente), este script ataca
directamente la API GraphQL interna que Booking usa para paginar resultados
(`https://www.booking.com/dml/graphql`, operación "FullSearch").

Ventajas de este enfoque:
  1. Los campos del GraphQL (`displayName`, `reviewScore`, `finalPrice`...)
     son estables en el tiempo -> Booking cambia el HTML/CSS a menudo, pero
     rara vez cambia el schema de su propia API interna.
  2. Paginar por `offset` es mucho más rápido y fiable que hacer scroll con
     un navegador para cada página de resultados.
  3. Solo necesitamos un navegador (Playwright) UNA vez, para cargar la
     página inicial, resolver el reto anti-bot y obtener cookies de sesión.
     El resto de páginas se piden como peticiones HTTP ligeras reutilizando
     esa misma sesión -> mucho más rápido y menos "ruidoso" para el sitio.

El motor de scraping (dataclasses, query GraphQL, parseo, orquestación) vive
en `backend/app/booking_graphql/` -> lo comparten este CLI y el backend web
(`backend/app/graphql_scraper.py`), para no duplicar lógica. Este archivo es
solo la capa de línea de comandos: argumentos, guardado a SQLite/CSV/XLSX y
el runner de jobs YAML.

QUÉ HACER SI BOOKING CAMBIA SU API (mantenimiento)
----------------------------------------------------
Búsqueda / barrido semanal (GraphQL, el modo normal):
  1. Abre la búsqueda en el navegador -> F12 -> pestaña Network -> filtra
     por "Fetch/XHR".
  2. Haz scroll o cambia de página y localiza la petición POST a
     `booking.com/dml/graphql`.
  3. Copia el "Request Payload" completo (el `query` de GraphQL) y
     sustituye la constante GRAPHQL_QUERY en
     `backend/app/booking_graphql/query.py`.
  4. Revisa si la estructura del JSON de respuesta sigue teniendo las
     mismas claves; ajusta `parse_result()` (en
     `backend/app/booking_graphql/client.py`) si no.

Modo --detalle (grid de tarifas de la ficha de hotel, `#hprt-table`):
  A diferencia de lo anterior, ESTO NO ES GraphQL: es HTML server-side con
  clases CSS que Booking puede cambiar. Si `--detalle` deja de encontrar
  filas, abre una ficha real con fechas (F12 -> Elements), localiza
  `#hprt-table` y reconstruye los selectores en `_HPRT_EXTRACT_JS`
  (`backend/app/booking_graphql/detail.py`). Las señales de hotel (Genius,
  desayuno, confort de cama, sold-out) sí son GraphQL, en el Apollo cache
  bajo la clave `roomTable(...)` -> ajusta `_extract_hotel_flags()` si
  cambian.

Ese es el mantenimiento real: paginación, guardado, reintentos, dataset
maestro y jobs no dependen de la estructura de Booking y no deberían tocarse.

USO
---
    pip install -r requirements.txt
    playwright install chromium

    # búsqueda única (usa la URL pegada tal cual del navegador):
    python booking.py "https://www.booking.com/searchresults.es.html?...."

    # o define la constante URL más abajo y ejecuta sin argumentos:
    python booking.py

    # SALIDA POR DEFECTO en cada ejecución: dataset maestro SQLite
    # (output/booking_master.db, acumulativo e idempotente -> pensado para
    # series históricas de revenue) + un .xlsx de esa ejecución. Para
    # cambiar el fichero por run usa --formato (repetible: json/csv/xlsx),
    # o quítalo del todo con --sin-excel:
    python booking.py "<url>" --formato csv --no-headless --max-paginas 5
    python booking.py "<url>" --sin-excel

    # publicar también la captura en la base que consume la consola web:
    python booking.py "<url>" --sync-web

    # barrido semanal: analiza 7 noches empezando el 2026-11-02, repitiendo
    # la misma búsqueda 8 semanas seguidas (checkin +7 días cada vez):
    python booking.py "<url>" --semanas 8 --fecha-inicio 2026-11-02

    # igual, pero con estancias de 3 noches en vez de 7:
    python booking.py "<url>" --semanas 8 --fecha-inicio 2026-11-02 --noches 3

    # modo detalle: TODAS las tarifas (habitación x régimen x cupos) de un
    # comp-set concreto, no solo la tarifa "cabecera" de cada hotel. Más
    # lento y más frágil (HTML, no GraphQL) -> para comp-sets pequeños:
    python booking.py "<url_con_checkin_checkout_ocupacion>" \
        --detalle --hoteles "es/ifa-altamarena,es/hotel-competidor"

    # jobs: varios comp-sets/barridos/detalles en una sola ejecución
    # (pensado para cron nocturno). Ver load_jobs() para el formato YAML:
    python booking.py --jobs jobs.yaml

El script acepta CUALQUIER URL de búsqueda de Booking.com copiada del
navegador (con destino, fechas, filtros, adultos, etc. ya aplicados).
Para scrapear otro destino/fechas, simplemente pega otra URL: no hace falta
tocar el código.

Además de los precios, cada fila guarda el CONTEXTO de la búsqueda (fechas de
entrada/salida, ocupación, fecha del scrape en UTC, precio/noche) y la
IDENTIDAD del comp-set (destino, dest_id, divisa solicitada, filtro), además
de señales de revenue: precio rack y % de descuento, disponibilidad/sold-out,
posición en el ranking y cancelación. Todo se acumula en el dataset maestro
para hacer SEGUIMIENTO en el tiempo sin perder de qué búsqueda venían.

La consola web mantiene aparte `hotel_inventory` con identidad, estrellas,
descripción, ciudad, foto, ubicación y distancia a playa. Cada captura mezcla
ese inventario con la tarifa observada y sólo rellena atributos estables que
estén vacíos.

La divisa se CLAVA (constante MONEDA en `backend/app/booking_graphql/config.py`,
por defecto EUR): Booking la elegiría por geo/IP si no, y las series no
serían comparables entre ejecuciones.

AVISO
-----
Este script es para uso personal / investigación de precios propios.
Respeta el robots.txt y añade límites de velocidad razonables (ya incluidos
por defecto) para no sobrecargar el sitio ni saltar sus protecciones de
forma agresiva.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import random
import sqlite3
import sys
from dataclasses import dataclass, fields
from datetime import date, datetime
from pathlib import Path
from typing import Any

from playwright.async_api import Error as PlaywrightError
import yaml

# Motor de scraping compartido con el backend web (ver
# backend/app/booking_graphql/). Este archivo es solo la capa CLI.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.app.booking_graphql import (  # noqa: E402
    Hotel,
    SearchContext,
    TarifaDetalle,
    normalize_search_url,
    scrape_all_pages,
    scrape_detail_for_hotels,
    scrape_weekly,
)
from backend.app.booking_graphql.helpers import (  # noqa: E402
    parse_date_safe as _parse_date_safe,
    parse_datetime_safe as _parse_datetime_safe,
)

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent

# URL de búsqueda por defecto. Puedes dejarla vacía ("") y pasarla siempre por
# línea de comandos. Si defines ambas, el argumento de línea de comandos MANDA.
URL = "https://www.booking.com/searchresults.es.html?label=gen173nr-10CAEoggI46AdIM1gEaEaIAQGYATO4AQfIAQ3YAQPoAQH4AQGIAgGoAgG4Avz2ytIGwAIB0gIkMThkOTg1MDctYTJkZS00ZTUzLTgxN2EtODA0ODI5MTRhOWI12AIB4AIB&aid=304142&ss=Gran+Canaria%2C+España&ssne=Fuerteventura&ssne_untouched=Fuerteventura&lang=es&src=searchresults&dest_id=754&dest_type=region&ac_position=1&ac_click_type=b&ac_langcode=es&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=64f2a144bc89065b&checkin=2026-11-16&checkout=2026-11-23&group_adults=2&no_rooms=1&group_children=0&nflt=mealplan%3D4"

# --- Barrido semanal (opcional) ---
# Si SEMANAS tiene un valor (> 0), ejecutar sin argumentos activa el barrido
# semanal en vez de una búsqueda única: repite la búsqueda de arriba una vez
# por semana, empezando en FECHA_INICIO y desplazando el checkin 7 días en
# cada iteración (cada búsqueda dura NOCHES noches).
# Los argumentos --semanas/--fecha-inicio/--noches de la línea de comandos
# SIEMPRE tienen prioridad sobre estas constantes (igual que con URL).
FECHA_INICIO = "2027-01-11"   # checkin de la primera semana, formato "YYYY-MM-DD"
NOCHES = 7           # noches de estancia por semana analizada
SEMANAS = 2       # nº de semanas a analizar; None o 0 = búsqueda única
                      # (usa el checkin/checkout que ya trae la URL de arriba)

OUTPUT_DIR = Path("output")
# Dataset maestro consolidado (SQLite). Cada ejecución hace UPSERT: acumula
# histórico sin duplicar, para construir series de precio en el tiempo.
DB_PATH = OUTPUT_DIR / "booking_master.db"
FORMATOS_VALIDOS = ("json", "csv", "xlsx")

log = logging.getLogger("booking")


# --------------------------------------------------------------------------
# 6) Guardado
# --------------------------------------------------------------------------

# Clave de idempotencia del dataset maestro: identifica una OBSERVACIÓN única
# = un hotel, para unas fechas/ocupación, capturado en un instante concreto.
# Re-ejecutar el mismo scrape reemplaza (no duplica); scrapes en momentos
# distintos acumulan -> serie temporal de precios.
_DB_PK = ("id", "checkin", "checkout", "adultos", "ninos", "habitaciones", "fecha_scrape")

# Mapa de tipo Python (del dataclass) a tipo de columna SQLite.
_SQLITE_TYPES = {int: "INTEGER", float: "REAL", bool: "INTEGER", str: "TEXT"}

# Clave de idempotencia de tarifas_detalle: una tarifa concreta (blockuid)
# de un hotel, para unas fechas/ocupación, en un instante de scrape.
_DETALLE_PK = (
    "hotel_pagename", "checkin", "checkout",
    "adultos", "ninos", "habitaciones", "blockuid", "fecha_scrape",
)


def _sqlite_columns(dataclass_type: type) -> list[tuple[str, str]]:
    """Deriva (nombre, tipo_sqlite) de los campos de un dataclass, para que
    el esquema de la tabla no se desincronice del modelo de datos."""
    cols = []
    for f in fields(dataclass_type):
        base = f.type
        # anotaciones tipo "float | None" -> nos quedamos con el primer tipo real
        sqlite_type = "TEXT"
        for py_type, sql in _SQLITE_TYPES.items():
            if py_type.__name__ in str(base):
                sqlite_type = sql
                break
        cols.append((f.name, sqlite_type))
    return cols


def _save_dataclass_rows(
    objs: list,
    dataclass_type: type,
    table: str,
    pk: tuple[str, ...],
    db_path: Path,
) -> int:
    """Vuelca instancias de un dataclass a una tabla SQLite con UPSERT
    idempotente (INSERT OR REPLACE por `pk`) y auto-migración de columnas
    nuevas (ALTER ADD COLUMN). Compartido por el dataset de hoteles (Fase 1)
    y el de tarifas_detalle (Fase 2B)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cols = _sqlite_columns(dataclass_type)
    col_names = [c[0] for c in cols]

    col_defs = ", ".join(f'"{name}" {typ}' for name, typ in cols)
    pk_def = ", ".join(f'"{c}"' for c in pk)
    placeholders = ", ".join("?" for _ in col_names)
    col_list = ", ".join(f'"{c}"' for c in col_names)

    bool_fields = {f.name for f in fields(dataclass_type) if "bool" in str(f.type)}

    rows = []
    for obj in objs:
        d = obj.as_row()
        rows.append([
            int(d[c]) if (c in bool_fields and d[c] is not None) else d[c]
            for c in col_names
        ])

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs}, PRIMARY KEY ({pk_def}))'
        )
        # Auto-migración: si la tabla ya existía de una versión anterior del
        # dataclass, añadimos las columnas nuevas. Así el dataset sobrevive
        # a que ampliemos el modelo de datos (nos pasó factura en Fase 2A).
        existentes = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
        for name, typ in cols:
            if name not in existentes:
                conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {typ}')
                log.info("Migración DB: %s.%s nueva columna (%s)", table, name, typ)
        if "id" in col_names:
            conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table}_id" ON "{table}" ("id")')
        if "checkin" in col_names:
            conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table}_checkin" ON "{table}" ("checkin")')
        conn.executemany(
            f'INSERT OR REPLACE INTO "{table}" ({col_list}) VALUES ({placeholders})',
            rows,
        )
        conn.commit()
    finally:
        conn.close()

    log.info("%s: %d filas -> %s", table, len(rows), db_path)
    return len(rows)


def save_to_db(hotels: list[Hotel], db_path: Path = DB_PATH) -> int:
    """Vuelca los hoteles al dataset maestro SQLite (tabla 'hoteles') con
    UPSERT idempotente. Devuelve el nº de filas escritas."""
    return _save_dataclass_rows(hotels, Hotel, "hoteles", _DB_PK, db_path)


def sync_to_web_db(
    hotels: list[Hotel],
    source_url: str,
    web_db_path: Path,
    target_name: str = "Booking CLI",
) -> int:
    """Publica una captura del CLI en la misma base que consume la web.

    El dataset maestro de exportación se conserva separado para análisis
    offline. Esta sincronización opt-in reutiliza el adaptador GraphQL y el
    inventario estable del backend, de modo que el CLI y la consola web no
    creen dos definiciones distintas de un hotel.
    """
    from backend.app.database import Database
    from backend.app.graphql_scraper import _hotel_to_row

    db = Database(web_db_path)
    target = db.upsert_target(target_name, source_url)
    rows = [_hotel_to_row(hotel, source_url, position=index + 1) for index, hotel in enumerate(hotels)]
    for row in rows:
        if row.latitude is not None and row.longitude is not None:
            db.upsert_location(row.hotelKey, row.detailUrl, row.latitude, row.longitude, row.address)
        db.upsert_hotel_inventory(row)
    snapshot = db.create_snapshot(
        target_id=target.id,
        source_url=source_url,
        requested_limit=len(rows),
        available_results=len(hotels),
        captured_rows=len(rows),
        raw_hash="booking-cli",
    )
    for row in rows:
        location = db.get_location(row.hotelKey)
        status = "ready" if location and location["latitude"] is not None and location["longitude"] is not None else "location_pending"
        db.insert_market_hotel(snapshot.id, row, status)
    log.info("Web sincronizada: %d hoteles -> %s (snapshot %s)", len(rows), web_db_path, snapshot.id)
    return snapshot.id


def save_detalle_to_db(tarifas: list[TarifaDetalle], db_path: Path = DB_PATH) -> int:
    """Vuelca el grid de tarifas detalladas (--detalle) a la tabla
    'tarifas_detalle' del mismo dataset maestro, con UPSERT idempotente."""
    return _save_dataclass_rows(tarifas, TarifaDetalle, "tarifas_detalle", _DETALLE_PK, db_path)


def save_results(
    items: list[Hotel] | list[TarifaDetalle],
    output_dir: Path = OUTPUT_DIR,
    formatos: tuple[str, ...] = FORMATOS_VALIDOS,
    prefix: str = "booking_resultados",
) -> None:
    """Exporta a fichero(s) por ejecución (json/csv/xlsx). Acepta tanto
    `list[Hotel]` (búsqueda/barrido) como `list[TarifaDetalle]` (--detalle);
    ambos dataclasses exponen `.as_row()`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [item.as_row() for item in items]

    # Timestamp en el nombre para NO sobrescribir scrapes anteriores
    # (esencial para el seguimiento de precios en el tiempo).
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{prefix}_{stamp}"

    log.info("Guardado: %d filas", len(rows))
    if not rows:
        log.warning("No hay resultados que guardar.")
        return

    if "json" in formatos:
        json_path = output_dir / f"{base}.json"
        json_path.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        log.info("  -> %s", json_path)

    if "csv" in formatos:
        csv_path = output_dir / f"{base}.csv"
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log.info("  -> %s", csv_path)

    if "xlsx" in formatos:
        xlsx_path = output_dir / f"{base}.xlsx"
        _save_xlsx(rows, xlsx_path)
        log.info("  -> %s", xlsx_path)


# Símbolo a mostrar junto al importe en las columnas de precio. Si aparece
# una moneda no listada aquí, se usa el propio código (p.ej. "USD") tal cual.
CURRENCY_SYMBOLS: dict[str, str] = {
    "EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF", "JPY": "¥",
}

# Qué campo de Hotel/SearchContext recibe qué formato en el Excel. El
# JSON/CSV se quedan con los valores crudos (str/float/bool) tal cual salen
# de parse_result -> son para procesar por máquina. El formato de celda solo
# se aplica aquí, en la vista pensada para abrir a mano en Excel.
_XLSX_CURRENCY_FIELDS = {"precio", "precio_noche", "precio_original", "precio_final"}
_XLSX_DATE_FIELDS = {"checkin", "checkout", "cancelacion_hasta"}
_XLSX_DATETIME_FIELDS = {"fecha_scrape"}
_XLSX_DECIMAL_FIELDS = {
    "puntuacion", "estrellas", "descuento_pct", "breakfast_score", "bed_comfort_score",
}
_XLSX_INT_FIELDS = {
    "num_resenas", "noches", "adultos", "ninos", "habitaciones", "posicion",
    "cupos_restantes", "ocupacion_tarifa", "ocupacion_max", "breakfast_type_id",
    "bed_comfort_resenas",
}
_XLSX_BOOL_FIELDS = {
    "cancelacion_gratis", "disponible", "sold_out", "cerrado", "tarifa_terceros",
    "sold_out_ficha", "genius", "ubicacion_top", "ninos_gratis", "tiene_cuna",
}
_XLSX_TEXT_FIELDS = {"id", "dest_id", "hotel_id", "blockuid"}  # forzar texto: evita que Excel los reinterprete


def _save_xlsx(rows: list[dict[str, Any]], path: Path) -> None:
    """Guarda a Excel con encabezado en negrita, filtros y formato de celda
    por tipo de dato (moneda, fecha, entero, Sí/No...). openpyxl es
    opcional: si no está instalado, avisamos en vez de romper."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        log.warning(
            "openpyxl no está instalado; omito el .xlsx. "
            "Instálalo con: pip install openpyxl"
        )
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Booking"

    headers = list(rows[0].keys())
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row_idx, row in enumerate(rows, start=2):
        moneda = row.get("moneda") or ""
        symbol = CURRENCY_SYMBOLS.get(moneda, moneda)
        currency_format = f'#,##0.00" {symbol}"' if symbol else "#,##0.00"

        for col_idx, header in enumerate(headers, start=1):
            value = row.get(header)
            cell = ws.cell(row=row_idx, column=col_idx)

            if header in _XLSX_DATE_FIELDS:
                cell.value = _parse_date_safe(value) or value
                cell.number_format = "dd/mm/yyyy"
            elif header in _XLSX_DATETIME_FIELDS:
                cell.value = _parse_datetime_safe(value) or value
                cell.number_format = "dd/mm/yyyy hh:mm"
            elif header in _XLSX_CURRENCY_FIELDS:
                cell.value = value
                cell.number_format = currency_format
            elif header in _XLSX_DECIMAL_FIELDS:
                cell.value = value
                cell.number_format = "0.0"
            elif header in _XLSX_INT_FIELDS:
                cell.value = value
                cell.number_format = "#,##0"
            elif header in _XLSX_BOOL_FIELDS:
                cell.value = "Sí" if value else ("No" if value is not None else None)
            elif header in _XLSX_TEXT_FIELDS:
                cell.value = value
                cell.number_format = "@"
            elif header == "url" and value:
                cell.value = value
                cell.hyperlink = value
                cell.style = "Hyperlink"
            else:
                cell.value = value

    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "A2"  # la cabecera queda fija al hacer scroll
    for idx, header in enumerate(headers, start=1):
        max_len = max(
            [len(str(header))] + [len(str(r.get(header) or "")) for r in rows]
        )
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(
            max_len + 2, 60
        )

    wb.save(path)


# --------------------------------------------------------------------------
# main / CLI
# --------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper de resultados de búsqueda de Booking.com.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="URL de búsqueda de Booking.com (si se omite, usa la constante URL).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=OUTPUT_DIR,
        help="Carpeta donde guardar los resultados.",
    )
    parser.add_argument(
        "--formato", choices=FORMATOS_VALIDOS, action="append", default=None,
        help=(
            "Formato(s) de fichero por ejecución, además del dataset maestro "
            "SQLite. Repetible. Por defecto: xlsx. Pasa --formato json --formato "
            "csv para sustituirlo, o --sin-excel para no generar ninguno."
        ),
    )
    parser.add_argument(
        "--sin-excel", action="store_true",
        help="No generar el Excel por ejecución (solo el dataset maestro SQLite).",
    )
    parser.add_argument(
        "--db", type=Path, default=DB_PATH,
        help="Ruta del dataset maestro SQLite (acumulativo).",
    )
    parser.add_argument(
        "--sync-web", action="store_true",
        help="Publica también la captura en la base SQLite de la consola web.",
    )
    parser.add_argument(
        "--web-db", type=Path, default=ROOT / "data" / "booking-prices.sqlite",
        help="SQLite que usa la consola web cuando se pasa --sync-web.",
    )
    parser.add_argument(
        "--max-paginas", type=int, default=None,
        help="Límite de páginas a pedir (25 resultados/página). Por defecto: todas.",
    )
    parser.add_argument(
        "--no-headless", dest="headless", action="store_false",
        help="Abre el navegador visible (útil para resolver captchas a mano).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Log detallado (DEBUG).",
    )
    parser.add_argument(
        "--semanas", type=int, default=None,
        help=(
            "Barrido semanal: en vez de una única búsqueda, repite la "
            "búsqueda de 'url' una vez por semana durante N semanas, "
            "desplazando el checkin 7 días cada vez. Requiere --fecha-inicio."
        ),
    )
    parser.add_argument(
        "--fecha-inicio", type=str, default=None,
        help="Checkin de la primera semana, formato YYYY-MM-DD. Solo con --semanas.",
    )
    parser.add_argument(
        "--noches", type=int, default=None,
        help=(
            "Noches de estancia por semana analizada. Solo con --semanas. "
            "Por defecto usa la constante NOCHES del archivo."
        ),
    )
    parser.add_argument(
        "--detalle", action="store_true",
        help=(
            "Modo detalle: en vez de una búsqueda, abre la FICHA de cada "
            "hotel de --hoteles y extrae TODAS sus tarifas (habitación x "
            "régimen x cupos). Usa checkin/checkout/ocupación de 'url' o de "
            "FECHA_INICIO/NOCHES. Más lento y más frágil que el modo normal "
            "(scraping de HTML, no GraphQL) -> pensado para un comp-set "
            "pequeño, no para volumen."
        ),
    )
    parser.add_argument(
        "--hoteles", type=str, default=None,
        help=(
            "Lista de hoteles para --detalle, separados por comas, formato "
            "'countrycode/pagename' (se sacan de la URL de la ficha: "
            "booking.com/hotel/<countrycode>/<pagename>.html). "
            "Ej: es/ifa-altamarena,es/hotel-otro"
        ),
    )
    parser.add_argument(
        "--jobs", type=Path, default=None,
        help=(
            "Fichero YAML con varios jobs (búsquedas/barridos/detalles) a "
            "ejecutar en una sola pasada, p.ej. para cron nocturno. Cuando "
            "se pasa, ignora 'url' y el resto de flags de un solo job."
        ),
    )
    parser.set_defaults(headless=True)
    return parser.parse_args(argv)


# --------------------------------------------------------------------------
# Menú interactivo: cuando se ejecuta sin indicar modo por flags y hay
# terminal, se pregunta qué tipo de scrape lanzar.
#   - sencillo -> búsqueda de resultados (GraphQL, rápido y robusto).
#   - completo -> detalle de TODAS las tarifas por hotel (ficha, más lento).
# No aparece si se pasó --detalle o --jobs (backward-compatible) ni sin TTY
# (cron), donde por defecto se comporta como el modo sencillo de siempre.
# --------------------------------------------------------------------------

def _input_default(prompt: str, default: str = "") -> str:
    """input() que no revienta si no hay entrada (EOF/Ctrl-D): devuelve el
    valor por defecto en vez de lanzar EOFError."""
    try:
        return input(prompt).strip()
    except EOFError:
        return default


def _prompt_scrape_mode() -> str:
    """Pregunta el tipo de scrape. Devuelve 'sencillo' o 'completo'."""
    print("\n¿Qué tipo de scrape quieres ejecutar?")
    print("  [1] Sencillo  — búsqueda de resultados (rápido y robusto, vía GraphQL). El modo de siempre.")
    print("  [2] Completo  — detalle de TODAS las tarifas por hotel (habitación x régimen x cupos). En desarrollo.")
    while True:
        opcion = _input_default("Elige 1 o 2 [1]: ", "1") or "1"
        if opcion in ("1", "sencillo", "s"):
            return "sencillo"
        if opcion in ("2", "completo", "c"):
            return "completo"
        print("Opción no válida. Escribe 1 (sencillo) o 2 (completo).")


def _prompt_hoteles() -> str:
    """Pide la lista de hoteles del modo completo si no vino por --hoteles."""
    print("\nModo completo: indica los hoteles (fichas) a analizar.")
    print("Formato: countrycode/pagename separados por comas.")
    print("Ejemplo: es/ifa-altamarena,es/grand-hotel-vesuvio")
    print("(se sacan de la URL de la ficha: booking.com/hotel/<countrycode>/<pagename>.html)")
    while True:
        valor = _input_default("Hoteles: ")
        if valor:
            return valor
        print("No puede estar vacío.")


async def main(
    search_url: str,
    headless: bool = True,
    max_pages: int | None = None,
    output_dir: Path = OUTPUT_DIR,
    formatos: tuple[str, ...] = (),
    db_path: Path = DB_PATH,
    start_date: date | None = None,
    nights: int = 7,
    weeks: int | None = None,
    sync_web: bool = False,
    web_db_path: Path | None = None,
) -> None:
    if weeks is not None:
        hotels = await scrape_weekly(
            search_url,
            start_date=start_date,
            nights=nights,
            weeks=weeks,
            headless=headless,
            max_pages=max_pages,
        )
    else:
        hotels = await scrape_all_pages(search_url, headless=headless, max_pages=max_pages)

    if not hotels:
        log.warning("No se obtuvo ningún hotel; no se guarda nada.")
        return

    # Salida principal: dataset maestro consolidado (SQLite, acumulativo).
    save_to_db(hotels, db_path=db_path)
    if sync_web:
        sync_to_web_db(hotels, search_url, web_db_path or ROOT / "data" / "booking-prices.sqlite")
    # Ficheros por run: solo si se pidieron explícitamente con --formato.
    if formatos:
        save_results(hotels, output_dir=output_dir, formatos=formatos)


def _parse_hoteles_arg(hoteles_arg: str) -> list[tuple[str, str]]:
    """'es/ifa-altamarena,es/hotel-otro' -> [('es','ifa-altamarena'), ...]"""
    hoteles = []
    for item in hoteles_arg.split(","):
        item = item.strip()
        if not item:
            continue
        if "/" not in item:
            raise ValueError(
                f"Formato de hotel inválido: {item!r}. "
                "Esperado 'countrycode/pagename', ej. 'es/ifa-altamarena' "
                "(se saca de la URL de la ficha: booking.com/hotel/es/ifa-altamarena.html)."
            )
        country_code, pagename = item.split("/", 1)
        hoteles.append((country_code.strip(), pagename.strip()))
    if not hoteles:
        raise ValueError("--hoteles está vacío.")
    return hoteles


async def run_detalle(
    search_url: str,
    hoteles_arg: str,
    headless: bool = True,
    db_path: Path = DB_PATH,
    output_dir: Path = OUTPUT_DIR,
    formatos: tuple[str, ...] = (),
) -> list[TarifaDetalle]:
    """Punto de entrada del modo --detalle: saca checkin/checkout/ocupación
    de `search_url` (misma URL que el modo normal) y la lista de hoteles de
    `hoteles_arg`, scrapea el grid COMPLETO de tarifas de cada uno (ficha,
    no búsqueda) y lo guarda en la tabla tarifas_detalle del dataset maestro
    (más fichero por ejecución si `formatos` lo pide). Devuelve las tarifas
    obtenidas (usado también por el runner de jobs, Fase 3).
    """
    _, params = normalize_search_url(search_url)
    lang = params.get("lang", "es")
    ctx = SearchContext.from_params(params)
    if not ctx.checkin or not ctx.checkout:
        raise ValueError(
            "La URL no tiene checkin/checkout; --detalle los necesita para "
            "saber qué fechas pedir en cada ficha de hotel."
        )

    hoteles = _parse_hoteles_arg(hoteles_arg)
    log.info("Modo detalle: %d hoteles, %s -> %s", len(hoteles), ctx.checkin, ctx.checkout)

    tarifas = await scrape_detail_for_hotels(
        hoteles,
        checkin=ctx.checkin,
        checkout=ctx.checkout,
        adults=ctx.adultos or 2,
        children=ctx.ninos or 0,
        rooms=ctx.habitaciones or 1,
        lang=lang,
        headless=headless,
    )
    if not tarifas:
        log.warning("No se obtuvo ninguna tarifa; no se guarda nada.")
        return tarifas

    save_detalle_to_db(tarifas, db_path=db_path)
    if formatos:
        save_results(tarifas, output_dir=output_dir, formatos=formatos, prefix="booking_detalle")
    return tarifas


# --------------------------------------------------------------------------
# 7) Jobs (--jobs archivo.yaml): varios comp-sets/ocupaciones/horizontes en
#    una sola ejecución programada (cron nocturno, etc.)
# --------------------------------------------------------------------------

@dataclass
class Job:
    """Un job del fichero YAML: una búsqueda única, un barrido semanal, o
    un detalle de comp-set. Los campos no aplicables al `tipo` del job se
    quedan a None/valor por defecto."""

    nombre: str
    tipo: str  # "busqueda" | "barrido" | "detalle"
    url: str
    max_paginas: int | None = None
    headless: bool = True
    formato: tuple[str, ...] = ()
    # solo tipo="barrido"
    fecha_inicio: str | None = None
    noches: int = 7
    semanas: int | None = None
    # solo tipo="detalle"
    hoteles: str | None = None


_TIPOS_JOB_VALIDOS = ("busqueda", "barrido", "detalle")


def load_jobs(jobs_path: Path) -> list[Job]:
    """Carga y valida un fichero de jobs YAML. Formato esperado:

        defaults:              # opcional; cada job lo hereda salvo que lo
          headless: true        # sobreescriba explícitamente
          formato: [xlsx]

        jobs:
          - nombre: "Gran Canaria pareja 7 noches"
            tipo: busqueda
            url: "https://www.booking.com/searchresults.es.html?..."

          - nombre: "Fuerteventura barrido anual"
            tipo: barrido
            url: "https://www.booking.com/searchresults.es.html?..."
            fecha_inicio: "2026-09-01"
            noches: 7
            semanas: 12

          - nombre: "Comp-set IFA Altamarena"
            tipo: detalle
            url: "https://www.booking.com/searchresults.es.html?ss=...&checkin=...&checkout=...&group_adults=2&no_rooms=1&group_children=0"
            hoteles: "es/ifa-altamarena,es/hotel-otro"

    Lanza ValueError con un mensaje claro (job y campo) si algo falta o es
    inválido, en vez de fallar a mitad de ejecución.
    """
    if not jobs_path.exists():
        raise ValueError(f"No existe el fichero de jobs: {jobs_path}")
    try:
        raw = yaml.safe_load(jobs_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{jobs_path}: YAML inválido: {exc}") from None

    defaults = raw.get("defaults") or {}
    jobs_raw = raw.get("jobs") or []
    if not jobs_raw:
        raise ValueError(f"{jobs_path}: no hay ningún job bajo la clave 'jobs:'.")

    jobs: list[Job] = []
    for i, item in enumerate(jobs_raw, start=1):
        merged = {**defaults, **(item or {})}
        nombre = merged.get("nombre") or f"job_{i}"

        tipo = merged.get("tipo")
        if tipo not in _TIPOS_JOB_VALIDOS:
            raise ValueError(
                f"Job '{nombre}': 'tipo' debe ser uno de {_TIPOS_JOB_VALIDOS} "
                f"(llegó {tipo!r})."
            )
        url = merged.get("url")
        if not url:
            raise ValueError(f"Job '{nombre}': falta 'url'.")

        formato = merged.get("formato", ["xlsx"])
        if isinstance(formato, str):
            formato = [formato]
        invalidos = [f for f in formato if f not in FORMATOS_VALIDOS]
        if invalidos:
            raise ValueError(
                f"Job '{nombre}': formato(s) inválido(s) {invalidos}; "
                f"válidos: {FORMATOS_VALIDOS}"
            )

        if tipo == "barrido":
            if not merged.get("fecha_inicio"):
                raise ValueError(f"Job '{nombre}' (tipo=barrido): falta 'fecha_inicio'.")
            if not merged.get("semanas"):
                raise ValueError(f"Job '{nombre}' (tipo=barrido): falta 'semanas'.")
            try:
                date.fromisoformat(str(merged["fecha_inicio"]))
            except ValueError:
                raise ValueError(
                    f"Job '{nombre}': fecha_inicio {merged['fecha_inicio']!r} "
                    "no es válida (usa YYYY-MM-DD)."
                ) from None
        if tipo == "detalle" and not merged.get("hoteles"):
            raise ValueError(f"Job '{nombre}' (tipo=detalle): falta 'hoteles'.")

        jobs.append(Job(
            nombre=str(nombre),
            tipo=tipo,
            url=str(url),
            max_paginas=merged.get("max_paginas"),
            headless=bool(merged.get("headless", True)),
            formato=tuple(formato),
            fecha_inicio=str(merged["fecha_inicio"]) if merged.get("fecha_inicio") else None,
            noches=int(merged.get("noches", 7)),
            semanas=merged.get("semanas"),
            hoteles=merged.get("hoteles"),
        ))
    return jobs


async def run_jobs(
    jobs_path: Path,
    db_path: Path = DB_PATH,
    output_dir: Path = OUTPUT_DIR,
    sync_web: bool = False,
    web_db_path: Path | None = None,
) -> None:
    """Ejecuta todos los jobs de un fichero YAML, uno tras otro, reutilizando
    las funciones ya probadas de búsqueda/barrido/detalle. Resiliente: un
    job que falle se descarta (se loguea) y se continúa con el resto, igual
    que las semanas de un barrido o los hoteles de un detalle -> una
    ejecución nocturna con 10 jobs no se cae entera porque uno falle.
    """
    jobs = load_jobs(jobs_path)
    log.info("Cargados %d jobs de %s", len(jobs), jobs_path)

    ok = 0
    for i, job in enumerate(jobs, start=1):
        log.info("########## Job %d/%d: %s (%s) ##########", i, len(jobs), job.nombre, job.tipo)
        try:
            if job.tipo == "busqueda":
                hotels = await scrape_all_pages(
                    job.url, headless=job.headless, max_pages=job.max_paginas,
                )
                if hotels:
                    save_to_db(hotels, db_path=db_path)
                    if sync_web:
                        sync_to_web_db(hotels, job.url, web_db_path or ROOT / "data" / "booking-prices.sqlite")
                    if job.formato:
                        save_results(hotels, output_dir=output_dir, formatos=job.formato)
                else:
                    log.warning("Job '%s': sin resultados.", job.nombre)

            elif job.tipo == "barrido":
                hotels = await scrape_weekly(
                    job.url,
                    start_date=date.fromisoformat(job.fecha_inicio),
                    nights=job.noches,
                    weeks=job.semanas,
                    headless=job.headless,
                    max_pages=job.max_paginas,
                )
                if hotels:
                    save_to_db(hotels, db_path=db_path)
                    if sync_web:
                        sync_to_web_db(hotels, job.url, web_db_path or ROOT / "data" / "booking-prices.sqlite")
                    if job.formato:
                        save_results(hotels, output_dir=output_dir, formatos=job.formato)
                else:
                    log.warning("Job '%s': sin resultados.", job.nombre)

            elif job.tipo == "detalle":
                await run_detalle(
                    job.url, job.hoteles, headless=job.headless, db_path=db_path,
                    output_dir=output_dir, formatos=job.formato,
                )

            ok += 1
        except (ValueError, RuntimeError, PlaywrightError) as exc:
            log.error("Job '%s' DESCARTADO: %s", job.nombre, exc)

        if i < len(jobs):
            await asyncio.sleep(random.uniform(3.0, 6.0))

    log.info("Jobs completados: %d/%d.", ok, len(jobs))


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.jobs:
        try:
            asyncio.run(run_jobs(
                args.jobs,
                db_path=args.db,
                output_dir=args.output_dir,
                sync_web=args.sync_web,
                web_db_path=args.web_db,
            ))
        except ValueError as exc:
            log.error("%s", exc)
            sys.exit(1)
        sys.exit(0)

    # Precedencia: argumento de línea de comandos > constante URL.
    search_url = args.url or URL
    if not search_url:
        log.error("No se ha especificado ninguna URL.")
        log.error(
            "Pásala por línea de comandos o define la constante URL al inicio del archivo:"
        )
        log.error('Uso: python booking.py "<url_de_busqueda_de_booking>"')
        sys.exit(1)

    # Por defecto se exporta xlsx en cada ejecución (además del dataset
    # maestro SQLite). --formato lo sustituye; --sin-excel lo desactiva.
    if args.sin_excel:
        formatos: tuple[str, ...] = ()
    else:
        formatos = tuple(args.formato) if args.formato else ("xlsx",)

    # Modo de scrape: si no se pidió uno explícito por flags (--detalle) y hay
    # terminal, preguntar interactivamente (sencillo=búsqueda vs completo=
    # detalle). Con --detalle explícito o sin TTY (cron), no se pregunta.
    modo_completo = args.detalle
    hoteles_arg = args.hoteles
    if not args.detalle and sys.stdin.isatty():
        if _prompt_scrape_mode() == "completo":
            modo_completo = True
            if not hoteles_arg:
                hoteles_arg = _prompt_hoteles()

    if modo_completo:
        if not hoteles_arg:
            log.error(
                "El modo completo/--detalle requiere hoteles "
                "(--hoteles 'countrycode/pagename' o el menú interactivo)."
            )
            sys.exit(1)
        try:
            asyncio.run(
                run_detalle(
                    search_url, hoteles_arg, headless=args.headless, db_path=args.db,
                    output_dir=args.output_dir, formatos=formatos,
                )
            )
        except (ValueError, RuntimeError) as exc:
            log.error("%s", exc)
            sys.exit(1)
        sys.exit(0)

    # Precedencia CLI > constantes del archivo, igual que con URL.
    weeks = args.semanas if args.semanas is not None else SEMANAS
    fecha_inicio_str = args.fecha_inicio or FECHA_INICIO
    nights = args.noches if args.noches is not None else (NOCHES or 7)

    start_date = None
    if weeks:
        if not fecha_inicio_str:
            log.error(
                "SEMANAS está activado pero falta la fecha de inicio. "
                "Define FECHA_INICIO en el archivo o pasa --fecha-inicio (YYYY-MM-DD)."
            )
            sys.exit(1)
        try:
            start_date = date.fromisoformat(fecha_inicio_str)
        except ValueError:
            log.error(
                "La fecha de inicio no es válida: %r (usa YYYY-MM-DD)",
                fecha_inicio_str,
            )
            sys.exit(1)
        if weeks < 1:
            log.error("SEMANAS/--semanas debe ser 1 o más.")
            sys.exit(1)
    else:
        weeks = None  # 0 o None -> búsqueda única

    try:
        asyncio.run(
            main(
                search_url,
                headless=args.headless,
                max_pages=args.max_paginas,
                output_dir=args.output_dir,
                formatos=formatos,
                db_path=args.db,
                start_date=start_date,
                nights=nights,
                weeks=weeks,
                sync_web=args.sync_web,
                web_db_path=args.web_db,
            )
        )
    except (ValueError, RuntimeError) as exc:
        log.error("%s", exc)
        sys.exit(1)
