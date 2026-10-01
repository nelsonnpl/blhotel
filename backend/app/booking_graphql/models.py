"""Dataclasses del motor de scraping GraphQL: contexto de búsqueda y las dos
formas de fila que produce (`Hotel` para resultados de búsqueda, `TarifaDetalle`
para el grid completo de una ficha en modo --detalle)."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Any

from .config import MONEDA
from .helpers import num_noches, to_int


@dataclass
class SearchContext:
    """Contexto de la búsqueda, común a todos los hoteles de un mismo scrape.

    Se guarda en cada fila para poder comparar precios en el tiempo sin perder
    de qué búsqueda (fechas, ocupación) venían los datos.
    """

    checkin: str | None = None
    checkout: str | None = None
    noches: int | None = None
    adultos: int | None = None
    ninos: int | None = None
    habitaciones: int | None = None
    fecha_scrape: str = ""
    # --- identidad del comp-set / mercado (para agrupar y comparar) ---
    destino: str | None = None          # texto de búsqueda (ss)
    dest_id: str | None = None          # id de destino de Booking
    dest_type: str | None = None        # region / city / hotel...
    divisa_solicitada: str | None = None  # la que pedimos nosotros (MONEDA)
    filtro_regimen: str | None = None   # nflt mealplan, si lo hay

    @classmethod
    def from_params(cls, params: dict[str, str]) -> "SearchContext":
        checkin = params.get("checkin")
        checkout = params.get("checkout")
        return cls(
            checkin=checkin,
            checkout=checkout,
            noches=num_noches(checkin, checkout),
            adultos=to_int(params.get("group_adults")),
            ninos=to_int(params.get("group_children")),
            habitaciones=to_int(params.get("no_rooms")),
            fecha_scrape=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            destino=params.get("ss"),
            dest_id=params.get("dest_id"),
            dest_type=params.get("dest_type"),
            divisa_solicitada=params.get("selected_currency") or MONEDA,
            filtro_regimen=params.get("nflt"),
        )


@dataclass
class Hotel:
    """Un resultado de búsqueda ya "aplanado" y listo para exportar."""

    id: str | None = None
    nombre: str | None = None
    posicion: int | None = None          # ranking en resultados (1 = arriba del todo)
    precio: float | None = None          # precio total de la estancia (con descuento)
    precio_noche: float | None = None    # precio dividido entre nº de noches
    precio_original: float | None = None  # referencia mostrada del mismo producto
    descuento_pct: float | None = None   # descuento calculable sobre esa referencia
    moneda: str | None = None
    disponible: bool | None = None       # hay precio para esas fechas/ocupación
    sold_out: bool | None = None         # aparece pero sin disponibilidad (señal de demanda)
    observation_status: str | None = None  # available/unavailable/parse_error/unknown
    cerrado: bool | None = None          # isClosed: propiedad cerrada temporalmente
    cupos_restantes: int | None = None   # "Nos quedan N a este precio" (escasez/demanda)
    ocupacion_tarifa: int | None = None  # nº de personas que cubre la tarifa
    tarifa_terceros: bool | None = None  # inventario de un tercero (TPI), no directo del hotel
    tipo_alojamiento: str | None = None  # Hotel, Apartamento, Villa, Hostal...
    tipo_habitacion: str | None = None
    puntuacion: float | None = None
    num_resenas: int | None = None
    estrellas: float | None = None       # "categoría" del alojamiento (1-5)
    regimen: str | None = None
    cancelacion_gratis: bool | None = None
    cancelacion_hasta: str | None = None  # freeCancellationUntil
    direccion: str | None = None
    ubicacion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    distancia_playa: str | None = None
    ubicacion_top: bool | None = None      # isWithinBestLocationScoreArea
    distrito_popular: str | None = None    # popularFreeDistrictName
    ninos_gratis: bool | None = None       # blockMatchTags.childStaysForFree
    tiene_cuna: bool | None = None         # hasCrib
    url: str | None = None
    foto: str | None = None
    descripcion: str | None = None
    ciudad: str | None = None
    pais_code: str | None = None
    distancia_principal: str | None = None
    playas_cercanas: list[str] | None = None
    puntuacion_texto: str | None = None
    sin_prepago: bool | None = None
    ufi: str | None = None
    # --- contexto de la búsqueda (para tracking de precios) ---
    checkin: str | None = None
    checkout: str | None = None
    noches: int | None = None
    adultos: int | None = None
    ninos: int | None = None
    habitaciones: int | None = None
    fecha_scrape: str | None = None
    # --- identidad del comp-set / mercado ---
    destino: str | None = None
    dest_id: str | None = None
    dest_type: str | None = None
    divisa_solicitada: str | None = None
    filtro_regimen: str | None = None

    def as_row(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


@dataclass
class TarifaDetalle:
    """Una fila del grid COMPLETO de tarifas de la ficha de un hotel
    (`--detalle`). Grano = habitación x régimen x condiciones, tal como
    Booking lo muestra en la tabla de la página del hotel (#hprt-table).

    A diferencia de Hotel (1 precio "cabecera" por hotel en resultados de
    búsqueda), aquí sale CADA tarifa que el hotel ofrece para esas fechas.
    """

    hotel_id: str | None = None
    hotel_nombre: str | None = None
    hotel_pagename: str | None = None
    tipo_habitacion: str | None = None
    ocupacion_max: int | None = None
    precio_original: float | None = None
    precio_final: float | None = None
    moneda: str | None = None
    regimen: str | None = None
    prepago_texto: str | None = None
    programa: str | None = None       # beneficio/promoción visible en la fila, p.ej. Genius
    cancelacion_texto: str | None = None
    cancelacion_gratis: bool | None = None
    cupos_restantes: int | None = None
    blockuid: str | None = None
    # --- señales a nivel de hotel (repetidas en cada fila; útil para pivotar) ---
    sold_out_ficha: bool | None = None   # isSoldOut de la ficha (ninguna tarifa disponible)
    genius: bool | None = None
    breakfast_score: float | None = None  # 0-10; 0 = sin reseñas suficientes
    breakfast_type_id: int | None = None  # código interno de Booking, sin tabla de mapeo pública
    bed_comfort_score: float | None = None
    bed_comfort_resenas: int | None = None
    estrellas: float | None = None
    # --- contexto ---
    checkin: str | None = None
    checkout: str | None = None
    adultos: int | None = None
    ninos: int | None = None
    habitaciones: int | None = None
    fecha_scrape: str | None = None

    def as_row(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}
