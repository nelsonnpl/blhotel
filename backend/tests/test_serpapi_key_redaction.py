from __future__ import annotations

import json
import logging

from backend.app import flask_app
from backend.app.database import Database
from backend.app.serpapi_flights import (
    AirSearchRoute,
    fetch_google_flights_with_retry,
    redact_serpapi_key_text,
)

SYNTH_KEY = "SYNTH-SECRET-ABC123XYZ"


def test_redact_removes_api_key_param_variants() -> None:
    samples = [
        f"https://serpapi.com/search.json?engine=google_flights&api_key={SYNTH_KEY}&departure_id=MAD",
        f"Client error '401 Unauthorized' for url 'https://serpapi.com/search.json?api_key={SYNTH_KEY}&engine=x'",
        f'{{"api_key": "{SYNTH_KEY}"}}',
        f"api_key={SYNTH_KEY}",
        f"api_key: {SYNTH_KEY}",
    ]
    for raw in samples:
        redacted = redact_serpapi_key_text(raw, SYNTH_KEY)
        assert "api_key" not in redacted.lower()
        assert SYNTH_KEY not in redacted
        assert "[clave oculta]" in redacted


def test_redact_replaces_literal_key_without_prefix() -> None:
    raw = f"SerpAPI error invalid key {SYNTH_KEY} rejected"
    redacted = redact_serpapi_key_text(raw, SYNTH_KEY)
    assert SYNTH_KEY not in redacted
    assert "[clave oculta]" in redacted


def test_retry_redacts_synthetic_provider_error() -> None:
    route = AirSearchRoute("MAD", "LPA", "Madrid", "2026-08-24")

    def boom(_route, _key, force_live=False):
        raise ValueError(
            f"Client error '401' for url 'https://serpapi.com/search.json?api_key={SYNTH_KEY}&engine=google_flights'"
        )

    try:
        fetch_google_flights_with_retry(route, SYNTH_KEY, attempts=1, fetcher=boom)
        raise AssertionError("debería fallar")
    except Exception as exc:  # noqa: BLE001
        text = str(exc)
        assert "api_key" not in text.lower()
        assert SYNTH_KEY not in text


def test_capture_air_payload_redacts_route_errors(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "redact-air.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    monkeypatch.setattr(flask_app, "serpapi_key", lambda: SYNTH_KEY)

    def boom(route, api_key: str, force_live: bool = False):
        raise ValueError(
            f"Client error '403 Forbidden' for url 'https://serpapi.com/search.json?engine=google_flights&api_key={api_key}&departure_id={route.origin}'"
        )

    monkeypatch.setattr(flask_app, "fetch_google_flights", boom)

    client = flask_app.app.test_client()
    response = client.post(
        "/api/air-data/capture",
        json={
            "areaIds": ["gran-canaria"],
            "countryIds": ["Espana"],
            "routeKeys": ["MAD_LPA"],
            "direct": True,
            "outboundDate": "2026-08-24",
            "nights": 6,
            "singleDate": True,
            "dailyDays": 1,
            "weeklyUntilDays": 14,
            "maxQueries": 10,
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["errors"]
    blob = json.dumps(payload["errors"])
    assert "api_key" not in blob.lower()
    assert SYNTH_KEY not in blob
    # La fila de ejecución persiste conteos pero nunca el secreto.
    row = test_db.conn.execute(
        "SELECT queries_failed, status FROM air_runs WHERE id = ?", (payload["run"]["id"],)
    ).fetchone()
    assert row["queries_failed"] >= 1
    assert SYNTH_KEY not in json.dumps(dict(row))


def test_fail_job_redacts_for_all_jobs(tmp_path) -> None:
    database = Database(tmp_path / "redact-fail.sqlite")
    job = database.enqueue_job("job-synth", "hotel_capture", {}, max_attempts=1)
    claimed = database.claim_next_job(["hotel_capture"])
    assert claimed["id"] == job["id"]
    database.fail_job(job["id"], f"boom api_key={SYNTH_KEY} url https://x/?api_key={SYNTH_KEY}")
    stored = database.get_job(job["id"])
    assert stored["status"] == "failed"
    assert "api_key" not in (stored["error"] or "").lower()
    assert SYNTH_KEY not in (stored["error"] or "")


def test_jobs_logger_redacts_api_key(caplog) -> None:
    jobs_logger = logging.getLogger("backend.app.jobs")
    # El `traceback` incluye nombres de fichero/función con `api_key` como
    # identificador de código; lo que nunca debe salir es el par `api_key=`
    # ni el valor sintético.
    prefix = "api" + "_" + "key"
    with caplog.at_level(logging.ERROR, logger="backend.app.jobs"):
        try:
            raise ValueError(f"falla con {prefix}={SYNTH_KEY}")
        except ValueError:
            jobs_logger.exception("Background job synth failed")
    text = caplog.text
    assert SYNTH_KEY not in text
    assert f"{prefix}=" not in text.lower()
    assert "[clave oculta]" in text
