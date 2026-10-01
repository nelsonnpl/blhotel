from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.app.database import Database


def test_recover_stale_jobs_requeues_retryable_and_fails_exhausted(tmp_path) -> None:
    database = Database(tmp_path / "jobs.sqlite")
    retryable = database.enqueue_job("job-retry", "hotel_capture", {}, max_attempts=2)
    exhausted = database.enqueue_job("job-failed", "hotel_capture", {}, max_attempts=1)
    assert database.claim_next_job(["hotel_capture"])["id"] == retryable["id"]
    assert database.claim_next_job(["hotel_capture"])["id"] == exhausted["id"]
    stale = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    database.conn.execute("UPDATE background_jobs SET updated_at = ?", (stale,))
    database.conn.commit()

    result = database.recover_stale_jobs()

    assert result == {"requeued": 1, "failed": 1}
    assert database.get_job("job-retry")["status"] == "queued"
    assert database.get_job("job-failed")["status"] == "failed"


def test_interrupted_review_capture_keeps_partial_rows_and_closes_pending_runs(tmp_path) -> None:
    database = Database(tmp_path / "review-jobs.sqlite")
    database.bootstrap_hotel_review_workspace()
    hotel_key = "atlas:servatur-monte-feliz"
    first = database.create_hotel_review_run(hotel_key, "google_maps")
    second = database.create_hotel_review_run(hotel_key, "booking")
    job = database.enqueue_job(
        "review-capture", "hotel_review_capture",
        {"tasks": [{"runId": first}, {"runId": second}]}, max_attempts=1,
    )
    assert database.claim_next_job(["hotel_review_capture"])["id"] == job["id"]
    database.update_hotel_review_run(first, status="running", rows_seen=5)
    stale = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    database.conn.execute("UPDATE background_jobs SET updated_at=? WHERE id=?", (stale, job["id"]))
    database.conn.commit()

    assert database.recover_stale_jobs() == {"requeued": 0, "failed": 1}
    rows = database.conn.execute(
        "SELECT id,status,rows_seen,error,completed_at FROM hotel_review_runs WHERE id IN (?,?)",
        (first, second),
    ).fetchall()
    by_id = {row["id"]: row for row in rows}
    assert by_id[first]["status"] == "partial" and by_id[first]["rows_seen"] == 5
    assert by_id[second]["status"] == "error"
    assert all(row["completed_at"] and "interrumpida" in row["error"] for row in rows)


def test_job_cancellation_is_cooperative_and_persistent(tmp_path) -> None:
    database = Database(tmp_path / "cancel.sqlite")
    queued = database.enqueue_job("job-queued", "assistant_analysis", {"ownerKey": "analyst"})
    cancelled = database.request_job_cancel(queued["id"])
    assert cancelled["status"] == "cancelled"
    assert cancelled["cancelRequested"] is True

    database.enqueue_job("job-running", "assistant_analysis", {"ownerKey": "analyst"})
    claimed = database.claim_next_job(["assistant_analysis"])
    assert claimed["status"] == "running"
    requested = database.request_job_cancel(claimed["id"])
    assert requested["status"] == "running"
    assert requested["cancelRequested"] is True
    database.cancel_job(claimed["id"])
    assert database.get_job(claimed["id"])["status"] == "cancelled"


def test_job_idempotency_reuses_the_same_request_key(tmp_path) -> None:
    database = Database(tmp_path / "idempotency.sqlite")
    first = database.enqueue_job(
        "job-first", "assistant_analysis", {"sessionId": 4}, idempotency_key="request-1"
    )
    second = database.get_job_by_idempotency("assistant_analysis", "request-1")

    assert second is not None
    assert second["id"] == first["id"]
    assert second["payload"] == {"sessionId": 4}


def test_active_assistant_job_is_scoped_to_session_and_owner(tmp_path) -> None:
    database = Database(tmp_path / "active.sqlite")
    queued = database.enqueue_job(
        "job-session", "assistant_analysis",
        {"sessionId": 7, "ownerKey": "analyst-a"},
    )

    assert database.active_assistant_job(7, "analyst-a")["id"] == queued["id"]
    assert database.active_assistant_job(7, "analyst-b") is None
    assert database.active_assistant_job(8, "analyst-a") is None


def test_budget_reservation_blocks_concurrent_caps_and_settles(tmp_path) -> None:
    database = Database(tmp_path / "budget.sqlite")
    # El gasto se imputa al mes en curso (create_assistant_run usa la fecha actual): el test no debe fijarlo.
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    first = database.reserve_assistant_budget("analyst", "request-1", 0.60, 1.00, month)

    assert first["status"] == "reserved"
    assert database.reserve_assistant_budget("analyst", "request-2", 0.50, 1.00, month) is None

    assert database.settle_assistant_budget("request-1", 0.42)["actualCostUsd"] == 0.42
    session = database.create_assistant_session("Budget", owner_key="analyst")
    database.create_assistant_run(session["id"], {"requestId": "request-1", "costUsd": 0.42})
    state = database.assistant_budget_state("analyst", month, 1.00)
    assert state["spentUsd"] == 0.42
    assert state["reservedUsd"] == 0.0
    assert state["remainingUsd"] == 0.58
