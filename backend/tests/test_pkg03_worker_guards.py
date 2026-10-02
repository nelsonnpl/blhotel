"""PKG-03: worker con guardas + idempotencia por owner + settled + tools con mercado."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from backend.app import flask_app
from backend.app.assistant import _run_tool, _tool_buscar_hotel
from backend.app.database import Database
from backend.app.models import MarketHotelRow


def _hotel_row(key: str, name: str | None = None) -> MarketHotelRow:
    return MarketHotelRow(
        hotelKey=key,
        hotelName=name or key,
        detailUrl="https://booking.com/hotel/es/test.html",
        price=700,
        pricePerNight=100,
        currency="EUR",
        checkIn="2026-10-06",
        checkOut="2026-10-13",
        nights=7,
        pax=2,
        position=1,
    )


def _capture(db: Database, target_id: int, url: str, rows: list[MarketHotelRow]):
    for row in rows:
        if not db.conn.execute(
            "SELECT 1 FROM hotel_locations WHERE hotel_key = ?", (row.hotelKey,)
        ).fetchone():
            db.upsert_location(row.hotelKey, row.detailUrl, None, None, None)
    snap = db.create_snapshot(target_id, url, 200, len(rows), len(rows), "2026-09-01T10:00:00+00:00")
    for row in rows:
        db.insert_market_hotel(snap.id, row, "location_pending")
    db.conn.execute("UPDATE market_snapshots SET scraped_at = ? WHERE id = ?", ("2026-09-01T10:00:00+00:00", snap.id))
    db.conn.commit()
    return snap


def test_worker_rejects_target_without_grant(tmp_path, monkeypatch) -> None:
    isolated = Database(tmp_path / "pkg03-worker.sqlite")
    try:
        target = isolated.upsert_target("Mercado PKG-03", "https://booking.com/searchresults.html?pkg03=1")
        isolated.ensure_identity("owner-a-pkg03", "A", "analyst")
        isolated.ensure_identity("owner-b-pkg03", "B", "analyst")
        isolated.grant_market_access("owner-a-pkg03", target.id, "viewer")
        monkeypatch.setattr(flask_app, "db", isolated)
        flask_app._assistant_rate_windows.clear()

        payload = {
            "ownerKey": "owner-b-pkg03",
            "targetId": target.id,
            "sessionId": None,
            "message": "Resume",
            "mode": "quick",
            "history": [],
        }
        try:
            flask_app._run_assistant_analysis_job(payload, lambda *_: None)
        except Exception as exc:  # noqa: BLE001 - el worker envuelve en AssistantError
            assert "mercado" in str(exc).lower() or "acceso" in str(exc).lower()
        else:
            raise AssertionError("El worker debió rechazar el target sin concesión")
    finally:
        isolated.conn.close()
        flask_app._assistant_rate_windows.clear()


def test_worker_respects_rate_limit(tmp_path, monkeypatch) -> None:
    isolated = Database(tmp_path / "pkg03-ratelimit.sqlite")
    try:
        runtime = replace(flask_app.settings, copilot_requests_per_minute=1)
        monkeypatch.setattr(flask_app, "settings", runtime)
        monkeypatch.setattr(flask_app, "db", isolated)
        flask_app._assistant_rate_windows.clear()
        # Llenar la ventana del worker para este owner.
        assert flask_app._consume_assistant_rate_slot("job:owner-rl") is None
        payload = {"ownerKey": "owner-rl", "message": "hola", "mode": "quick", "history": []}
        try:
            flask_app._run_assistant_analysis_job(payload, lambda *_: None)
        except Exception as exc:  # noqa: BLE001
            assert "demasiadas" in str(exc).lower() or "copilot" in str(exc).lower()
        else:
            raise AssertionError("El worker debió respetar el rate-limit")
    finally:
        isolated.conn.close()
        flask_app._assistant_rate_windows.clear()


def test_idempotency_is_scoped_by_owner(tmp_path) -> None:
    database = Database(tmp_path / "pkg03-idem.sqlite")
    try:
        first = database.enqueue_job(
            "job-a", "assistant_analysis", {"ownerKey": "owner-a", "sessionId": 1},
            idempotency_key="request-X",
        )
        second = database.enqueue_job(
            "job-b", "assistant_analysis", {"ownerKey": "owner-b", "sessionId": 2},
            idempotency_key="request-X",
        )
        assert first["id"] != second["id"]
        assert first["idempotency_key"] != second["idempotency_key"]
        got_a = database.get_job_by_idempotency("assistant_analysis", "request-X", "owner-a")
        got_b = database.get_job_by_idempotency("assistant_analysis", "request-X", "owner-b")
        assert got_a is not None and got_b is not None
        assert got_a["id"] == first["id"]
        assert got_b["id"] == second["id"]
        # Sin owner (legado) sigue funcionando para claves sin prefijo.
        legacy = Database(tmp_path / "pkg03-legacy.sqlite")
        try:
            one = legacy.enqueue_job("job-1", "assistant_analysis", {"sessionId": 4}, idempotency_key="request-1")
            assert legacy.get_job_by_idempotency("assistant_analysis", "request-1")["id"] == one["id"]
        finally:
            legacy.conn.close()
    finally:
        database.conn.close()


def test_settled_request_creates_new_reservation_and_enforces_ceiling(tmp_path) -> None:
    database = Database(tmp_path / "pkg03-settled.sqlite")
    try:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        first = database.reserve_assistant_budget("analyst", "request-1", 0.60, 1.00, month)
        assert first["status"] == "reserved"
        assert database.settle_assistant_budget("request-1", 0.42)["status"] == "settled"
        session = database.create_assistant_session("Budget", owner_key="analyst")
        database.create_assistant_run(session["id"], {"requestId": "request-1", "costUsd": 0.42})
        # Techo agotado: el reenvío del requestId liquidado no reutiliza el
        # settled como autorización → None (el endpoint responde 402).
        assert database.reserve_assistant_budget("analyst", "request-1", 0.60, 1.00, month) is None
        # Con techo amplio sí crea una reserva nueva, nunca devuelve settled.
        fresh = database.reserve_assistant_budget("analyst", "request-1", 0.10, 10.00, month)
        assert fresh["status"] == "reserved"
    finally:
        database.conn.close()


def test_tools_without_market_require_selection(tmp_path) -> None:
    database = Database(tmp_path / "pkg03-tools.sqlite")
    try:
        target_a = database.upsert_target("Zona A", "https://booking.com/searchresults.html?pkg03=a")
        target_b = database.upsert_target("Zona B", "https://booking.com/searchresults.html?pkg03=b")
        _capture(database, target_a.id, target_a.url, [_hotel_row("hotel-zona-a", "Hotel Zona A")])
        _capture(database, target_b.id, target_b.url, [_hotel_row("hotel-zona-b", "Hotel Zona B")])

        direct = _tool_buscar_hotel(database, {"nombre": "Hotel"})
        assert "error" in direct and "mercado" in direct["error"].lower()

        via_run = _run_tool(database, None, None, "buscar_hotel", {"nombre": "Hotel"}, {})
        assert "error" in via_run and "selecciona" in via_run["error"].lower() and "mercado" in via_run["error"].lower()

        via_hist = _run_tool(database, None, None, "historial_precio_hotel", {"nombre": "Hotel"}, {})
        assert "error" in via_hist and "mercado" in via_hist["error"].lower()

        via_list = _run_tool(database, None, None, "listar_competidores", {}, {})
        assert "error" in via_list and "mercado" in via_list["error"].lower()

        # Con mercado sí resuelve dentro de ese mercado.
        ok_tool = _tool_buscar_hotel(database, {"nombre": "Zona A", "targetId": target_a.id})
        assert ok_tool.get("encontrados") == 1
    finally:
        database.conn.close()
