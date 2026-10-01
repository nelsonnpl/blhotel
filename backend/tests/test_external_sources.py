from backend.app.external_sources import public_source_catalog
from backend.app.flask_app import app
from backend.app.database import Database

from pathlib import Path
import tempfile


def test_public_catalog_contains_governed_sources_without_secrets() -> None:
    catalog = public_source_catalog()

    assert {item["id"] for item in catalog} == {
        "istac-accommodation",
        "dataestur-segittur",
        "aemet-opendata",
        "aena-traffic",
        "eurostat-tourism",
    }
    assert all(item["url"].startswith("https://") for item in catalog)
    assert all("api_key" not in item and "token" not in item for item in catalog)
    assert all(item["decision_uses"] for item in catalog)
    istac = next(item for item in catalog if item["id"] == "istac-accommodation")
    dataestur = next(item for item in catalog if item["id"] == "dataestur-segittur")
    assert any(dataset["id"] == "C00065A_000038" for dataset in istac["recommended_datasets"])
    assert any(dataset["id"] == "C00065A_000060" for dataset in istac["recommended_datasets"])
    assert any(
        dataset["id"] == "PRECIOS_ALOJAMIENTOS_HOTELEROS_DL"
        for dataset in dataestur["recommended_datasets"]
    )


def test_external_sources_endpoint_declares_schema_and_access_requirements() -> None:
    response = app.test_client().get("/api/external/sources")

    assert response.status_code == 200
    body = response.get_json()
    assert body["schemaVersion"] == "external-sources.v1"
    aemet = next(item for item in body["sources"] if item["id"] == "aemet-opendata")
    assert aemet["requires_api_key"] is True
    assert aemet["granularity"] == "horaria / diaria"


def test_external_cache_upserts_normalized_rows_without_duplicates() -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Database(Path(directory) / "external.sqlite")
        base = {
            "sourceId": "istac-accommodation",
            "datasetId": "C00065A_000038",
            "metric": "adr",
            "unit": "EUR",
            "geographyType": "microdestination",
            "geographyCode": "Maspalomas",
            "periodStart": "2026-01-01",
            "periodEnd": "2026-12-31",
            "value": 214.5,
            "revision": "2026-08",
            "qualityStatus": "ok",
            "metadata": {"coverage": "annual"},
        }
        assert database.upsert_external_observations([base, {**base, "value": 215.0}]) == 2
        rows = database.list_external_observations(source_id="istac-accommodation")
        assert len(rows) == 1
        assert rows[0]["value"] == 215.0
        assert rows[0]["metadata"] == {"coverage": "annual"}
        status = database.external_cache_status()
        assert status[0]["rowCount"] == 1


def test_external_observations_endpoint_supports_filters_and_limit() -> None:
    response = app.test_client().get(
        "/api/external/observations?source=istac-accommodation&metric=adr&limit=1"
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["schemaVersion"] == "external-observations.v1"
    assert len(body["observations"]) <= 1
