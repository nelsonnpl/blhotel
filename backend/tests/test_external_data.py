from __future__ import annotations

from pathlib import Path
import tempfile

import httpx
import pytest

from backend.app.database import Database
from backend.app.external_data import (
    DATAESTUR_API_BASE,
    ExternalDataError,
    filter_istac_territories,
    fetch_dataestur_hotel_prices,
    fetch_istac_csv,
    parse_dataestur_hotel_prices,
    parse_istac_csv,
)
from backend.app.assistant import build_revenue_context
from backend.app.copilot_gateway import project_context_for_experts


def test_dataestur_price_parser_handles_cp1252_and_missing_values() -> None:
    payload = (
        "AÑO;MES;CATEGORIA_ALOJAMIENTO;CCAA;PROVINCIA;PERIODO_ANTELACION;"
        "PRECIO_CHECK_IN_ENTRE_SEMANA;PRECIO_CHECK_IN_FIN_DE_SEMANA\n"
        "2026;8;Hotel 4 Estrellas;Canarias;Las Palmas;1 Mes;195,0;203,5\n"
        "2026;8;Hotel 4 Estrellas;Canarias;Las Palmas;2 Semanas;;210,0\n"
    ).encode("cp1252")

    rows = parse_dataestur_hotel_prices(payload, fetched_at="2026-09-06T00:00:00+00:00")

    assert len(rows) == 3
    assert rows[0]["periodStart"] == "2026-08-01"
    assert rows[0]["value"] == 195.0
    assert rows[0]["segment"].endswith("day_type=weekday")
    assert rows[-1]["value"] == 210.0


def test_dataestur_sync_uses_http_response_but_stores_only_rows() -> None:
    payload = (
        "AÑO;MES;CATEGORIA_ALOJAMIENTO;CCAA;PROVINCIA;PERIODO_ANTELACION;"
        "PRECIO_CHECK_IN_ENTRE_SEMANA;PRECIO_CHECK_IN_FIN_DE_SEMANA\n"
        "2026;8;Hotel 5 Estrellas;Canarias;Las Palmas;1 Semana;300,0;320,0\n"
    ).encode("cp1252")

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(f"{DATAESTUR_API_BASE}/PRECIOS_")
        assert request.url.params["CCAA"] == "Canarias"
        assert request.url.params["Provincia"] == "Todos"
        return httpx.Response(200, content=payload, request=request)

    with tempfile.TemporaryDirectory() as directory:
        database = Database(Path(directory) / "external.sqlite")
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            result = fetch_dataestur_hotel_prices(
                database,
                start_year=2026,
                start_month=8,
                end_year=2026,
                end_month=8,
                client=client,
            )
        assert result["downloadedRows"] == 2
        assert database.external_cache_status()[0]["rowCount"] == 2
        run = database.latest_external_ingestion(
            "dataestur-segittur", "PRECIOS_ALOJAMIENTOS_HOTELEROS_DL"
        )
        assert run and run["status"] == "success" and run["rowCount"] == 2
        assert database.conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE '%payload%'").fetchone()[0] == 0


def test_istac_parser_accepts_long_format() -> None:
    payload = (
        "TIME_PERIOD;MICRODESTINO;INDICADOR;OBS_VALUE\n"
        "2025;Maspalomas;Tarifa media diaria (ADR);214,5\n"
        "2025;Maspalomas;Ingresos por habitación disponible (RevPAR);155,2\n"
    ).encode("utf-8")

    rows = parse_istac_csv(payload, dataset_id="C00065A_000038")

    assert {row["metric"] for row in rows} == {"adr", "revpar"}
    assert all(row["geographyCode"] == "Maspalomas" for row in rows)
    assert all(row["periodStart"] == "2025-01-01" for row in rows)


def test_istac_parser_accepts_official_localized_headers_and_monthly_periods() -> None:
    payload = (
        "MEDIDAS#es,MEDIDAS_CODE,TIME_PERIOD#es,TIME_PERIOD_CODE,TERRITORIO#es,TERRITORIO_CODE,OBS_VALUE\n"
        "Tarifa media diaria,ADR,07/2026,2026-M07,Gran Canaria,ES705,149.11\n"
        "Tasa de ocupación por plaza,TASA_OCUPACION_PLAZA,2025,2025,Canarias,ES70,71.24\n"
        "Empleos por cada 100 plazas alojativas,EMPLEOS,07/2026,2026-M07,Gran Canaria,ES705,20\n"
    ).encode("utf-8")

    rows = parse_istac_csv(payload, dataset_id="C00065A_000038")

    adr = next(row for row in rows if row["metric"] == "adr")
    occupancy = next(row for row in rows if row["metric"] == "occupancy_rate")
    assert adr["geographyCode"] == "Gran Canaria"
    assert adr["periodStart"] == "2026-07-01"
    assert adr["periodEnd"] == "2026-07-31"
    assert adr["metadata"]["officialGeographyCode"] == "ES705"
    assert occupancy["periodStart"] == "2025-01-01"
    assert occupancy["periodEnd"] == "2025-12-31"
    assert len(rows) == 2


def test_istac_sync_marks_empty_parser_result_as_error() -> None:
    payload = b"TIME_PERIOD;TERRITORIO;OBS_VALUE\n2026;Canarias;\n"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payload, request=request)

    with tempfile.TemporaryDirectory() as directory:
        database = Database(Path(directory) / "external.sqlite")
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(ExternalDataError, match="sin filas normalizables"):
                fetch_istac_csv(database, dataset_id="C00065A_000038", version="1.43", client=client)
        run = database.latest_external_ingestion("istac-accommodation", "C00065A_000038")
        assert run and run["status"] == "error" and run["rowCount"] == 0


def test_istac_territory_filter_keeps_only_official_scope() -> None:
    rows = [
        {"metadata": {"officialGeographyCode": "ES70"}},
        {"metadata": {"officialGeographyCode": "ES705"}},
        {"metadata": {"officialGeographyCode": "ES704"}},
    ]
    scoped = filter_istac_territories(rows, ["ES70", "ES705"])
    assert [item["metadata"]["officialGeographyCode"] for item in scoped] == ["ES70", "ES705"]


def test_external_cache_is_projected_into_copilot_with_provenance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Database(Path(directory) / "external.sqlite")
        target = database.upsert_target("Gran Canaria (Sur)", "https://example.test/gran-canaria")
        database.upsert_external_observations(
            [{
                "sourceId": "dataestur-segittur",
                "datasetId": "PRECIOS_ALOJAMIENTOS_HOTELEROS_DL",
                "metric": "hotel_price_by_lead_time",
                "unit": "EUR/room_night",
                "geographyType": "province",
                "geographyCode": "Las Palmas",
                "segment": "category=Hotel 4 Estrellas;lead_time=1 Mes;day_type=weekday",
                "periodStart": "2026-02-01",
                "value": 201.0,
            }]
        )
        context = build_revenue_context(database, target.id)
        assert context["contextoExterno"]["filtroProvincia"] == "Las Palmas"
        assert context["contextoExterno"]["dataesturPrecios"][0]["value"] == 201.0
        projected = project_context_for_experts(context, ["hotel_revenue"])
        evidence = projected["evidencia"]["records"]
        assert any(record["entityType"] == "external" for record in evidence)
        assert any(record["sourceId"] == "dataestur-segittur" for record in evidence)
