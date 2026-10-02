from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.app import flask_app
from backend.app.assistant import ask_openrouter
from backend.app.config import OpenRouterSettings
from backend.app.database import Database


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(api_key="test-key", model="test/model", base_url="https://example.test/v1")


def test_chat_two_rounds_sum_cost_and_visible_in_budget(tmp_path, monkeypatch) -> None:
    """I1-06/I1-07: usage.include + suma de rondas con _sum_usage; coste visible."""
    captured: dict = {}
    calls = {"n": 0}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, _url, *, headers, json, timeout):
            captured.update(json)
            return None  # nunca se usa: se parchea _post_chat_completion

    monkeypatch.setattr("backend.app.assistant.httpx.Client", FakeClient)

    usages = [
        {"cost": 0.015, "prompt_tokens": 10, "completion_tokens": 5},
        {"cost": 0.025, "prompt_tokens": 7, "completion_tokens": 3},
    ]

    def fake_post(client, settings, headers, payload, deadline, telemetry):
        assert payload.get("usage") == {"include": True}
        idx = calls["n"]
        calls["n"] += 1
        if idx == 0:
            return {
                "usage": dict(usages[0]),
                "choices": [{
                    "message": {
                        "content": "",
                        "tool_calls": [{
                            "id": "call-1", "type": "function",
                            "function": {"name": "buscar_hotel", "arguments": "{}"},
                        }],
                    }
                }],
            }
        return {
            "usage": dict(usages[1]),
            "choices": [{"message": {"content": "**Lectura** ok"}}],
        }

    monkeypatch.setattr("backend.app.assistant._post_chat_completion", fake_post)

    telemetry: dict = {}
    # db no nulo para permitir ronda de herramientas; sin mercado devuelve error controlado.
    reply = ask_openrouter(
        _settings(), "hola", {}, db=object(), target_id=None,
        telemetry=telemetry, mode="quick",
    )
    assert reply
    assert calls["n"] == 2
    assert abs(float(telemetry["usage"]["cost"]) - 0.04) < 1e-9
    assert telemetry["usage"]["prompt_tokens"] == 17

    database = Database(tmp_path / "chat.sqlite")
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    session = database.create_assistant_session("Chat", owner_key="analyst")
    database.create_assistant_run(session["id"], telemetry)
    row = database.conn.execute("SELECT cost_usd FROM assistant_runs").fetchone()
    assert float(row["cost_usd"]) > 0
    state = database.assistant_budget_state("analyst", month, 10.0)
    assert state["spentUsd"] > 0


def test_purge_preserves_current_month(tmp_path) -> None:
    """I1-08: --purge-audit nunca borra el mes en curso."""
    database = Database(tmp_path / "purge.sqlite")
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    session = database.create_assistant_session("P", owner_key="analyst")
    database.create_assistant_run(session["id"], {"requestId": "cur", "cost": 0.11})
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    with database.lock:
        database.conn.execute(
            "INSERT INTO assistant_runs (session_id, request_id, model, mode, outcome, cost_usd, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session["id"], "old", "m", "quick", "success", 0.22, old),
        )
        database.conn.commit()
    assert database.conn.execute("SELECT COUNT(*) FROM assistant_runs").fetchone()[0] == 2
    removed = database.purge_assistant_runs(30)
    assert removed == 1
    remaining = [dict(r) for r in database.conn.execute("SELECT request_id, cost_usd FROM assistant_runs").fetchall()]
    assert {r["request_id"] for r in remaining} == {"cur"}
    assert database.assistant_month_spend("analyst", month) > 0


def test_budget_reaper_releases_stale_reservation(tmp_path) -> None:
    """I1-08/B2-06: reserved >1h se libera (reaper reutiliza recover_stale_jobs)."""
    database = Database(tmp_path / "reaper.sqlite")
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    assert database.reserve_assistant_budget("analyst", "req-old", 0.5, 1.0, month)["status"] == "reserved"
    stale = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    database.conn.execute(
        "UPDATE assistant_budget_reservations SET updated_at = ? WHERE request_id = ?",
        (stale, "req-old"),
    )
    database.conn.commit()
    assert database.assistant_budget_state("analyst", month, 1.0)["reservedUsd"] == 0.5
    assert database.release_stale_assistant_budgets() == 1
    state = database.assistant_budget_state("analyst", month, 1.0)
    assert state["reservedUsd"] == 0.0
    # El reaper integrado en recover_stale_jobs hace lo mismo.
    assert database.reserve_assistant_budget("analyst", "req-old2", 0.5, 1.0, month)["status"] == "reserved"
    database.conn.execute(
        "UPDATE assistant_budget_reservations SET updated_at = ? WHERE request_id = ?",
        (stale, "req-old2"),
    )
    database.conn.commit()
    database.recover_stale_jobs()
    assert database.assistant_budget_state("analyst", month, 1.0)["reservedUsd"] == 0.0


def test_review_overrun_is_recorded_before_raise(tmp_path, monkeypatch) -> None:
    """I1-09: exceso en reseñas -> error + coste visible en presupuesto."""
    database = Database(tmp_path / "review.sqlite")
    database.bootstrap_hotel_review_workspace()
    key = "atlas:servatur-monte-feliz"
    database.upsert_hotel_reviews(key, "google", None, [
        {"sourceReviewId": "g-1", "reviewOriginal": "Habitación amplia y limpia", "rating": 5,
         "sourceUrl": "https://www.google.com/maps/reviews/1"},
    ])
    monkeypatch.setattr(flask_app, "db", database)

    class FakeModels:
        ok = True

        def json(self):
            return {"data": [{"id": "test/model",
                              "pricing": {"prompt": "0.000001", "completion": "0.000002"}}]}

        def raise_for_status(self):
            return None

    class FakeCompletion:
        def json(self):
            return {"usage": {"cost": 0.20, "prompt_tokens": 10},
                    "choices": [{"message": {"content": "{}"}}]}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(flask_app.httpx, "get", lambda *a, **k: FakeModels())
    monkeypatch.setattr(flask_app.httpx, "post", lambda *a, **k: FakeCompletion())
    from dataclasses import replace as _replace
    _openrouter = _replace(
        flask_app.settings.openrouter,
        api_key="test-key",
        model="test/model",
        base_url="https://example.test",
    )
    _settings = _replace(flask_app.settings, openrouter=_openrouter)
    monkeypatch.setattr(flask_app, "settings", _settings)

    payload = {"hotelKey": key, "sources": ["google"], "budgetUsd": 0.05, "ownerKey": "review-tester"}
    try:
        flask_app._run_hotel_review_analysis_job(payload, lambda *a, **k: None)
    except RuntimeError as exc:
        assert "superó el límite" in str(exc)
    else:
        raise AssertionError("debió fallar por exceso de coste")

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    assert database.assistant_month_spend("review-tester", month) > 0
    row = database.conn.execute(
        "SELECT cost_usd FROM assistant_runs ORDER BY id DESC LIMIT 1").fetchone()
    assert row is not None and float(row["cost_usd"]) > 0
