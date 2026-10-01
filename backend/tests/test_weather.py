from datetime import datetime, timedelta, timezone

import pytest

from backend.app.weather import known_at_capture, make_weather_record
from backend.app.database import Database
from backend.app.models import MarketHotelRow
from backend.app.weather_market import cluster_market_rows


CAPTURE = "2026-09-07T08:00:00+00:00"


def test_forecast_retrieved_before_capture_is_known():
    record = make_weather_record(
        provider="open-meteo", dataset="daily", kind="forecast", location_key="gran-canaria-sur",
        valid_at="2026-09-10T00:00:00+00:00", retrieved_at="2026-09-07T07:55:00+00:00",
        capture_at=CAPTURE, values={"temperature_max": 27.0}, units={"temperature_max": "°C"},
    )
    assert record.known_at_capture is True
    assert record.retrospective is False
    assert known_at_capture([record]) == [record]


def test_forecast_retrieved_after_capture_is_not_known_then():
    record = make_weather_record(
        provider="open-meteo", dataset="daily", kind="forecast", location_key="gran-canaria-sur",
        valid_at="2026-09-10T00:00:00+00:00", retrieved_at="2026-09-07T08:01:00+00:00",
        capture_at=CAPTURE, values={"temperature_max": 27.0}, units={"temperature_max": "°C"},
    )
    assert record.known_at_capture is False
    assert record.retrospective is False
    assert known_at_capture([record]) == []


def test_observation_retrieved_later_is_retrospective():
    record = make_weather_record(
        provider="aemet", dataset="hourly-observation", kind="observed", location_key="station-1234",
        valid_at="2026-09-07T07:00:00+00:00", retrieved_at="2026-09-07T09:00:00+00:00",
        capture_at=CAPTURE, values={"temperature": 25.0}, units={"temperature": "°C"},
    )
    assert record.known_at_capture is False
    assert record.retrospective is True
    assert known_at_capture([record]) == []


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="zona horaria"):
        make_weather_record(
            provider="aemet", dataset="hourly", kind="observed", location_key="station-1234",
            valid_at=datetime(2026, 9, 7, 7, tzinfo=timezone.utc),
            retrieved_at="2026-09-07T07:30:00", capture_at=CAPTURE,
            values={}, units={},
        )


def test_weather_cache_persists_normalised_rows_only(tmp_path):
    db = Database(tmp_path / "weather.sqlite")
    record = make_weather_record(
        provider="open-meteo", dataset="forecast.daily", kind="forecast", location_key="sur",
        valid_at="2026-09-10T00:00:00+00:00", retrieved_at=CAPTURE, capture_at=CAPTURE,
        values={"temperature_2m_max": 27.0}, units={"temperature_2m_max": "°C"},
    )
    summary = db.persist_weather_records([record], latitude=27.75, longitude=-15.58, payload_hash="abc")
    saved = db.weather_snapshot(summary["snapshotId"])
    assert saved["provider"] == "open-meteo"
    assert saved["days"][0]["values"]["temperature_2m_max"] == 27.0
    assert saved["payloadHash"] == "abc"
    assert db.conn.execute("SELECT COUNT(*) FROM weather_snapshots").fetchone()[0] == 1
    assert db.conn.execute("SELECT COUNT(*) FROM weather_daily").fetchone()[0] == 1
    db.conn.close()


def test_weather_cache_reuses_fresh_market_query(tmp_path):
    db = Database(tmp_path / "weather-market.sqlite")
    captured_now = datetime.now(timezone.utc)
    record = make_weather_record(
        provider="open-meteo", dataset="forecast.daily", kind="forecast", location_key="cell:27.75:-15.58",
        valid_at="2026-09-10T00:00:00+00:00", local_date="2026-09-10",
        retrieved_at=captured_now, capture_at=captured_now,
        values={"temperature_2m_max": 27.0}, units={"temperature_2m_max": "°C"},
    )
    summary = db.persist_weather_records(
        [record], latitude=27.75, longitude=-15.58, payload_hash="abc", market_snapshot_id=42,
    )
    cached = db.cached_weather_snapshot(
        "cell:27.75:-15.58", market_snapshot_id=42, start_date="2026-09-10", end_date="2026-09-10",
        max_age_hours=24,
    )
    assert cached is not None
    assert cached["id"] == summary["snapshotId"]
    assert db.cached_weather_snapshot(
        "cell:27.75:-15.58", market_snapshot_id=99, start_date="2026-09-10", end_date="2026-09-10",
    ) is None
    db.conn.close()


def test_weather_association_ignores_enrichment_retrieved_after_photo(tmp_path):
    db = Database(tmp_path / "weather-as-of.sqlite")
    target = db.upsert_target("Gran Canaria", "https://example.test/gran-canaria")
    db.upsert_location("hotel-a", "https://example.test/a", 27.75, -15.58, "Gran Canaria")
    captured_at = datetime(2026, 8, 1, 8, tzinfo=timezone.utc)
    snapshot = db.create_snapshot(target.id, "https://example.test/market", 1, 1, 1, "hash-as-of")
    db.conn.execute("UPDATE market_snapshots SET scraped_at = ? WHERE id = ?", (captured_at.isoformat(), snapshot.id))
    db.insert_market_hotel(snapshot.id, MarketHotelRow(
        hotelKey="hotel-a", hotelName="Hotel A", detailUrl="https://example.test/a",
        position=1, price=100, pricePerNight=100, currency="EUR",
        checkIn="2026-09-10", checkOut="2026-09-11", nights=1,
    ), "location_pending")
    db.conn.commit()

    for retrieved_at, temperature in ((captured_at - timedelta(minutes=5), 20), (captured_at + timedelta(hours=1), 99)):
        record = make_weather_record(
            provider="open-meteo", dataset="forecast.daily", kind="forecast", location_key="cell:as-of",
            valid_at="2026-09-10T00:00:00+00:00", local_date="2026-09-10",
            retrieved_at=retrieved_at, capture_at=retrieved_at,
            values={"temperature_2m_max": temperature, "precipitation_sum": 0.0},
            units={"temperature_2m_max": "°C", "precipitation_sum": "mm"},
        )
        db.persist_weather_records([record], latitude=27.75, longitude=-15.58, market_snapshot_id=snapshot.id)

    weather_rows = db.conn.execute(
        "SELECT id FROM weather_snapshots WHERE market_snapshot_id = ? ORDER BY id", (snapshot.id,)
    ).fetchall()
    result = db.weather_price_association(target.id, limit_snapshots=2)
    assert len(weather_rows) == 2
    assert result["observations"][0]["temperatureMaxMeanC"] == 20
    assert result["observations"][0]["knownAtCaptureDays"] == result["observations"][0]["weatherDays"]
    db.conn.close()


def test_weather_association_does_not_mix_a_different_stay_window(tmp_path):
    db = Database(tmp_path / "weather-window.sqlite")
    target = db.upsert_target("Gran Canaria", "https://example.test/gran-canaria")
    db.upsert_location("hotel-a", "https://example.test/a", 27.75, -15.58, "Gran Canaria")
    captured_at = datetime(2026, 8, 1, 8, tzinfo=timezone.utc)
    snapshot = db.create_snapshot(target.id, "https://example.test/market", 1, 1, 1, "hash-window")
    db.conn.execute("UPDATE market_snapshots SET scraped_at = ? WHERE id = ?", (captured_at.isoformat(), snapshot.id))
    db.insert_market_hotel(snapshot.id, MarketHotelRow(
        hotelKey="hotel-a", hotelName="Hotel A", detailUrl="https://example.test/a",
        position=1, price=100, pricePerNight=100, currency="EUR",
        checkIn="2026-09-10", checkOut="2026-09-11", nights=1,
    ), "location_pending")
    db.conn.commit()
    record = make_weather_record(
        provider="open-meteo", dataset="forecast.daily", kind="forecast", location_key="cell:different-stay",
        valid_at="2026-11-10T00:00:00+00:00", local_date="2026-11-10",
        retrieved_at=captured_at - timedelta(minutes=5), capture_at=captured_at - timedelta(minutes=5),
        values={"temperature_2m_max": 20}, units={"temperature_2m_max": "°C"},
    )
    db.persist_weather_records([record], latitude=27.75, longitude=-15.58, market_snapshot_id=snapshot.id)
    result = db.weather_price_association(target.id, limit_snapshots=2)
    assert result["observations"] == []
    assert result["status"] == "insufficient_sample"
    db.conn.close()


def test_market_weather_groups_nearby_hotels_and_keeps_outliers_separate():
    rows = [
        MarketHotelRow(hotelKey="a", hotelName="A", detailUrl="https://booking.com/a", position=1, latitude=27.7501, longitude=-15.5801),
        MarketHotelRow(hotelKey="b", hotelName="B", detailUrl="https://booking.com/b", position=2, latitude=27.7504, longitude=-15.5804),
        MarketHotelRow(hotelKey="c", hotelName="C", detailUrl="https://booking.com/c", position=3, latitude=27.7801, longitude=-15.6101),
        MarketHotelRow(hotelKey="d", hotelName="D", detailUrl="https://booking.com/d", position=4),
    ]
    groups = cluster_market_rows(rows, precision=2)
    assert len(groups) == 2
    assert sorted(len(group["hotelKeys"]) for group in groups.values()) == [1, 2]


def test_weather_price_association_requires_as_of_capture_and_is_reproducible(tmp_path):
    db = Database(tmp_path / "weather-association.sqlite")
    target = db.upsert_target("Gran Canaria", "https://example.test/gran-canaria")
    db.upsert_location("hotel-a", "https://example.test/a", 27.75, -15.58, "Gran Canaria")
    base = datetime(2026, 8, 1, 8, tzinfo=timezone.utc)
    for index, (price, temperature) in enumerate(((100, 20), (110, 21), (120, 23), (130, 22))):
        observed_at = base + timedelta(days=index)
        snapshot = db.create_snapshot(
            target.id, "https://example.test/market", 1, 1, 1, f"hash-{index}",
        )
        db.conn.execute("UPDATE market_snapshots SET scraped_at = ? WHERE id = ?", (observed_at.isoformat(), snapshot.id))
        db.insert_market_hotel(
            snapshot.id,
            MarketHotelRow(
                hotelKey="hotel-a", hotelName="Hotel A", detailUrl="https://example.test/a",
                position=1, price=price, pricePerNight=price, currency="EUR",
                checkIn="2026-09-10", checkOut="2026-09-11", nights=1,
            ),
            "location_pending",
        )
        db.conn.commit()
        record = make_weather_record(
            provider="open-meteo", dataset="forecast.daily", kind="forecast", location_key=f"cell:{index}",
            valid_at="2026-09-10T00:00:00+00:00", local_date="2026-09-10",
            retrieved_at=observed_at - timedelta(hours=1), capture_at=observed_at,
            values={"temperature_2m_max": temperature, "precipitation_sum": 0.0},
            units={"temperature_2m_max": "°C", "precipitation_sum": "mm"},
        )
        db.persist_weather_records(
            [record], latitude=27.75, longitude=-15.58,
            market_snapshot_id=snapshot.id,
        )

    result = db.weather_price_association(target.id, limit_snapshots=8)
    assert result["status"] == "ready"
    assert result["samplePairs"] == 3
    assert result["temperatureAdrCorrelation"] is not None
    assert all(item["eligibleAtCapture"] for item in result["observations"])
    db.conn.close()
