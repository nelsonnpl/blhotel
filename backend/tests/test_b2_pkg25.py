"""B2 PKG-25 (carril BE): logging central, dotenv única, límites síncronos, reintentos/cancel."""
from __future__ import annotations

import json
import logging

from backend.app import flask_app
from backend.app import serpapi_flights
from backend.app.database import Database
from backend.app.jobs import BackgroundJobWorker, JobCancelled
from backend.app.secure_logging import (
    PLACEHOLDER,
    SecretRedactFilter,
    redact_text,
)


SYNTH = "SYNTH-SECRET-ABC123XYZ"


def test_central_redact_removes_api_key_variants_and_literals() -> None:
    samples = [
        f"https://serpapi.com/search.json?engine=google_flights&api_key={SYNTH}&x=1",
        f'{{"api_key": "{SYNTH}"}}',
        f"Bearer {SYNTH}-bearer-token-xyz",
        f"Falla con password={SYNTH}",
    ]
    for raw in samples:
        redacted = redact_text(raw, (SYNTH,))
        assert SYNTH not in redacted
        assert PLACEHOLDER in redacted
    # Sin literal extra, el patrón api_key= basta.
    redacted = redact_text(f"ops api_key={SYNTH} end")
    assert "api_key" not in redacted.lower()
    assert SYNTH not in redacted


def test_central_filter_redacts_logs_without_secrets(caplog) -> None:
    logger = logging.getLogger("backend.app.jobs")
    # El `traceback` incluye la línea de código; se construye el par
    # dinámicamente para que el propio fichero no aporte el positivo.
    prefix = "api" + "_" + "key"
    with caplog.at_level(logging.ERROR, logger="backend.app.jobs"):
        try:
            raise ValueError(f"falla con {prefix}={SYNTH}")
        except ValueError:
            logger.exception("Background job synth failed")
    assert SYNTH not in caplog.text
    assert f"{prefix}=" not in caplog.text.lower()
    assert PLACEHOLDER in caplog.text


def test_serpapi_env_loads_once_per_process(monkeypatch) -> None:
    import dotenv

    calls = {"n": 0}
    real = dotenv.load_dotenv

    def counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(dotenv, "load_dotenv", counting)
    # Resetear el guardián para observar exactamente una lectura.
    monkeypatch.setattr(serpapi_flights, "_ENV_LOADED", False)
    serpapi_flights._ensure_env_loaded()
    serpapi_flights._ensure_env_loaded()
    serpapi_flights.serpapi_key()
    serpapi_flights.should_use_live_air_data()
    serpapi_flights.configured_air_routes()
    assert calls["n"] == 1
    assert serpapi_flights._ENV_LOADED is True
    assert serpapi_flights.SERPAPI_TIMEOUT_S == 90.0
    assert serpapi_flights.SERPAPI_MAX_ATTEMPTS == 2


def test_serpapi_retry_defaults_bounded_two_attempts() -> None:
    attempts_seen: list[int] = []
    prefix = "api" + "_" + "key"

    def boom(route, key, force_live=False):
        attempts_seen.append(1)
        raise ValueError(f"transient {prefix}={SYNTH}")

    try:
        serpapi_flights.fetch_google_flights_with_retry(
            serpapi_flights.AirSearchRoute("MAD", "LPA", "Madrid", "2026-08-24"),
            SYNTH,
            fetcher=boom,
        )
        raise AssertionError("debería fallar")
    except ValueError as exc:
        assert SYNTH not in str(exc)
        assert "api_key" not in str(exc).lower()
    # PA-92 por defecto: 2 intentos.
    assert len(attempts_seen) == 2


def test_sync_air_capture_over_limit_uses_413_with_job_hint(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "b2-sync-air.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    monkeypatch.setattr(flask_app, "serpapi_key", lambda: "test-key")
    # 8 rutas x 20 fechas aprox > 25: gran-canaria completo con cobertura amplia.
    response = flask_app.app.test_client().post(
        "/api/air-data/capture",
        json={
            "areaIds": ["gran-canaria"],
            "countryIds": [],
            "routeKeys": [],
            "direct": True,
            "outboundDate": "2026-08-24",
            "nights": 6,
            "dailyDays": 14,
            "weeklyUntilDays": 90,
            "maxQueries": 5000,
        },
    )
    assert response.status_code == 413
    body = response.get_json()
    assert "jobs/air-capture" in body["error"]
    assert body["syncMaxQueries"] == flask_app.SYNC_AIR_MAX_QUERIES


def test_sync_detail_over_limit_uses_413_with_job_hint() -> None:
    hotels = [
        {"hotelKey": f"/hotel/es/h{i}", "detailUrl": "https://booking.com/hotel/es/a.html"}
        for i in range(flask_app.SYNC_DETAIL_MAX_HOTELS + 1)
    ]
    response = flask_app.app.test_client().post(
        "/api/scrape/detail",
        json={
            "targetId": 1,
            "hotels": hotels,
            "checkIn": "2026-10-01",
            "checkOut": "2026-10-08",
            "adults": 2,
            "children": 0,
            "rooms": 1,
        },
    )
    assert response.status_code == 413
    assert "jobs/hotel-detail-capture" in response.get_json()["error"]


def test_air_capture_job_uses_single_attempt_no_silent_retries(monkeypatch, tmp_path) -> None:
    """`max_attempts` coherente: 1 en cola (el reintento vive por consulta PA-92)."""
    test_db = Database(tmp_path / "b2-max-attempts.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    seen: dict = {}

    class FakeWorker:
        def start(self):
            return None

        def enqueue(self, kind, payload, max_attempts=3, **kwargs):
            seen["kind"] = kind
            seen["max_attempts"] = max_attempts
            return {"id": "job-1", "status": "queued", "payload": payload}

    monkeypatch.setattr(flask_app, "active_job_worker", lambda: FakeWorker())
    response = flask_app.app.test_client().post(
        "/api/jobs/air-capture",
        json={"areaIds": ["gran-canaria"], "direct": True, "outboundDate": "2026-08-24", "nights": 6},
    )
    assert response.status_code == 202
    assert seen == {"kind": "air_capture", "max_attempts": 1}


def test_air_capture_cooperative_cancel_marks_run_cancelled(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "b2-cancel.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    monkeypatch.setattr(flask_app, "serpapi_key", lambda: "test-key")

    def fake_fetch(route, api_key: str, force_live: bool = False):
        return {
            "search_metadata": {"id": "S", "created_at": "2026-06-07T10:00:00Z"},
            "price_insights": {"typical_price_range": [100, 200]},
            "best_flights": [
                {
                    "price": 120,
                    "total_duration": 170,
                    "flights": [
                        {
                            "airline": "Test",
                            "flight_number": "T1",
                            "departure_airport": {"id": route.origin, "time": "2026-08-24 09:00"},
                            "arrival_airport": {"id": route.destination, "time": "2026-08-24 11:00"},
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr(flask_app, "fetch_google_flights", fake_fetch)

    from backend.app.models import AirCapturePayload

    payload = AirCapturePayload.model_validate(
        {
            "areaIds": ["gran-canaria"],
            "countryIds": ["Espana"],
            "routeKeys": ["MAD_LPA"],
            "direct": True,
            "outboundDate": "2026-08-24",
            "nights": 6,
            "singleDate": True,
        }
    )

    calls = {"n": 0}

    def cancelling_progress(value: int, message: str) -> None:
        calls["n"] += 1
        if calls["n"] >= 1:
            raise JobCancelled("Trabajo cancelado por el usuario")

    try:
        flask_app.capture_air_payload(payload, cancelling_progress)
        raise AssertionError("debería cancelarse")
    except JobCancelled:
        pass
    row = test_db.conn.execute("SELECT status FROM air_runs ORDER BY id DESC LIMIT 1").fetchone()
    assert row["status"] == "cancelled"


def test_fail_job_never_persists_secrets(tmp_path) -> None:
    database = Database(tmp_path / "b2-fail.sqlite")
    job = database.enqueue_job("job-synth", "hotel_capture", {}, max_attempts=1)
    assert database.claim_next_job(["hotel_capture"])["id"] == job["id"]
    prefix = "api" + "_" + "key"
    database.fail_job(job["id"], f"boom {prefix}={SYNTH} Bearer {SYNTH}")
    stored = database.get_job(job["id"])
    blob = json.dumps(stored)
    assert SYNTH not in blob
    assert "api_key" not in (stored["error"] or "").lower()
