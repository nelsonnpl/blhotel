"""I1-19 (con B1): MoA con progreso consultable + comparable sin N+1."""
from __future__ import annotations

import time

from backend.app import copilot_moa, flask_app
from backend.app.assistant import AssistantError
from backend.app.config import OpenRouterSettings
from backend.app.database import COMPARABLE_MAX_SNAPSHOTS, Database
from backend.app.models import MarketHotelRow


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(api_key="test", model="legacy", base_url="https://example.test")


def _context() -> dict:
    return {
        "zonaActiva": {"id": 2, "name": "Gran Canaria"},
        "calidadAnalisis": {"estado": "vigente", "comparabilidadPct": 100},
        "evidencia": {"records": [{"metric": "adr", "quality": "verified"}]},
    }


def test_moa_publishes_progress_phases_without_extra_cost(monkeypatch) -> None:
    def fake_ask(settings, message, context, **kwargs):
        kwargs["telemetry"].update({"usage": {"total_tokens": 5}, "latencyMs": 2, "attempts": 1})
        return "síntesis final" if settings.model == settings.synthesis_model else f"informe {settings.model}"

    monkeypatch.setattr(copilot_moa, "ask_openrouter", fake_ask)
    events: list[tuple[int, str]] = []
    telemetry: dict = {}
    result = copilot_moa.run_moa(
        _settings(),
        "¿Puedo subir el precio?",
        _context(),
        experts=["hotel_revenue", "market_checker", "data_quality"],
        telemetry=telemetry,
        on_progress=lambda pct, msg: events.append((pct, msg)),
    )
    assert result == "síntesis final"
    assert len(events) >= 4  # lanzamiento + 2 expertos + síntesis
    pcts = [pct for pct, _ in events]
    assert pcts == sorted(pcts) and pcts[0] >= 0 and pcts[-1] <= 100
    assert any("experto" in msg.lower() or "moa" in msg.lower() for _, msg in events)
    # Sin on_progress sigue funcionando (compatibilidad con chat directo).
    telemetry2: dict = {}
    assert copilot_moa.run_moa(
        _settings(), "¿Puedo subir el precio?", _context(),
        experts=["hotel_revenue", "data_quality"], telemetry=telemetry2,
    )


def test_moa_progress_survives_failed_expert(monkeypatch) -> None:
    def fake_ask(settings, message, context, **kwargs):
        if settings.model == "google/gemini-3.8-flash":
            raise AssistantError("critic no disponible")
        return "respuesta sintetizada" if settings.model == "deepseek/deepseek-v4-pro-0813" else "informe revenue"

    monkeypatch.setattr(copilot_moa, "ask_openrouter", fake_ask)
    events: list[tuple[int, str]] = []
    telemetry: dict = {}
    result = copilot_moa.run_moa(
        _settings(), "¿Puedo subir el precio?", _context(),
        experts=["hotel_revenue", "market_checker", "data_quality"],
        telemetry=telemetry,
        on_progress=lambda pct, msg: events.append((pct, msg)),
    )
    assert result == "respuesta sintetizada"
    assert events and events[-1][0] == 95


def _hotel(key: str, price: float = 100, **changes) -> MarketHotelRow:
    values = dict(
        hotelKey=key, hotelName=key, detailUrl="https://www.booking.com/hotel/es/test.html",
        price=price * 7, pricePerNight=price, pricePerPersonPerNight=price / 2,
        currency="EUR", checkIn="2026-10-01", checkOut="2026-10-08", nights=7,
        pax=2, roomType="Double", board="Todo incluido", freeCancellation=False, position=1,
    )
    return MarketHotelRow(**(values | changes))


def _capture(db: Database, target_id: int, url: str, rows: list[MarketHotelRow], when: str):
    photo = db.create_snapshot(target_id, url, 200, len(rows), len(rows), when)
    for row in rows:
        if not db.conn.execute("SELECT 1 FROM hotel_locations WHERE hotel_key = ?", (row.hotelKey,)).fetchone():
            db.upsert_location(row.hotelKey, row.detailUrl, None, None, None)
        db.insert_market_hotel(photo.id, row, "location_pending")
    db.conn.execute("UPDATE market_snapshots SET scraped_at = ? WHERE id = ?", (when, photo.id))
    db.conn.commit()
    return photo


def test_comparable_respects_cap_and_index(tmp_path) -> None:
    db = Database(tmp_path / "i119-cap.sqlite")
    try:
        assert COMPARABLE_MAX_SNAPSHOTS == 120
        idx = {row["name"] for row in db.conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()}
        assert "idx_market_snapshots_comparable" in idx
        assert "idx_market_snapshot_hotels_snapshot" in idx
    finally:
        db.conn.close()


def test_comparable_120_photos_single_bulk_plus_winner(tmp_path) -> None:
    db = Database(tmp_path / "i119-120.sqlite")
    try:
        target = db.upsert_target("I1-19", "https://www.booking.com/searchresults.html?i119=1")
        hotels = [f"hotel-{h:03d}" for h in range(20)]
        for i in range(120):
            when = f"2026-{(1 + (i // 28)):02d}-{((i % 28) + 1):02d}T10:00:00+00:00"
            _capture(db, target.id, target.url, [_hotel(k, price=100 + (i % 5)) for k in hotels], when)
        latest = db.latest_snapshot(target.id)
        assert latest is not None
        rows = db.snapshot_rows(latest.id)
        # Caso peor: producto que no existe -> barrido completo de 120.
        nomatch = [_hotel(k, board="Solo desayuno") for k in hotels]
        calls = {"n": 0}
        orig = db.snapshot_rows
        def counting(snapshot_id: int):
            calls["n"] += 1
            return orig(snapshot_id)
        db.snapshot_rows = counting  # type: ignore[method-assign]
        try:
            t0 = time.perf_counter()
            result = db.comparable_snapshot(target.id, nomatch, latest.id)
            dt_ms = (time.perf_counter() - t0) * 1000
        finally:
            db.snapshot_rows = orig  # type: ignore[method-assign]
        assert result["snapshot"] is None
        # Sin N+1: vía rápida (3) + 1 bulk, cero barrido de 120. snapshot_rows
        # solo se usa en vía rápida y ganadora: acotado, no lineal en fotos.
        assert calls["n"] <= 3, f"N+1: {calls['n']} snapshot_rows en barrido completo"
        assert dt_ms < 200, f"comparable 120 fotos tardó {dt_ms:.1f} ms"

        # Caso con ganador: exactamente 1 lectura completa (la ganadora).
        calls["n"] = 0
        db.snapshot_rows = counting  # type: ignore[method-assign]
        try:
            hit = db.comparable_snapshot(target.id, rows, latest.id)
        finally:
            db.snapshot_rows = orig  # type: ignore[method-assign]
        assert hit["snapshot"] is not None
        assert len(hit["matchedCurrentRows"]) == 20
        assert hit["coveragePct"] == 100.0
        assert calls["n"] == 1, f"ganadora debe costar 1 snapshot_rows, fueron {calls['n']}"
    finally:
        db.conn.close()


def test_comparable_winner_matches_legacy_semantics(tmp_path) -> None:
    db = Database(tmp_path / "i119-sem.sqlite")
    try:
        target = db.upsert_target("I1-19-sem", "https://www.booking.com/searchresults.html?i119=sem")
        old = _capture(db, target.id, target.url, [_hotel("a", 100)], "2026-09-01T10:00:00+00:00")
        new = _capture(db, target.id, target.url, [_hotel("a", 120)], "2026-09-02T10:00:00+00:00")
        rows = db.snapshot_rows(new.id)
        result = db.comparable_snapshot(target.id, rows, new.id)
        assert result["snapshot"] is not None and result["snapshot"].id == old.id
        assert result["matchedPreviousRows"][0].pricePerNight == 100
        assert result["coveragePct"] == 100.0
    finally:
        db.conn.close()


def test_assistant_job_publishes_moa_progress_to_pollable_job(tmp_path, monkeypatch) -> None:
    """El job async no queda mudo: run_moa -> progress -> GET /jobs/<id>."""
    isolated = Database(tmp_path / "i119-job.sqlite")
    try:
        target = isolated.upsert_target("I1-19-job", "https://www.booking.com/searchresults.html?i119=job")
        isolated.ensure_identity("owner-i119", "O", "analyst")
        isolated.grant_market_access("owner-i119", target.id, "viewer")
        session_data = isolated.create_assistant_session("S", target_id=target.id, owner_key="owner-i119")
        monkeypatch.setattr(flask_app, "db", isolated)
        flask_app._assistant_rate_windows.clear()

        seen: list[tuple[int, str]] = []

        def fake_chat():
            from flask import g as _g
            moa_progress = getattr(_g, "assistant_moa_progress", None)
            assert callable(moa_progress), "el job debe exponer progreso MoA vía g"
            # Simula el panel real: run_moa emite fases al job.
            telemetry: dict = {}
            copilot_moa.run_moa(
                _settings(), "¿Subo precio?", _context(),
                experts=["hotel_revenue", "market_checker", "data_quality"],
                telemetry=telemetry,
                on_progress=moa_progress,
            )
            from flask import jsonify
            return jsonify({"reply": "ok", "session": session_data}), 200

        monkeypatch.setattr(flask_app, "assistant_chat", fake_chat)
        monkeypatch.setattr(
            copilot_moa, "ask_openrouter",
            lambda settings, *a, **k: (
                k["telemetry"].update({"usage": {"total_tokens": 1}, "latencyMs": 1, "attempts": 1}),
                "síntesis" if settings.model == settings.synthesis_model else "informe",
            )[1],
        )

        def capture_progress(pct: int, msg: str) -> None:
            seen.append((pct, msg))

        out = flask_app._run_assistant_analysis_job(
            {"ownerKey": "owner-i119", "sessionId": session_data["id"],
             "targetId": target.id, "message": "¿Subo precio?", "mode": "decision", "history": []},
            capture_progress,
        )
        assert out["reply"] == "ok"
        assert len(seen) >= 6  # 5 contexto + 15 fuentes + >=4 fases MoA
        pcts = [pct for pct, _ in seen]
        assert pcts == sorted(pcts)
        moa_pcts = [pct for pct, _ in seen if 20 <= pct <= 85]
        assert len(moa_pcts) >= 4, f"MoA debe publicar >=4 fases en 20-85, fueron {seen}"
        assert any("moa" in msg.lower() or "experto" in msg.lower() or "sintet" in msg.lower() for _, msg in seen)
    finally:
        isolated.conn.close()
        flask_app._assistant_rate_windows.clear()
