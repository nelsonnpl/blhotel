"""PKG-27 (carril QA · I1-21, B2-19, G1-14/21): no-regresión que faltaba + receta.

Inventario previo (en verde; NO se duplican, solo se citan):
- I1-04 idempotencia x owner (jobs) .... backend/tests/test_pkg03_worker_guards.py:93
- I1-05 settled no reutiliza ........... backend/tests/test_pkg03_worker_guards.py:122
- I1-07 suma usage ..................... backend/tests/test_pkg04_accounting.py:15,
                                          backend/tests/test_pkg21_search_models_attachments.py:121
- I1-08 purga conserva mes ............. backend/tests/test_pkg04_accounting.py:86
- I1-11 history forjado ................. backend/tests/test_pkg23_jev_history_cost.py:15,31,41
- I1-17 patron `tiempo` ................. backend/tests/test_pkg21_search_models_attachments.py:35
- B2-19 cancel queued/running ........... backend/tests/test_jobs.py:52
- B2-19 redactado api_key ............... backend/tests/test_serpapi_key_redaction.py:98
Molde reutilizado: backend/tests/test_jobs.py:93-105 (reserva/budget).

Solo se anade lo que faltaba: idempotencia x owner en la capa de
presupuesto, doble-claim, truncado, worker.start idempotente y 402 con
DB vacia (dependencia de seed).

Receta de aislamiento (PKG-27d). `backend/tests/conftest.py` fija un sqlite
compartido en `tempfile.gettempdir()/scraping-hotels-pytest.sqlite` (en
macOS es `$TMPDIR`, NO `/tmp` literal). La suite DEPENDE del seed:
- sin grants (`local-revenue` -> admin en mercados 1/2) los GET con
  `targetId` devuelven 403 (p. ej. `test_hotel_history_...`);
- con reservas `reserved` acumuladas >= 50 USD el chat responde 402
  (techo mensual comprometido) aunque la DB este recien creada.
Receta (copia poblada, fresca en CADA pasada):
  FIXED=$(.venv/bin/python -c "import tempfile; print(tempfile.gettempdir())")/scraping-hotels-pytest.sqlite
  cp data/booking-prices.sqlite "$FIXED"   # seed: mercados 1/2 + grants local-revenue
  .venv/bin/python -m pytest backend/tests/ -q
Aislamiento barato por ejecucion: cada test NUEVO usa tmp_path (fichero
propio, cierre en finally) y nunca toca el fijo; el global flask_app.db
solo se toca con monkeypatch (se restaura solo).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from backend.app import flask_app
from backend.app.database import Database


def test_budget_reservation_idempotency_is_owner_scoped(tmp_path) -> None:
    """I1-04 (capa presupuesto): mismo requestId de otro owner nunca colisiona."""
    database = Database(tmp_path / "pkg27-budget-owner.sqlite")
    try:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        mine = database.reserve_assistant_budget("owner-a", "req-x", 0.40, 1.00, month)
        assert mine is not None and mine["status"] == "reserved"
        assert database.reserve_assistant_budget("owner-b", "req-x", 0.40, 1.00, month) is None
        again = database.reserve_assistant_budget("owner-a", "req-x", 0.40, 1.00, month)
        assert again is not None and again["status"] == "reserved"
        assert again["reservedUsd"] == 0.40
    finally:
        database.conn.close()


def test_job_double_claim_has_single_winner(tmp_path) -> None:
    """B2-19: el segundo claim no roba un trabajo ya en running."""
    database = Database(tmp_path / "pkg27-claim.sqlite")
    try:
        job = database.enqueue_job("job-27", "hotel_capture", {}, max_attempts=1)
        first = database.claim_next_job(["hotel_capture"])
        assert first is not None and first["id"] == job["id"]
        assert first["status"] == "running"
        assert database.claim_next_job(["hotel_capture"]) is None
        assert database.get_job(job["id"])["status"] == "running"
    finally:
        database.conn.close()


def test_job_failure_and_progress_truncate_long_text(tmp_path) -> None:
    """B2-19: fail_job trunca a 1000 y el progreso a 300 (redactado ya en test_serpapi)."""
    database = Database(tmp_path / "pkg27-truncate.sqlite")
    try:
        job = database.enqueue_job("job-long", "hotel_capture", {}, max_attempts=1)
        assert database.claim_next_job(["hotel_capture"])["id"] == job["id"]
        database.update_job_progress(job["id"], 50, "x" * 500)
        assert len(database.get_job(job["id"])["message"]) <= 300
        database.fail_job(job["id"], "y" * 5000)
        stored = database.get_job(job["id"])
        assert stored["status"] == "failed"
        assert len(stored["error"]) <= 1000
    finally:
        database.conn.close()


def test_worker_start_is_idempotent(tmp_path) -> None:
    """B2-19: doble start() no crea un segundo hilo."""
    from backend.app.jobs import BackgroundJobWorker

    database = Database(tmp_path / "pkg27-worker.sqlite")
    try:
        worker = BackgroundJobWorker(database)
        worker.start()
        first_thread = worker.thread
        assert first_thread is not None and first_thread.is_alive()
        worker.start()
        assert worker.thread is first_thread
    finally:
        database.conn.close()


def test_assistant_chat_returns_402_on_empty_db_without_seed(tmp_path, monkeypatch) -> None:
    """Aislamiento (d): DB vacia + techo 0 -> 402 sin llamar al proveedor ni necesitar seed."""
    empty = Database(tmp_path / "pkg27-empty.sqlite")
    try:
        monkeypatch.setattr(flask_app, "db", empty)
        runtime = replace(
            flask_app.settings,
            openrouter=replace(flask_app.settings.openrouter, api_key="test-key"),
            copilot_monthly_budget_usd=0.0,
        )
        monkeypatch.setattr(flask_app, "settings", runtime)
        monkeypatch.setattr(flask_app, "load_settings", lambda require_decodo=False: runtime)

        def _no_provider(*args, **kwargs):
            raise AssertionError("con 402 no debe llamarse al proveedor")

        monkeypatch.setattr(flask_app, "ask_openrouter", _no_provider)
        flask_app._assistant_rate_windows.clear()
        flask_app.clear_cache()
        response = flask_app.app.test_client().post(
            "/api/assistant/chat",
            json={"message": "¿Cuál es el ADR medio?", "mode": "quick"},
        )
        assert response.status_code == 402, response.get_data(as_text=True)
        assert response.get_json()["error"]
    finally:
        empty.conn.close()
        flask_app._assistant_rate_windows.clear()
        flask_app.clear_cache()
