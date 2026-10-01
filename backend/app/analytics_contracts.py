"""Contrato semántico de consultas analíticas de solo lectura.

La primera versión expone el alcance actual del dashboard (la última foto de
un mercado). Los identificadores y fórmulas son estables para que la UI y el
Copilot no tengan que conocer las claves internas de ``dashboard_metrics``.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


SEMANTIC_VERSION = "revenue-semantics.v1"


METRIC_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "adr_mean",
        "label": "ADR medio",
        "unit": "EUR/room_night",
        "formula": "media de price_per_night sobre filas con precio, noches y moneda comparables",
        "path": ("market", "avgPricePerNight"),
    },
    {
        "id": "adr_median",
        "label": "ADR mediano",
        "unit": "EUR/room_night",
        "formula": "mediana de price_per_night sobre filas con precio, noches y moneda comparables",
        "path": ("market", "medianPricePerNight"),
    },
    {
        "id": "hotel_count",
        "label": "Hoteles comparables",
        "unit": "hotels",
        "formula": "recuento de filas con precio, noches y moneda comparables",
        "path": ("rateShoppingIndex", "totalCompetitors"),
    },
    {
        "id": "adr_movement_pct",
        "label": "Variación ADR",
        "unit": "percent",
        "formula": "variación porcentual del ADR medio frente a la foto comparable anterior",
        "path": ("movement", "avgPricePerNightChangePct"),
    },
    {
        "id": "comparison_coverage_pct",
        "label": "Cobertura comparable",
        "unit": "percent",
        "formula": "filas actuales que cumplen la equivalencia de producto frente a la foto anterior",
        "path": ("comparison", "matchedCoveragePct"),
    },
    {
        "id": "adr_min",
        "label": "ADR mínimo",
        "unit": "EUR/room_night",
        "formula": "mínimo de price_per_night sobre filas comparables",
        "path": ("market", "minPricePerNight"),
    },
    {
        "id": "adr_max",
        "label": "ADR máximo",
        "unit": "EUR/room_night",
        "formula": "máximo de price_per_night sobre filas comparables",
        "path": ("market", "maxPricePerNight"),
    },
)

_CATALOG_BY_ID = {item["id"]: item for item in METRIC_CATALOG}


class AnalyticsQueryPayload(BaseModel):
    """Consulta declarativa limitada a la primera superficie semántica.

    No acepta SQL, expresiones ni filtros silenciosamente ignorados. El
    endpoint devuelve un error si se solicita una dimensión que aún no tiene
    implementación en esta fase.
    """

    model_config = ConfigDict(extra="forbid")

    dataset: Literal["hotel_market"] = "hotel_market"
    targetId: int = Field(ge=1)
    snapshotId: int | None = Field(default=None, ge=1)
    metrics: list[str] = Field(min_length=1, max_length=8)
    dimensions: list[Literal["market", "hotel", "checkIn"]] = Field(default_factory=list, max_length=2)
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0, le=100_000)
    semanticVersion: Literal["revenue-semantics.v1"] = SEMANTIC_VERSION

    @model_validator(mode="after")
    def validate_metrics(self):
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("dimensions no puede contener identificadores duplicados")
        if "market" in self.dimensions and len(self.dimensions) > 1:
            raise ValueError("market no se puede combinar con otras dimensions")
        if self.dimensions and self.dimensions != ["market"]:
            unsupported = {"adr_movement_pct", "comparison_coverage_pct"}.intersection(self.metrics)
            if unsupported:
                raise ValueError("Las métricas de movimiento solo están disponibles en dimensión market")
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError("metrics no puede contener identificadores duplicados")
        unknown = sorted(set(self.metrics) - set(_CATALOG_BY_ID))
        if unknown:
            raise ValueError(f"Métricas no soportadas: {', '.join(unknown)}")
        unsupported_filters = sorted(set(self.filters) - {"targetId", "hotelKey", "checkIn"})
        if unsupported_filters:
            raise ValueError(f"Filtros no soportados en esta fase: {', '.join(unsupported_filters)}")
        if "targetId" in self.filters and self.filters["targetId"] != self.targetId:
            raise ValueError("filters.targetId debe coincidir con targetId")
        if "hotelKey" in self.filters and (not isinstance(self.filters["hotelKey"], str) or not self.filters["hotelKey"].strip()):
            raise ValueError("filters.hotelKey debe ser texto no vacío")
        if "checkIn" in self.filters:
            if not isinstance(self.filters["checkIn"], str):
                raise ValueError("filters.checkIn debe tener formato YYYY-MM-DD")
            try:
                date.fromisoformat(self.filters["checkIn"])
            except ValueError as exc:
                raise ValueError("filters.checkIn debe tener formato YYYY-MM-DD") from exc
        if {"hotelKey", "checkIn"}.intersection(self.filters) and {"adr_movement_pct", "comparison_coverage_pct"}.intersection(self.metrics):
            raise ValueError("Las métricas de movimiento no están disponibles con filtros de observación")
        return self


def metric_catalog() -> list[dict[str, Any]]:
    """Devuelve una copia serializable para evitar mutaciones globales."""
    return [dict(item, path=list(item["path"])) for item in METRIC_CATALOG]


def metric_definition(metric_id: str) -> dict[str, Any]:
    return _CATALOG_BY_ID[metric_id]
