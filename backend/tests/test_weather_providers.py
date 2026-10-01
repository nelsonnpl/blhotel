import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from backend.app.weather import known_at_capture
from backend.app.weather_providers import (
    AemetClient,
    OpenMeteoClient,
    WeatherProviderError,
    normalise_open_meteo_daily,
)


CAPTURE = "2026-09-07T08:00:00+00:00"


def open_meteo_payload():
    return {
        "model": "test-model",
        "daily": {
            "time": ["2026-09-10", "2026-09-11"],
            "weather_code": [1, 3],
            "temperature_2m_max": [27.1, 26.4],
            "temperature_2m_min": [20.2, 19.8],
            "precipitation_sum": [0.0, 1.2],
            "precipitation_probability_max": [5, 40],
            "wind_speed_10m_max": [22.0, 25.0],
            "sunshine_duration": [36000, 30000],
        },
        "daily_units": {
            "weather_code": "wmo code", "temperature_2m_max": "°C", "temperature_2m_min": "°C",
            "precipitation_sum": "mm", "precipitation_probability_max": "%",
            "wind_speed_10m_max": "km/h", "sunshine_duration": "s",
        },
    }


def test_open_meteo_daily_normalisation_preserves_units_and_time_semantics():
    records = normalise_open_meteo_daily(
        open_meteo_payload(), location_key="gran-canaria-sur",
        retrieved_at="2026-09-07T07:55:00+00:00", capture_at=CAPTURE,
    )
    assert len(records) == 2
    assert records[0].values["temperature_2m_max"] == 27.1
    assert records[0].units["precipitation_sum"] == "mm"
    assert records[0].valid_at.tzinfo is not None
    assert len(known_at_capture(records)) == 2


def test_open_meteo_missing_daily_values_are_unknown():
    payload = open_meteo_payload()
    payload["daily"].pop("sunshine_duration")
    records = normalise_open_meteo_daily(
        payload, location_key="gran-canaria-sur", retrieved_at=CAPTURE, capture_at=CAPTURE,
    )
    assert records[0].values["sunshine_duration"] is None


def test_open_meteo_http_errors_are_controlled():
    async def handler(request):
        return httpx.Response(429, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(WeatherProviderError, match="HTTP 429"):
        asyncio.run(OpenMeteoClient(client).forecast_daily(
            latitude=27.7, longitude=-15.6, start_date="2026-09-10", end_date="2026-09-11",
            location_key="sur", retrieved_at=CAPTURE, capture_at=CAPTURE,
        ))
    asyncio.run(client.aclose())


def test_aemet_hateoas_resource_does_not_accept_external_download_hosts():
    class FakeClient:
        async def get(self, url, **kwargs):
            return httpx.Response(200, json={"datos": "https://example.test/data"})

    with pytest.raises(WeatherProviderError, match="enlace de descarga"):
        asyncio.run(AemetClient("secret", http_client=FakeClient()).fetch_resource(
            "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
        ))


def test_aemet_hateoas_fetches_data_link_without_exposing_key():
    class FakeClient:
        def __init__(self):
            self.urls = []

        async def get(self, url, **kwargs):
            self.urls.append((url, kwargs))
            if url.endswith("todas"):
                return httpx.Response(200, json={"datos": "https://opendata.aemet.es/data/123", "metadatos": "https://opendata.aemet.es/meta/123"})
            return httpx.Response(200, json=[{"idema": "1234", "temperatura": "25.0"}])

    fake = FakeClient()
    resource = asyncio.run(AemetClient("secret", http_client=fake).fetch_resource(
        "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
    ))
    assert resource.payload[0]["idema"] == "1234"
    assert fake.urls[0][1]["headers"] == {"api_key": "secret"}
    assert "secret" not in resource.data_url
