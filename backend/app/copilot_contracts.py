"""Contratos pequeños y explícitos para las respuestas de Revenue Copilot.

Estos modelos no obligan todavía al proveedor LLM a devolver JSON. Sirven para
validar el paquete de datos que sí controla la aplicación antes de enviarlo al
modelo y para conservar la procedencia de cada cifra que se muestra al usuario.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EvidenceQuality = Literal["verified", "partial", "stale", "missing", "unverified"]
ComparisonStatus = Literal["matched", "matched_partial", "unmatched", "not_applicable"]
EvidenceEntity = Literal["market", "hotel", "route", "capture", "external", "data_quality"]
RoutingStrategy = Literal["single_expert", "expert_panel"]
ExpertName = Literal["hotel_revenue", "air_access", "market_checker", "data_quality"]


class EvidenceRecord(BaseModel):
    """Una cifra observada o calculada con su semántica y procedencia."""

    model_config = ConfigDict(extra="forbid")

    evidenceId: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    entityType: EvidenceEntity
    entityId: str | None = None
    targetId: int | None = None
    value: int | float | str | bool | None = None
    unit: str | None = None
    period: str | None = None
    sourceId: str | None = None
    datasetId: str | None = None
    observedAt: str | None = None
    snapshotId: int | None = None
    sourceTable: str | None = None
    sourceRowIds: list[int] = Field(default_factory=list)
    quality: EvidenceQuality
    comparability: ComparisonStatus = "not_applicable"
    calculation: str | None = None
    queriedAt: str | None = None
    sourceObservedAt: str | None = None


class EvidenceBundle(BaseModel):
    """Paquete versionado que viaja dentro del contexto del asistente."""

    model_config = ConfigDict(extra="forbid")

    schemaVersion: Literal["revenue-evidence.v1"] = "revenue-evidence.v1"
    records: list[EvidenceRecord] = Field(default_factory=list, max_length=80)


class DataGateResult(BaseModel):
    """Resultado normalizado del control de calidad previo al razonamiento."""

    model_config = ConfigDict(extra="forbid")

    blocked: bool
    canRecommend: bool
    warnings: list[str] = Field(default_factory=list)
    severity: Literal["ok", "warning", "blocked"]


class RoutingPlan(BaseModel):
    """Plan local de expertos; no implica llamadas adicionales al proveedor."""

    model_config = ConfigDict(extra="forbid")

    schemaVersion: Literal["revenue-routing.v1"] = "revenue-routing.v1"
    requestedMode: Literal["quick", "auto", "analysis", "decision"]
    complexity: Literal["simple", "multi_signal", "complex"]
    strategy: RoutingStrategy
    experts: list[ExpertName] = Field(min_length=1, max_length=3)
    aggregation: Literal["direct", "single_call_synthesis", "multi_call_synthesis"]
    model: str | None = None
    selectionReason: str | None = Field(default=None, max_length=240)
    requiresRecommendation: bool = False
    reason: str = Field(min_length=1, max_length=240)
