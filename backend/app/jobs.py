from __future__ import annotations

import logging
from datetime import datetime, timezone
from threading import Event, Lock, Thread
from time import monotonic
from typing import Callable
from uuid import uuid4

from .database import Database
from .secure_logging import install_secret_redact_filter

logger = logging.getLogger(__name__)
# B2-09: el worker puede vivir sin importar `flask_app`; el filtro central
# debe estar activo aquí también para que `logger.exception` nunca emita
# secretos aunque el import llegue solo desde `jobs`.
install_secret_redact_filter(("", __name__))
JobHandler = Callable[[dict, Callable[[int, str], None]], dict]


class JobCancelled(Exception):
    """Raised by a handler when the operator requested cancellation."""


class BackgroundJobWorker:
    """Persistent queue with two isolated lanes for a single Flask deployment.

    B2-07/08 (D3 = SI separar): cola rapida (Copilot/assistant) y cola larga
    (capturas hotel/aerea/detalle/resenas/Jev). Un Jev de 30 min en la cola
    larga nunca bloquea el chat Copilot porque cada cola tiene su propio hilo
    y su propio `claim_next_job` disjunto.

    Jobs live in SQLite, so clients can reconnect and poll their state. This
    intentionally keeps the worker abstraction small; a multi-instance
    deployment can replace it with a dedicated queue without changing routes.

    Recuperacion: `recover_stale_jobs` con 900 s solo reencola lo
    genuinamente atascado. Cada trabajo en curso mantiene latido (lease por
    cola): `progress()` ya toca `updated_at`, y un latido de respaldo lo
    refresca cada `heartbeat_interval` para que un trabajo lento (p. ej. Jev
    30 min) nunca parezca atascado. Sin latido >900 s se considera caida del
    proceso y se reencola/falla segun intentos.
    """

    FAST_QUEUE = "fast"
    LONG_QUEUE = "long"
    # B2-07: rapida = Copilot/assistant; larga = todo lo demas.
    FAST_KINDS = frozenset({"assistant_analysis"})
    LONG_KINDS = frozenset(
        {
            "air_capture",
            "hotel_capture",
            "hotel_detail_capture",
            "hotel_review_capture",
            "hotel_review_analysis",
        }
    )
    QUEUE_BY_KIND: dict[str, str] = {
        "assistant_analysis": "fast",
        "air_capture": "long",
        "hotel_capture": "long",
        "hotel_detail_capture": "long",
        "hotel_review_capture": "long",
        "hotel_review_analysis": "long",
    }
    STALE_AFTER_SECONDS = 900
    RECOVERY_INTERVAL_S = 30.0
    HEARTBEAT_INTERVAL_S = 60.0

    def __init__(self, db: Database) -> None:
        self.db = db
        self.handlers: dict[str, JobHandler] = {}
        self.queue_by_kind: dict[str, str] = {}
        # Compat: `wake`/`thread` son el carril rapido (test_pkg27 los usa).
        self.wake = Event()
        self.slow_wake = Event()
        self.thread: Thread | None = None
        self.slow_thread: Thread | None = None
        self._next_recovery_at: dict[str, float] = {
            self.FAST_QUEUE: 0.0,
            self.LONG_QUEUE: 0.0,
        }
        self._recovery_lock = Lock()
        self._running_lock = Lock()
        self._running: dict[str, str] = {}
        self.heartbeat_interval = self.HEARTBEAT_INTERVAL_S
        self.recovery_interval = self.RECOVERY_INTERVAL_S
        self.stale_after_seconds = self.STALE_AFTER_SECONDS

    def queue_for(self, kind: str) -> str:
        """Return the lane for a job kind (unknown kinds go long to protect fast)."""
        if kind in self.queue_by_kind:
            return self.queue_by_kind[kind]
        return self.QUEUE_BY_KIND.get(kind, self.LONG_QUEUE)

    def kinds_for_queue(self, queue: str) -> list[str]:
        return [kind for kind in self.handlers if self.queue_for(kind) == queue]

    def register(self, kind: str, handler: JobHandler, queue: str | None = None) -> None:
        self.handlers[kind] = handler
        self.queue_by_kind[kind] = queue or self.QUEUE_BY_KIND.get(kind, self.LONG_QUEUE)

    def _wake_for(self, queue: str) -> Event:
        return self.wake if queue == self.FAST_QUEUE else self.slow_wake

    def _thread_for(self, queue: str) -> Thread | None:
        return self.thread if queue == self.FAST_QUEUE else self.slow_thread

    def _set_thread_for(self, queue: str, thread: Thread) -> None:
        if queue == self.FAST_QUEUE:
            self.thread = thread
        else:
            self.slow_thread = thread

    def start(self, queue: str | None = None) -> None:
        """Start worker threads on demand (per queue when `queue` is given).

        Sin argumento arranca ambos carriles (idempotente, para compat con
        `test_worker_start_is_idempotent`); `enqueue()` siempre llama con su
        cola para el arranque bajo demanda por cola.
        """
        queues = [queue] if queue else [self.FAST_QUEUE, self.LONG_QUEUE]
        with self._recovery_lock:
            recovered = self.db.recover_stale_jobs(stale_after_seconds=self.stale_after_seconds)
            if recovered["requeued"] or recovered["failed"]:
                logger.warning("Recovered stale jobs: %s", recovered)
        for item in queues:
            existing = self._thread_for(item)
            if existing and existing.is_alive():
                continue
            self._next_recovery_at[item] = monotonic() + self.recovery_interval
            name = "revenue-job-worker" if item == self.FAST_QUEUE else "revenue-job-worker-long"
            thread = Thread(target=self._run, args=(item,), name=name, daemon=True)
            self._set_thread_for(item, thread)
            thread.start()

    def enqueue(self, kind: str, payload: dict, max_attempts: int = 3, idempotency_key: str | None = None) -> dict:
        if kind not in self.handlers:
            raise ValueError(f"Tipo de trabajo no registrado: {kind}")
        if idempotency_key:
            existing = self.db.get_job_by_idempotency(kind, idempotency_key)
            if existing is not None:
                return existing
        job = self.db.enqueue_job(uuid4().hex, kind, payload, max_attempts=max_attempts, idempotency_key=idempotency_key)
        # Arranque bajo demanda por cola: solo despierta/arranca su carril.
        self.start(queue=self.queue_for(kind))
        self._wake_for(self.queue_for(kind)).set()
        return job

    def _touch(self, job_id: str) -> None:
        """Latido de respaldo: refresca `updated_at` sin mover progreso."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            with self.db.lock:
                self.db.conn.execute(
                    "UPDATE background_jobs SET updated_at = ? WHERE id = ? AND status = 'running'",
                    (now, job_id),
                )
                self.db.conn.commit()
        except Exception:  # noqa: BLE001 - el latido nunca rompe el trabajo
            pass

    def _run(self, queue: str) -> None:
        wake = self._wake_for(queue)
        while True:
            kinds = self.kinds_for_queue(queue)
            job = self.db.claim_next_job(kinds) if kinds else None
            if not job:
                if monotonic() >= self._next_recovery_at.get(queue, 0.0):
                    with self._recovery_lock:
                        recovered = self.db.recover_stale_jobs(stale_after_seconds=self.stale_after_seconds)
                        if recovered["requeued"] or recovered["failed"]:
                            logger.warning("Recovered stale jobs: %s", recovered)
                    self._next_recovery_at[queue] = monotonic() + self.recovery_interval
                wake.wait(timeout=1)
                wake.clear()
                continue
            self._execute(job, queue)

    def _execute(self, job: dict, queue: str) -> None:
        handler = self.handlers[job["kind"]]
        stop = Event()

        def _beat() -> None:
            while not stop.wait(self.heartbeat_interval):
                self._touch(job["id"])

        with self._running_lock:
            self._running[job["id"]] = queue
        beat = Thread(target=_beat, name=f"revenue-job-heartbeat-{queue}", daemon=True)
        beat.start()
        try:
            try:
                if self.db.is_job_cancel_requested(job["id"]):
                    self.db.cancel_job(job["id"])
                    return

                def progress(value: int, message: str) -> None:
                    if self.db.is_job_cancel_requested(job["id"]):
                        raise JobCancelled("Trabajo cancelado por el usuario")
                    self.db.update_job_progress(job["id"], value, message)

                result = handler(job["payload"], progress)
                if self.db.is_job_cancel_requested(job["id"]):
                    self.db.cancel_job(job["id"])
                else:
                    self.db.complete_job(job["id"], result)
            except JobCancelled as exc:
                self.db.cancel_job(job["id"], str(exc))
            except Exception as exc:  # noqa: BLE001 - failures are persisted for the operator
                logger.exception("Background job %s failed", job["id"])
                self.db.fail_job(job["id"], str(exc))
        finally:
            stop.set()
            with self._running_lock:
                self._running.pop(job["id"], None)
