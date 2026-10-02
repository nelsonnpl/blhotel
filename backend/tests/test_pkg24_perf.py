"""PKG-24 (B1-07/08/09/10): sin N+1, history paginado, rate con caché, índices."""
from __future__ import annotations

import time

from backend.app import flask_app, rate_calendar
from backend.app.database import Database
from backend.app.models import MarketHotelRow


def _hotel(key: str, price: float = 100, **changes) -> MarketHotelRow:
    values = dict(
        hotelKey=key, hotelName=key, detailUrl="https://www.booking.com/hotel/es/test.html",
        price=price * 7, pricePerNight=price, pricePerPersonPerNight=price / 2,
        currency="EUR", checkIn="2026-10-01", checkOut="2026-10-08", nights=7,
        pax=2, roomType="Double", board="Todo incluido", freeCancellation=False, position=1,
    )
    return MarketHotelRow(**(values | changes))


def _capture(db: Database, target_id: int, url: str, rows: list[MarketHotelRow], when: str, group: str | None = None):
    photo = db.create_snapshot(target_id, url, 200, len(rows), len(rows), when, capture_group_id=group)
    for row in rows:
        if not db.conn.execute("SELECT 1 FROM hotel_locations WHERE hotel_key = ?", (row.hotelKey,)).fetchone():
            db.upsert_location(row.hotelKey, row.detailUrl, None, None, None)
        db.insert_market_hotel(photo.id, row, "location_pending")
    db.conn.execute("UPDATE market_snapshots SET scraped_at = ? WHERE id = ?", (when, photo.id))
    db.conn.commit()
    return photo


class _Counter:
    """Cuenta sentencias SQL vía trace (sqlite3.Connection.execute es read-only)."""

    def __init__(self, db: Database):
        self.db = db
        self.n = 0

    def __enter__(self):
        def _cb(_sql: str) -> None:
            self.n += 1

        self.db.conn.set_trace_callback(_cb)
        return self

    def __exit__(self, *args):
        self.db.conn.set_trace_callback(None)


def _review_db(tmp_path) -> tuple[Database, str]:
    db = Database(tmp_path / "pkg24-profile.sqlite")
    db.bootstrap_hotel_review_workspace()
    key = "atlas:servatur-monte-feliz"
    db.upsert_hotel_reviews(key, "google", None, [
        {"sourceReviewId": f"g-{i}", "reviewOriginal": f"Great {i}", "rating": 4 + (i % 2),
         "publishedAt": f"2026-0{(i % 9) + 1}-15T10:00:00+00:00", "datePrecision": "exact",
         "sourceUrl": "https://www.google.com/maps/reviews/1"}
        for i in range(6)
    ])
    db.upsert_hotel_reviews(key, "booking", None, [
        {"sourceReviewId": f"b-{i}", "reviewOriginal": f"Bien {i}", "rating": 8,
         "ratingScale": 10, "publishedAt": "2026-05-10T10:00:00+00:00",
         "datePrecision": "exact", "sourceUrl": "https://www.booking.com/hotel/es/x.html"}
        for i in range(4)
    ])
    for source in ("google", "booking"):
        run = db.create_hotel_review_run(key, source, status="completed", source_url="https://example.test")
        db.update_hotel_review_run(run, status="completed", rows_seen=10, coverage={"completado": True}, complete=True)
    db.conn.execute(
        "INSERT INTO hotel_attribute_observations(hotel_key,attribute,value_json,source,observed_at,selected)"
        " VALUES (?, 'google_aggregate', ?, 'google', '2026-09-01', 1)",
        (key, '{"rating": 4.5, "reviewCount": 120}'),
    )
    db.conn.execute(
        "INSERT INTO hotel_attribute_observations(hotel_key,attribute,value_json,source,observed_at,selected)"
        " VALUES (?, 'booking_aggregate', ?, 'booking_graphql', '2026-09-02', 1)",
        (key, '{"rating": 8.6, "reviewCount": 300}'),
    )
    db.conn.commit()
    return db, key


def test_profile_bulk_sin_n_mas_1(tmp_path) -> None:
    db, key = _review_db(tmp_path)
    try:
        with _Counter(db) as counter:
            profile = db.hotel_review_profile(key)
        assert profile is not None
        sources = {item["source"]: item for item in profile["sources"]}
        assert set(sources) >= {"google", "booking"}
        assert sources["google"]["ratingScale"] == 5
        assert sources["booking"]["ratingScale"] == 10
        assert sum(item["count"] for item in sources["google"]["ratingDistribution"]) == 6
        assert sources["google"]["datedTrend"]
        assert sources["google"]["latestRun"]["status"] == "completed"
        assert sources["google"]["publishedRating"] == 4.5
        assert sources["booking"]["publishedRating"] == 8.6
        first_n = counter.n
        # Añadir una fuente más no debe sumar 4 queries (bulk: coste fijo).
        db.upsert_hotel_reviews(key, "google", None, [
            {"sourceReviewId": "g-extra", "reviewOriginal": "Extra", "rating": 5,
             "sourceUrl": "https://www.google.com/maps/reviews/1"}
        ])
        with _Counter(db) as counter2:
            db.hotel_review_profile(key)
        assert counter2.n <= first_n + 1, f"N+1: {first_n} -> {counter2.n}"
        assert first_n <= 14, f"demasiadas queries fijas: {first_n}"
    finally:
        db.conn.close()


def test_capture_history_paginado_y_bulk(tmp_path) -> None:
    db = Database(tmp_path / "pkg24-captures.sqlite")
    try:
        target = db.upsert_target("PKG24", "https://www.booking.com/searchresults.html?pkg24=1")
        hotels = [f"hotel-{h}" for h in range(4)]
        for i, (group, when) in enumerate([
            ("grp-a", "2026-09-01T10:00:00+00:00"), ("grp-a", "2026-09-01T10:01:00+00:00"),
            ("grp-b", "2026-09-08T10:00:00+00:00"), ("grp-b", "2026-09-08T10:01:00+00:00"),
        ]):
            _capture(db, target.id, target.url, [_hotel(k, price=100 + i) for k in hotels], when, group=group)
        with _Counter(db) as counter:
            page = db.capture_history_page(target.id, limit=1, offset=0)
        assert page["total"] == 2
        assert len(page["items"]) == 1
        assert page["items"][0]["kind"] == "capture_group"
        assert page["items"][0]["capturedRows"] >= page["items"][0]["comparableRows"] > 0
        assert page["items"][0]["checkIns"] == ["2026-10-01"]
        assert counter.n <= 5, f"N+1 en captures: {counter.n} queries"
        second = db.capture_history_page(target.id, limit=1, offset=1)
        assert second["items"][0]["id"] != page["items"][0]["id"]
        # Compat: la firma antigua sigue devolviendo lista.
        assert isinstance(db.capture_history(target.id, 10), list)
    finally:
        db.conn.close()


def test_hotels_history_paginado(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "pkg24-history.sqlite")
    try:
        target = db.upsert_target("PKG24-H", "https://www.booking.com/searchresults.html?pkg24h=1")
        for i in range(3):
            _capture(
                db, target.id, target.url,
                [_hotel(f"h-{h}", price=90 + i * 5 + h) for h in range(5)],
                f"2026-09-0{i + 1}T10:00:00+00:00",
            )
        page = db.hotel_row_history_page(target.id, limit_snapshots=3, limit=4, offset=0)
        assert page["total"] == 15
        assert len(page["rows"]) == 4
        assert page["limit"] == 4 and page["offset"] == 0
        nxt = db.hotel_row_history_page(target.id, limit_snapshots=3, limit=4, offset=4)
        assert len(nxt["rows"]) == 4
        assert nxt["rows"][0]["id"] != page["rows"][0]["id"]
        # Endpoint expone pagination sin romper `rows`.
        monkeypatch.setattr(flask_app, "db", db)
        client = flask_app.app.test_client()
        response = client.get(f"/api/hotels/history?targetId={target.id}&limitSnapshots=3&limit=4&offset=4")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body["rows"]) == 4
        assert body["pagination"]["total"] == 15
        captures = client.get(f"/api/captures/history?targetId={target.id}&limit=1&offset=0")
        assert captures.status_code == 200
        assert "pagination" in captures.get_json()
    finally:
        db.conn.close()


def test_rate_calendar_cache_y_etag(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "pkg24-rate.sqlite")
    try:
        target = db.upsert_target("PKG24-R", "https://www.booking.com/searchresults.html?pkg24r=1")
        _capture(db, target.id, target.url, [_hotel("r-a", 100), _hotel("r-b", 200)], "2026-10-01T10:00:00+00:00")
        monkeypatch.setattr(flask_app, "db", db)
        flask_app.clear_cache()
        client = flask_app.app.test_client()
        first = client.get(f"/api/hotels/rate-calendar?targetId={target.id}&days=14&from=2026-10-01")
        assert first.status_code == 200
        assert first.headers.get("ETag")
        assert "max-age=30" in (first.headers.get("Cache-Control") or "")
        assert ("rate-calendar", target.id, "2026-10-01", 14, "all", "all") in flask_app._CACHE
        second = client.get(
            f"/api/hotels/rate-calendar?targetId={target.id}&days=14&from=2026-10-01",
            headers={"If-None-Match": first.headers["ETag"]},
        )
        assert second.status_code == 304
    finally:
        db.conn.close()
        flask_app.clear_cache()


def test_indices_pkg24_existen(tmp_path) -> None:
    db = Database(tmp_path / "pkg24-idx.sqlite")
    try:
        names = {row["name"] for row in db.conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()}
        for expected in (
            "idx_hotel_rate_details_snapshot",
            "idx_market_snapshot_hotels_checkin",
            "idx_market_snapshot_hotels_hotelkey",
            "idx_hotel_reviews_profile",
            "idx_market_snapshots_comparable",
        ):
            assert expected in names, f"falta índice {expected}"
    finally:
        db.conn.close()


def test_rate_calendar_p95_objetivo_en_copia_aislada(tmp_path) -> None:
    """10x datos en copia aislada: p95 ≤150 ms (objetivo)."""
    db = Database(tmp_path / "pkg24-p95.sqlite")
    try:
        target = db.upsert_target("PKG24-P95", "https://www.booking.com/searchresults.html?pkg24p95=1")
        hotels = [f"p95-{h:03d}" for h in range(40)]
        for i in range(30):
            when = f"2026-08-{(i % 28) + 1:02d}T10:00:00+00:00"
            _capture(db, target.id, target.url, [_hotel(k, price=100 + (i % 7)) for k in hotels], when)
        start = rate_calendar.parse_start("2026-10-01")
        latencies: list[float] = []
        for _ in range(11):
            lap = time.perf_counter()
            rate_calendar.build_rate_calendar(db, target.id, start, 30)
            latencies.append((time.perf_counter() - lap) * 1000)
        latencies.sort()
        p95 = latencies[int(0.95 * (len(latencies) - 1))]
        assert p95 <= 150, f"p95 {p95:.1f} ms supera objetivo 150 ms"
    finally:
        db.conn.close()
