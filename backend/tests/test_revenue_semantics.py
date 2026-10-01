from datetime import datetime, timezone

import pytest

from backend.app.database import Database
from backend.app.models import MarketHotelRow
from backend.app.revenue_semantics import freshness, product_signature


@pytest.fixture
def market(tmp_path):
    db = Database(tmp_path / "market.sqlite")
    target = db.upsert_target("Test market", "https://www.booking.com/searchresults.html")
    yield db, target
    db.conn.close()


def hotel(key, price=100, **changes):
    values = dict(hotelKey=key, hotelName=key, detailUrl="https://www.booking.com/hotel/es/test.html",
                  price=price * 7, pricePerNight=price, pricePerPersonPerNight=price / 2,
                  currency="EUR", checkIn="2026-10-01", checkOut="2026-10-08", nights=7,
                  pax=2, roomType="Double", board="Todo incluido", freeCancellation=False, position=1)
    return MarketHotelRow(**(values | changes))


def capture(market, rows, when, available=None):
    db, target = market
    photo = db.create_snapshot(target.id, target.url, 200, available or len(rows), len(rows), when)
    for row in rows:
        if not db.conn.execute("SELECT 1 FROM hotel_locations WHERE hotel_key = ?", (row.hotelKey,)).fetchone():
            db.upsert_location(row.hotelKey, row.detailUrl, None, None, None)
        db.insert_market_hotel(photo.id, row, "location_pending")
    db.conn.execute("UPDATE market_snapshots SET scraped_at = ? WHERE id = ?", (when, photo.id))
    db.conn.commit()
    return photo


def test_population_change_does_not_create_price_movement(market):
    db, target = market
    before = capture(market, [hotel(k) for k in "abc"], "2026-09-01T10:00:00+00:00")
    capture(market, [hotel(k) for k in "abc"] + [hotel("new", 1000)], "2026-09-02T10:00:00+00:00")
    result = db.dashboard_metrics(target.id)
    assert result["market"]["avgPricePerNight"] == 325
    assert result["movement"]["avgPricePerNightChangePct"] == 0
    assert result["movement"]["avgPriceChangePct"] == 0
    assert result["movement"]["avgPricePerPersonNightChangePct"] == 0
    assert result["comparison"]["previousSnapshotId"] == before.id
    assert result["comparison"]["matchedCoveragePct"] == 75
    assert not any(o["type"] == "raise_rate" for o in db.revenue_opportunities(target.id))


def test_dashboard_metrics_can_select_a_historical_snapshot(market):
    db, target = market
    old = capture(market, [hotel("a", 100)], "2026-09-01T10:00:00+00:00")
    latest = capture(market, [hotel("a", 140)], "2026-09-02T10:00:00+00:00")

    selected = db.dashboard_metrics(target.id, snapshot_id=old.id)
    current = db.dashboard_metrics(target.id)
    assert selected["latestSnapshot"]["id"] == old.id
    assert selected["market"]["avgPricePerNight"] == 100
    assert current["latestSnapshot"]["id"] == latest.id
    assert current["market"]["avgPricePerNight"] == 140
    assert db.dashboard_metrics(target.id + 1, snapshot_id=old.id)["latestSnapshot"] is None


@pytest.mark.parametrize("field,value", [("board", None), ("roomType", " "), ("pax", None),
                                          ("freeCancellation", None), ("currency", None),
                                          ("checkOut", "2026-10-09"), ("pricePerNight", 0)])
def test_missing_or_invalid_fields_do_not_prove_equivalence(market, field, value):
    db, target = market
    capture(market, [hotel("a", **{field: value})], "2026-09-01T10:00:00+00:00")
    capture(market, [hotel("a", **{field: value})], "2026-09-02T10:00:00+00:00")
    assert not db.dashboard_metrics(target.id)["movement"]["isComparable"]
    assert db.pickup_analysis(target.id) == []


def test_false_cancellation_is_known_and_can_match():
    assert product_signature(hotel("a")) is not None


def test_historical_comparison_never_looks_into_future(market):
    db, target = market
    old = capture(market, [hotel("a")], "2026-09-01T10:00:00+00:00")
    capture(market, [hotel("a", 120)], "2026-09-02T10:00:00+00:00")
    assert db.comparable_snapshot(target.id, db.snapshot_rows(old.id), old.id)["snapshot"] is None


def test_ambiguous_duplicate_product_is_not_arbitrarily_selected(market):
    db, target = market
    capture(market, [hotel("a"), hotel("a", 150)], "2026-09-01T10:00:00+00:00")
    capture(market, [hotel("a", 120)], "2026-09-02T10:00:00+00:00")
    assert not db.dashboard_metrics(target.id)["movement"]["isComparable"]


def test_stability_does_not_compare_different_stays(market):
    db, target = market
    capture(market, [hotel("a", 100)], "2026-09-01T10:00:00+00:00")
    capture(market, [hotel("a", 200, checkIn="2026-11-01", checkOut="2026-11-08")], "2026-09-02T10:00:00+00:00")
    assert db.competitive_stability(target.id) == []


def test_stability_reports_only_current_equivalent_product(market):
    db, target = market
    capture(market, [hotel("a", 100)], "2026-09-01T10:00:00+00:00")
    capture(market, [hotel("a", 900, board="Breakfast")], "2026-09-02T10:00:00+00:00")
    capture(market, [hotel("a", 100)], "2026-09-03T10:00:00+00:00")
    result = db.competitive_stability(target.id)[0]
    assert result["consistencyScore"] == 100
    assert result["observations"] == 2
    assert result["checkIn"] == "2026-10-01"


def test_low_capture_coverage_is_quality_not_demand(market):
    db, target = market
    capture(market, [hotel("a")], "2026-09-01T10:00:00+00:00", available=100)
    result = db.dashboard_metrics(target.id)
    signal = next(i for i in result["insights"] if i["id"] == "demand-surge")
    assert signal["type"] == "data_quality"
    assert "ocupación" in signal["message"]
    assert all(i["type"] != "demand_surge" for i in db.revenue_opportunities(target.id))


def test_map_defaults_to_same_latest_photo(market):
    db, target = market
    db.upsert_location("a", "https://www.booking.com/hotel/es/test.html", 28.0, -15.5, "Test")
    capture(market, [hotel("a", 100)], "2026-09-01T10:00:00+00:00")
    last = capture(market, [hotel("a", 200)], "2026-09-02T10:00:00+00:00")
    result = db.market_heatmap(target.id)
    assert result["points"][0]["avgPricePerNight"] == 200
    assert result["snapshotIds"] == [last.id]
    assert db.market_heatmap(target.id, 2)["scope"] == "historical_aggregate"


def test_rate_curve_keeps_currencies_separate_and_calendar_days(market):
    db, target = market
    capture(market, [hotel("a", 100), hotel("b", 200, currency="USD")], "2026-09-30T23:00:00+00:00")
    points = db.demand_curve(target.id)
    assert [(p["currency"], p["daysUntilCheckIn"], p["avgAdr"]) for p in points] == [("EUR", 1, 100), ("USD", 1, 200)]


def test_freshness_is_independent_of_comparability():
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    assert freshness("2026-09-01T00:00:00+00:00", now)["estado"] == "caducado"
    assert freshness("2026-09-06T00:00:00+00:00", now)["etiqueta"] == "Fecha no verificable"


def test_ambiguous_duplicate_is_excluded_from_rate_movement(market):
    db, target = market
    capture(market, [hotel('a'), hotel('a', 150)], '2026-09-01T10:00:00+00:00')
    capture(market, [hotel('a', 120)], '2026-09-02T10:00:00+00:00')
    assert db.pickup_analysis(target.id) == []


def test_rate_movement_preserves_product_and_capture_identity(market):
    db, target = market
    before = capture(market, [hotel('a')], '2026-09-01T10:00:00+00:00')
    after = capture(market, [hotel('a', 110)], '2026-09-02T10:00:00+00:00')
    change = db.pickup_analysis(target.id)[0]
    assert (change['previousSnapshotId'], change['snapshotId']) == (before.id, after.id)
    assert change['currency'] == 'EUR'
    assert change['checkOut'] == '2026-10-08'
    assert change['pickupPct'] == 10


def test_workspace_trend_uses_nightly_rate_and_rejects_mixed_currency(market):
    db, target = market
    capture(market, [hotel('a', 100)], '2026-09-01T10:00:00+00:00')
    capture(market, [hotel('a'), hotel('b', 200, currency='USD')], '2026-09-02T10:00:00+00:00')
    points = db._trend(target.id)
    assert points[0]['avgPrice'] == 700
    assert points[0]['avgPricePerNight'] == 100
    assert points[1]['avgPricePerNight'] is None


def test_ai_history_retains_evidence_dimensions(market):
    from backend.app.assistant import _tool_historial_precio_hotel
    db, target = market
    photo = capture(market, [hotel('example')], '2026-09-01T10:00:00+00:00')
    result = _tool_historial_precio_hotel(db, {'nombre': 'example'})
    assert result['targetId'] == target.id
    entry = result['capturas'][0]
    assert entry['snapshotId'] == photo.id
    assert (entry['moneda'], entry['adultos'], entry['regimen']) == ('EUR', 2, 'Todo incluido')


def test_ai_does_not_pick_first_ambiguous_hotel(market):
    from backend.app.assistant import _tool_historial_precio_hotel
    capture(market, [hotel('example one'), hotel('example two')], '2026-09-01T10:00:00+00:00')
    result = _tool_historial_precio_hotel(market[0], {'nombre': 'example'})
    assert result['requiereAclaracion']
    assert len(result['candidatos']) == 2
    assert 'capturas' not in result


def test_ai_history_is_compact_but_keeps_comparison_dimensions(market):
    from backend.app.assistant import _tool_historial_precio_hotel
    db, target = market
    capture(market, [hotel('example')], '2026-09-01T10:00:00+00:00')
    result = _tool_historial_precio_hotel(db, {'nombre': 'example'})
    entry = result['capturas'][0]
    assert set(entry) == {'snapshotId', 'fechaObservacion', 'entrada', 'salida', 'noches', 'adultos', 'habitacion', 'regimen', 'moneda', 'cancelacionGratis', 'tarifaNoche'}
    assert entry['snapshotId'] is not None and entry['moneda'] == 'EUR'


def test_tool_trace_records_names_without_exposing_arguments(market):
    from backend.app.assistant import _run_tool
    capture(market, [hotel('a')], '2026-09-01T10:00:00+00:00')
    telemetry = {}
    result = _run_tool(market[0], market[1].id, None, 'listar_competidores', {}, telemetry)
    assert result['total'] == 1
    assert telemetry['toolNames'] == ['listar_competidores']
    assert telemetry['toolEvidenceIds'][0].startswith('tool-listar_competidores-')
    assert result['_evidence']['evidenceId'] == telemetry['toolEvidenceIds'][0]
    assert result['_evidence']['tool'] == 'listar_competidores'
    assert result['_evidence']['queriedAt']
    assert result['_evidence']['sourceObservedAt'] is not None
    assert result['_evidence']['queriedAt'] != result['_evidence']['sourceObservedAt']
    assert 'arguments' not in telemetry
