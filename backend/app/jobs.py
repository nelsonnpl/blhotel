from __future__ import annotations

import logging
from threading import Event, Thread
from time import monotonic
from typing import Callable
from uuid import uuid4

from .database import Database

logger = logging.getLogger(__name__)
JobHandler = Callable[[dict, Callable[[int, str], None]], dict]


class JobCancelled(Exception):
    """Raised by a handler when the operator requested cancellation."""


class BackgroundJobWorker:
    """Small persistent queue for a single Flask deployment.

    Jobs live in SQLite, so clients can reconnect and poll their state. This
    intentionally keeps the worker abstraction small; a multi-instance
    deployment can replace it with a dedicated queue without changing routes.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.handlers: dict[str, JobHandler] = {}
        self.wake = Event()
        self.thread: Thread | None = None
        self._next_recovery_at = 0.0

    def register(self, kind: str, handler: JobHandler) -> None:
        self.handlers[kind] = handler

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        recovered = self.db.recover_stale_jobs()
        if recovered["requeued"] or recovered["failed"]:
            logger.warning("Recovered stale jobs: %s", recovered)
        self._next_recovery_at = monotonic() + 30
        self.thread = Thread(target=self._run, name="revenue-job-worker", daemon=True)
        self.thread.start()

    def enqueue(self, kind: str, payload: dict, max_attempts: int = 3, idempotency_key: str | None = None) -> dict:
        if kind not in self.handlers:
            raise ValueError(f"Tipo de trabajo no registrado: {kind}")
        if idempotency_key:
            existing = self.db.get_job_by_idempotency(kind, idempotency_key)
            if existing is not None:
                return existing
        job = self.db.enqueue_job(uuid4().hex, kind, payload, max_attempts=max_attempts, idempotency_key=idempotency_key)
        self.wake.set()
        return job

    def _run(self) -> None:
        while True:
            job = self.db.claim_next_job(list(self.handlers))
            if not job:
                if monotonic() >= self._next_recovery_at:
                    recovered = self.db.recover_stale_jobs()
                    if recovered["requeued"] or recovered["failed"]:
                        logger.warning("Recovered stale jobs: %s", recovered)
                    self._next_recovery_at = monotonic() + 30
                self.wake.wait(timeout=1)
                self.wake.clear()
                continue
            handler = self.handlers[job["kind"]]
            try:
                if self.db.is_job_cancel_requested(job["id"]):
                    self.db.cancel_job(job["id"])
                    continue

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
