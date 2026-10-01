"""Adaptadores HTTP de meteorología, sin persistencia.

Los adaptadores devuelven registros normalizados o un recurso AEMET pendiente
de normalizar. No escriben SQLite: la captura decide después si el dato era
conocido en su instante y qué retención aplicar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx

from .weather import WeatherRecord, make_weather_record


class WeatherProviderError(RuntimeError):
    """Error de transporte o contrato de una fuente meteorológica."""


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_DAILY_VARIABLES = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "sunshine_duration",
)
AEMET_BASE_URL = "https://opendata.aemet.es/opendata"
AEMET_HOSTS = {"opendata.aemet.es", "www.aemet.es"}


def _as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def normalise_open_meteo_daily(
    payload: dict[str, Any],
    *,
    location_key: str,
    retrieved_at: str | datetime,
    capture_at: str | datetime,
    timezone_name: str = "Atlantic/Canary",
    source_url: str | None = None,
) -> list[WeatherRecord]:
    """Normaliza las variables diarias seleccionadas de Open-Meteo.

    Las fechas diarias se interpretan en la zona solicitada y cada fila
    conserva proveedor, modelo, unidades y semántica temporal.
    """
    daily = payload.get("daily")
    if not isinstance(daily, dict) or not isinstance(daily.get("time"), list):
        raise WeatherProviderError("Respuesta Open-Meteo sin bloque daily.time")
    times = daily["time"]
    try:
        local_zone = ZoneInfo(timezone_name)
    except Exception as exc:  # noqa: BLE001 - configuración inválida del adaptador
        raise WeatherProviderError(f"Zona horaria meteorológica inválida: {timezone_name}") from exc

    daily_units = payload.get("daily_units") if isinstance(payload.get("daily_units"), dict) else {}
    model = payload.get("model")
    records: list[WeatherRecord] = []
    for index, day in enumerate(times):
        try:
            valid_at = datetime.fromisoformat(f"{day}T00:00:00").replace(tzinfo=local_zone)
        except (TypeError, ValueError) as exc:
            raise WeatherProviderError(f"Fecha diaria Open-Meteo inválida: {day!r}") from exc
        values = {
            variable: _as_float((daily.get(variable) or [None] * len(times))[index])
            if index < len(daily.get(variable) or []) else None
            for variable in OPEN_METEO_DAILY_VARIABLES
        }
        units = {
            variable: str(daily_units[variable])
            for variable in OPEN_METEO_DAILY_VARIABLES
            if daily_units.get(variable) is not None
        }
        records.append(make_weather_record(
            provider="open-meteo",
            dataset="forecast.daily",
            kind="forecast",
            location_key=location_key,
            valid_at=valid_at,
            local_date=str(day),
            retrieved_at=retrieved_at,
            capture_at=capture_at,
            values=values,
            units=units,
            model=str(model) if model else None,
            source_url=source_url,
        ))
    return records


class OpenMeteoClient:
    """Cliente de previsión diaria; no guarda respuestas ni hace reintentos."""

    def __init__(self, http_client: httpx.AsyncClient | None = None, base_url: str = OPEN_METEO_FORECAST_URL):
        self.http_client = http_client
        self.base_url = base_url

    async def forecast_daily(
        self,
        *,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        location_key: str,
        retrieved_at: str | datetime,
        capture_at: str | datetime,
        timezone_name: str = "Atlantic/Canary",
    ) -> list[WeatherRecord]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join(OPEN_METEO_DAILY_VARIABLES),
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timezone": timezone_name,
        }
        owns_client = self.http_client is None
        client = self.http_client or httpx.AsyncClient(timeout=20.0)
        try:
            response = await client.get(self.base_url, params=params)
            if response.status_code >= 400:
                raise WeatherProviderError(f"Open-Meteo HTTP {response.status_code}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise WeatherProviderError("Respuesta Open-Meteo no es JSON") from exc
            return normalise_open_meteo_daily(
                payload,
                location_key=location_key,
                retrieved_at=retrieved_at,
                capture_at=capture_at,
                timezone_name=timezone_name,
                source_url=str(response.url),
            )
        except httpx.HTTPError as exc:
            raise WeatherProviderError(f"Error de red Open-Meteo: {exc}") from exc
        finally:
            if owns_client:
                await client.aclose()


@dataclass(frozen=True)
class AemetResource:
    endpoint_url: str
    data_url: str
    metadata_url: str | None
    retrieved_at: str
    payload: Any


def _validate_aemet_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in AEMET_HOSTS:
        raise WeatherProviderError("AEMET devolvió un enlace de descarga no permitido")
    return value


class AemetClient:
    """Cliente HATEOAS de AEMET; deja la normalización de cada endpoint aislada."""

    def __init__(self, api_key: str, http_client: httpx.AsyncClient | None = None, base_url: str = AEMET_BASE_URL):
        if not api_key.strip():
            raise ValueError("AEMET_API_KEY es obligatorio para consultar AEMET")
        self.api_key = api_key.strip()
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")

    async def fetch_resource(self, endpoint: str) -> AemetResource:
        endpoint_url = _validate_aemet_url(endpoint)
        owns_client = self.http_client is None
        client = self.http_client or httpx.AsyncClient(timeout=20.0)
        try:
            response = await client.get(endpoint_url, headers={"api_key": self.api_key})
            if response.status_code >= 400:
                raise WeatherProviderError(f"AEMET HTTP {response.status_code}")
            try:
                envelope = response.json()
            except ValueError as exc:
                raise WeatherProviderError("Respuesta inicial de AEMET no es JSON") from exc
            data_url = envelope.get("datos") if isinstance(envelope, dict) else None
            metadata_url = envelope.get("metadatos") if isinstance(envelope, dict) else None
            if not isinstance(data_url, str):
                raise WeatherProviderError("AEMET no devolvió el enlace datos")
            data_url = _validate_aemet_url(data_url)
            if metadata_url is not None:
                metadata_url = _validate_aemet_url(str(metadata_url))
            data_response = await client.get(data_url)
            if data_response.status_code >= 400:
                raise WeatherProviderError(f"AEMET descarga HTTP {data_response.status_code}")
            try:
                payload = data_response.json()
            except ValueError:
                payload = data_response.text
            retrieved_at = datetime.now().astimezone().isoformat()
            return AemetResource(endpoint_url, data_url, metadata_url, retrieved_at, payload)
        except httpx.HTTPError as exc:
            raise WeatherProviderError(f"Error de red AEMET: {exc}") from exc
        finally:
            if owns_client:
                await client.aclose()

    async def municipal_daily(self, municipality_id: str) -> AemetResource:
        return await self.fetch_resource(f"{self.base_url}/api/prediccion/especifica/municipio/diaria/{municipality_id}")

    async def conventional_observations(self) -> AemetResource:
        return await self.fetch_resource(f"{self.base_url}/api/observacion/convencional/todas")
