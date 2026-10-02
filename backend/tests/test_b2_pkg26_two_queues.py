"""B2 PKG-26 (carril BE): dos colas — rapida (Copilot) y larga (capturas/Jev).

D3 aprobada = SI separar: un Jev de 30 min no bloquea el Copilot.
Arranque bajo demanda por cola; `recover_stale_jobs` 900 s solo reencola lo
genuinamente atascado (latido/lease por cola).
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from threading import Event

from backend.app.database import Database
from backend.app.jobs import BackgroundJobWorker


def _wait_until(predicate, timeout: float = 5.0, interval: float = 0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    return predicate()


def test_queue_mapping_separates_fast_and_long() -> None:
    assert BackgroundJobWorker.STALE_AFTER_SECONDS == 900
    worker = BackgroundJobWorker.__new__(BackgroundJobWorker)
    # Sin tocar DB: solo el mapeo estatico.
    assert BackgroundJobWorker.QUEUE_BY_KIND["assistant_analysis"] == BackgroundJobWorker.FAST_QUEUE
    for kind in (
        "air_capture",
        "hotel_capture",
        "hotel_detail_capture",
        "hotel_review_capture",
        "hotel_review_analysis",
    ):
        assert BackgroundJobWorker.QUEUE_BY_KIND[kind] == BackgroundJobWorker.LONG_QUEUE
    # Desconocidos van a larga para proteger la rapida.
    assert BackgroundJobWorker.QUEUE_BY_KIND.get("unknown-kind", BackgroundJobWorker.LONG_QUEUE) == BackgroundJobWorker.LONG_QUEUE


def test_start_on_demand_per_queue(tmp_path) -> None:
    database = Database(tmp_path / "pkg26-demand.sqlite")
    try:
        worker = BackgroundJobWorker(database)
        worker.recovery_interval = 60.0
        worker.heartbeat_interval = 0.05
        worker.register("assistant_analysis", lambda payload, progress: {"ok": True})
        worker.register("hotel_review_capture", lambda payload, progress: {"ok": True})

        # Solo la rapida arranca al encolar rapido.
        fast_job = worker.enqueue("assistant_analysis", {"ownerKey": "o", "sessionId": 1}, max_attempts=1)
        assert fast_job["status"] == "queued"
        assert worker.thread is not None and worker.thread.is_alive()
        assert worker.slow_thread is None or not worker.slow_thread.is_alive()

        # La larga arranca solo al encolar largo.
        worker.enqueue("hotel_review_capture", {"tasks": []}, max_attempts=1)
        slow = _wait_until(lambda: worker.slow_thread is not None and worker.slow_thread.is_alive())
        assert slow
        assert worker.thread.is_alive()
    finally:
        database.conn.close()


def test_long_capture_does_not_block_copilot(tmp_path) -> None:
    """Captura larga en curso + chat Copilot -> el chat progresa sin esperar."""
    database = Database(tmp_path / "pkg26-isolation.sqlite")
    try:
        long_started = Event()
        long_release = Event()

        def long_handler(payload: dict, progress) -> dict:
            long_started.set()
            progress(10, "Jev en curso (30 min simulado)")
            # Simula el Jev largo bloqueado; el latido de respaldo mantiene el lease.
            finished = long_release.wait(timeout=10)
            assert finished, "el test debe liberar el Jev largo"
            progress(90, "Jev terminando")
            return {"ok": True, "simulated": "jev-30min"}

        def fast_handler(payload: dict, progress) -> dict:
            progress(50, "Copilot en curso")
            return {"reply": "ok"}

        worker = BackgroundJobWorker(database)
        worker.recovery_interval = 60.0
        worker.heartbeat_interval = 0.05
        worker.register("hotel_review_capture", long_handler)
        worker.register("assistant_analysis", fast_handler)

        long_job = worker.enqueue("hotel_review_capture", {"tasks": [{"runId": 1}]}, max_attempts=1)
        assert long_started.wait(timeout=5), "la captura larga debe empezar"
        assert database.get_job(long_job["id"])["status"] == "running"

        fast_job = worker.enqueue(
            "assistant_analysis", {"ownerKey": "o", "sessionId": 9, "message": "hola"}, max_attempts=1
        )
        succeeded = _wait_until(
            lambda: (database.get_job(fast_job["id"]) or {}).get("status") == "succeeded",
            timeout=5.0,
        )
        assert succeeded, "el Copilot debe progresar sin esperar al Jev largo"
        # La larga sigue en curso: no fue bloqueada ni duplicada por la rapida.
        assert database.get_job(long_job["id"])["status"] == "running"

        long_release.set()
        done = _wait_until(
            lambda: (database.get_job(long_job["id"]) or {}).get("status") == "succeeded",
            timeout=5.0,
        )
        assert done
    finally:
        try:
            long_release.set()
        except Exception:
            pass
        database.conn.close()


def test_recovery_does_not_duplicate_running_with_heartbeat(tmp_path) -> None:
    """Recovery 900 s: con latido reciente no reencola; sin latido si."""
    database = Database(tmp_path / "pkg26-recovery.sqlite")
    try:
        worker = BackgroundJobWorker(database)
        worker.heartbeat_interval = 0.05
        worker.register("hotel_capture", lambda payload, progress: {"ok": True})

        # Trabajo en marcha con latido fresco: no se toca.
        fresh = database.enqueue_job("job-fresh", "hotel_capture", {}, max_attempts=1)
        assert database.claim_next_job(["hotel_capture"])["id"] == fresh["id"]
        worker._touch(fresh["id"])
        result = database.recover_stale_jobs(stale_after_seconds=900)
        assert result == {"requeued": 0, "failed": 0}
        assert database.get_job("job-fresh")["status"] == "running"

        # Trabajo genuinamente atascado (1 h sin latido): se reencola.
        stale = database.enqueue_job("job-stale", "hotel_capture", {}, max_attempts=2)
        assert database.claim_next_job(["hotel_capture"])["id"] == stale["id"]
        old = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        database.conn.execute("UPDATE background_jobs SET updated_at = ? WHERE id = ?", (old, stale["id"]))
        database.conn.commit()
        result = database.recover_stale_jobs(stale_after_seconds=900)
        assert result == {"requeued": 1, "failed": 0}
        assert database.get_job("job-stale")["status"] == "queued"
        # Drenar la cola para aislar el caso borde (FIFO: stale volveria primero).
        assert database.claim_next_job(["hotel_capture"])["id"] == stale["id"]
        database.complete_job(stale["id"], {"ok": True})
        assert database.get_job("job-stale")["status"] == "succeeded"

        # Corte 900 s: 600 s no es stale, 960 s si.
        boundary_ok = database.enqueue_job("job-600", "hotel_capture", {}, max_attempts=1)
        assert database.claim_next_job(["hotel_capture"])["id"] == boundary_ok["id"]
        recent = (datetime.now(timezone.utc) - timedelta(seconds=600)).isoformat()
        database.conn.execute("UPDATE background_jobs SET updated_at = ? WHERE id = ?", (recent, boundary_ok["id"]))
        database.conn.commit()
        assert database.recover_stale_jobs(stale_after_seconds=900) == {"requeued": 0, "failed": 0}
        assert database.get_job("job-600")["status"] == "running"

        old960 = (datetime.now(timezone.utc) - timedelta(seconds=960)).isoformat()
        database.conn.execute("UPDATE background_jobs SET updated_at = ? WHERE id = ?", (old960, boundary_ok["id"]))
        database.conn.commit()
        # max_attempts=1 y attempts=1 -> agotado -> failed, no duplicado en queued.
        assert database.recover_stale_jobs(stale_after_seconds=900) == {"requeued": 0, "failed": 1}
        assert database.get_job("job-600")["status"] == "failed"
    finally:
        database.conn.close()


def test_worker_uses_900s_stale_cutoff(tmp_path) -> None:
    database = Database(tmp_path / "pkg26-cutoff.sqlite")
    try:
        worker = BackgroundJobWorker(database)
        assert worker.stale_after_seconds == 900
        assert worker.heartbeat_interval < 900
        assert worker.recovery_interval == 30.0
    finally:
        database.conn.close()
