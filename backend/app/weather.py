"""Contrato temporal y geográfico para enriquecer una foto con meteorología.

Este módulo no consulta proveedores ni persiste datos todavía. Define la
semántica que deben respetar AEMET, Open-Meteo u otro adaptador: qué se sabía
en el momento de la extracción y qué dato solo se recuperó retrospectivamente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


WeatherKind = Literal["observed", "forecast"]


def parse_utc(value: str | datetime) -> datetime:
    """Normaliza un instante ISO a UTC y rechaza horas sin zona."""
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("La meteorología requiere instantes con zona horaria")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class WeatherRecord:
    provider: str
    dataset: str
    kind: WeatherKind
    location_key: str
    valid_at: datetime
    local_date: str | None
    retrieved_at: datetime
    capture_at: datetime
    values: dict[str, float | None]
    units: dict[str, str]
    known_at_capture: bool
    retrospective: bool
    model: str | None = None
    source_url: str | None = None


def make_weather_record(
    *,
    provider: str,
    dataset: str,
    kind: WeatherKind,
    location_key: str,
    valid_at: str | datetime,
    retrieved_at: str | datetime,
    capture_at: str | datetime,
    values: dict[str, float | None],
    units: dict[str, str],
    local_date: str | None = None,
    model: str | None = None,
    source_url: str | None = None,
) -> WeatherRecord:
    """Construye una observación/previsión con semántica *as of capture*.

    Una previsión solo es conocida en la foto si se recuperó antes o justo al
    capturar. Una observación física recuperada después puede conservarse como
    retrospectiva, pero nunca se presenta como contexto disponible entonces.
    """
    valid = parse_utc(valid_at)
    retrieved = parse_utc(retrieved_at)
    captured = parse_utc(capture_at)
    known = retrieved <= captured
    retrospective = retrieved > captured and valid <= captured
    return WeatherRecord(
        provider=provider,
        dataset=dataset,
        kind=kind,
        location_key=location_key,
        valid_at=valid,
        local_date=local_date,
        retrieved_at=retrieved,
        capture_at=captured,
        values=dict(values),
        units=dict(units),
        known_at_capture=known,
        retrospective=retrospective,
        model=model,
        source_url=source_url,
    )


def known_at_capture(records: list[WeatherRecord]) -> list[WeatherRecord]:
    """Filtra el contexto que podía existir al tomar la foto."""
    return [record for record in records if record.known_at_capture and not record.retrospective]
