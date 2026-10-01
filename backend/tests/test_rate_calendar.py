from datetime import date

import pytest

from backend.app import rate_calendar
from backend.app.database import Database
from backend.app.models import MarketHotelRow

URL = "https://www.booking.com/searchresults.html?dest_id=1&selected_currency=EUR"


@pytest.fixture()
def db(tmp_path):
    database = Database(tmp_path / "calendar.sqlite")
    yield database
    database.conn.close()


def _row(key, name, check_in, price_per_night, *, room="Habitación Doble Estándar", board="Todo incluido", units=None, sold_out=None, district="Maspalomas", rating=8.4, reviews=900):
    check_out = (date.fromisoformat(check_in).toordinal() + 7)
    return MarketHotelRow(
        hotelKey=key, hotelName=name, detailUrl=URL, position=1, roomType=room, board=board, rating=rating, reviewCount=reviews,
        price=None if price_per_night is None else price_per_night * 7, pricePerNight=price_per_night, nights=7, currency="EUR",
        checkIn=check_in, checkOut=date.fromordinal(check_out).isoformat(), unitsLeft=units, soldOut=sold_out, popularDistrict=district,
    )


def _photo(db, target_id, rows, *, available=None, status=None):
    profile = {"captureQuality": {"status": status}} if status else None
    snapshot = db.create_snapshot(target_id, URL, 200, len(rows) if available is None else available, len(rows), "hash", capture_profile=profile)
    for row in rows:
        db.upsert_location(row.hotelKey, URL, 27.76, -15.58, None)
        db.insert_market_hotel(snapshot.id, row, "ready")
    return snapshot


def test_empty_market_returns_the_horizon_without_any_price(db):
    target = db.upsert_target("Vacío", URL)
    result = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 14)
    assert result["dates"][0] == "2026-10-01" and len(result["dates"]) == 14
    assert result["hotels"] == []
    assert result["medians"] == [None] * 14
    assert result["coverage"]["capturedDates"] == 0
    assert result["coverage"]["dates"] == [None] * 14
    assert result["latestCheckIn"] is None


def test_single_captured_date_fills_only_that_column(db):
    target = db.upsert_target("Una fecha", URL)
    _photo(db, target.id, [
        _row("a", "Servatur Waikiki", "2026-10-06", 200.0, units=2),
        _row("b", "Don Gregory by Dunas - Adults Only", "2026-10-06", 300.0),
        _row("c", "Hotel Sahara Playa", "2026-10-06", 400.0, units=5),
    ])
    result = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 30)
    i = result["dates"].index("2026-10-06")
    assert result["coverage"]["capturedDates"] == 1
    assert [d for d in result["coverage"]["dates"] if d] == [result["coverage"]["dates"][i]]
    hotels = {h["key"]: h for h in result["hotels"]}
    # fuera de la fecha capturada no hay ni precio ni estado: nunca se rellena
    assert all(h["prices"][j] is None and h["status"][j] is None for h in hotels.values() for j in range(30) if j != i)
    assert hotels["a"]["prices"][i] == 200.0 and hotels["a"]["status"][i] == "low"  # unitsLeft ≤ 2
    assert hotels["c"]["status"][i] == "ok"  # quedan 5: no es cupo bajo
    assert result["medians"][i] == 300.0 and result["p25"][i] == 250.0 and result["p75"][i] == 350.0
    assert hotels["b"]["chain"] == "Dunas" and hotels["b"]["adultsOnly"] is True
    assert hotels["a"]["zone"] == "Maspalomas" and hotels["a"]["lat"] == pytest.approx(27.76)
    assert result["latestCheckIn"] == "2026-10-06"


def test_closed_only_when_the_capture_is_complete(db):
    target = db.upsert_target("Varias fechas", URL)
    _photo(db, target.id, [_row("a", "Hotel A", "2026-10-06", 200.0), _row("b", "Hotel B", "2026-10-06", 260.0)])
    # captura completa (todos los resultados recibidos) en la que «b» no aparece → cerrado
    _photo(db, target.id, [_row("a", "Hotel A", "2026-10-13", 210.0)], available=1)
    # captura parcial: la ausencia de «b» no prueba nada
    _photo(db, target.id, [_row("a", "Hotel A", "2026-10-20", 220.0)], available=9, status="partial")
    # «b» aparece agotado: cerrado aunque esté en resultados
    _photo(db, target.id, [_row("a", "Hotel A", "2026-10-27", 230.0), _row("b", "Hotel B", "2026-10-27", None, sold_out=True)])
    result = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 30)
    col = {d: result["dates"].index(d) for d in ("2026-10-06", "2026-10-13", "2026-10-20", "2026-10-27")}
    b = next(h for h in result["hotels"] if h["key"] == "b")
    assert b["status"][col["2026-10-06"]] == "ok"
    assert b["status"][col["2026-10-13"]] == "closed"
    assert b["status"][col["2026-10-20"]] == "unknown"
    assert b["status"][col["2026-10-27"]] == "closed" and b["prices"][col["2026-10-27"]] is None
    coverage = result["coverage"]["dates"]
    assert coverage[col["2026-10-13"]]["complete"] is True
    assert coverage[col["2026-10-20"]]["complete"] is False
    assert result["coverage"]["capturedDates"] == 4


def test_latest_photo_wins_for_a_repeated_check_in(db):
    target = db.upsert_target("Repetida", URL)
    _photo(db, target.id, [_row("a", "Hotel A", "2026-10-06", 200.0)])
    newer = _photo(db, target.id, [_row("a", "Hotel A", "2026-10-06", 240.0)])
    result = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 14)
    i = result["dates"].index("2026-10-06")
    assert result["hotels"][0]["prices"][i] == 240.0
    assert result["coverage"]["dates"][i]["snapshotId"] == newer.id


def test_dates_outside_the_horizon_are_ignored(db):
    target = db.upsert_target("Horizonte", URL)
    _photo(db, target.id, [_row("a", "Hotel A", "2026-09-29", 200.0)])  # antes del inicio
    _photo(db, target.id, [_row("a", "Hotel A", "2026-10-20", 210.0)])  # después de 14 días
    result = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 14)
    assert result["coverage"]["capturedDates"] == 0 and result["hotels"] == []


def test_room_family_and_board_filters_use_the_effective_rate(db):
    target = db.upsert_target("Filtros", URL)
    photo = _photo(db, target.id, [
        _row("a", "Hotel A", "2026-10-06", 200.0, room="Suite Junior con vistas"),
        _row("b", "Hotel B", "2026-10-06", 300.0, room="Habitación Doble"),
        _row("c", "Hotel C", "2026-10-06", 280.0, room="Bungalow Superior", board="Desayuno incluido (Bueno)"),
    ])
    result = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 14, family="Suite")
    i = result["dates"].index("2026-10-06")
    assert [h["key"] for h in result["hotels"]] == ["a"]  # sin tarifa que cumpla: sale del análisis
    assert result["medians"][i] == 200.0
    assert result["facets"]["roomFamilies"] == ["Doble", "Suite", "Bungalow / villa"]
    assert result["facets"]["boards"] == ["Desayuno", "Todo incluido"]
    board = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 14, board="Desayuno")
    assert [h["key"] for h in board["hotels"]] == ["c"]
    # con detalle de tarifas vinculado a la foto, se usa la tarifa mínima de la familia pedida
    db.conn.execute(
        "INSERT INTO hotel_rate_details (target_id, hotel_key, room_type, price_final, board, units_left, check_in, check_out, captured_at, snapshot_id)"
        " VALUES (?, 'b', 'Suite Deluxe', 2800, 'Todo incluido', 1, '2026-10-06', '2026-10-13', '2026-09-28T10:00:00', ?)",
        (target.id, photo.id),
    )
    db.conn.commit()
    detailed = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 14, family="Suite")
    b = next(h for h in detailed["hotels"] if h["key"] == "b")
    assert b["prices"][i] == 400.0 and b["status"][i] == "low"
    assert detailed["coverage"]["dates"][i]["detail"] is True


def test_extractions_expose_median_band_and_hotel_prices_per_photo(db):
    target = db.upsert_target("Evolución", URL)
    first = _photo(db, target.id, [_row("a", "Hotel A", "2026-10-06", 200.0), _row("b", "Hotel B", "2026-10-06", 300.0)])
    second = _photo(db, target.id, [_row("a", "Hotel A", "2026-10-13", 220.0), _row("b", "Hotel B", "2026-10-13", 330.0)])
    result = rate_calendar.build_rate_calendar(db, target.id, date(2026, 10, 1), 30)
    assert [e["snapshotId"] for e in result["extractions"]] == [first.id, second.id]
    assert result["extractions"][1]["median"] == 275.0
    assert result["extractions"][1]["prices"] == {"a": 220.0, "b": 330.0}


@pytest.mark.parametrize(
    ("name", "family"),
    [("Suite Junior", "Suite"), ("Habitación Familiar (2 adultos + 2 niños)", "Familiar"), ("Bungalow con jardín", "Bungalow / villa"),
     ("Villa Premium", "Bungalow / villa"), ("Apartamento de 1 dormitorio", "Apartamento"), ("Estudio", "Apartamento"),
     ("Habitación Doble Estándar", "Doble"), ("Twin Room", "Doble"), ("Habitación Individual", "Otra"), (None, "Otra")],
)
def test_room_family_is_deduced_from_the_name_without_guessing(name, family):
    assert rate_calendar.room_family(name) == family


def test_endpoint_validates_parameters_and_serves_the_calendar(tmp_path, monkeypatch):
    from backend.app import flask_app

    database = Database(tmp_path / "endpoint.sqlite")
    target = database.upsert_target("Endpoint", URL)
    _photo(database, target.id, [_row("a", "Hotel A", "2026-10-06", 200.0)])
    monkeypatch.setattr(flask_app, "db", database)
    client = flask_app.app.test_client()
    try:
        response = client.get(f"/api/hotels/rate-calendar?targetId={target.id}&from=2026-10-01&days=14")
        assert response.status_code == 200
        body = response.get_json()
        assert body["days"] == 14 and body["hotels"][0]["key"] == "a"
        assert client.get(f"/api/hotels/rate-calendar?targetId={target.id}&from=mañana").status_code == 400
        assert client.get(f"/api/hotels/rate-calendar?targetId={target.id}&roomFamily=Ático").status_code == 400
        assert client.get(f"/api/hotels/rate-calendar?targetId={target.id}&days=500").status_code == 400
        assert client.get("/api/hotels/rate-calendar").status_code == 400
    finally:
        database.conn.close()
