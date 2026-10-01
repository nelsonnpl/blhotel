from __future__ import annotations

import time

from backend.app import flask_app
from backend.app.air_data import build_air_payload
from backend.app.serpapi_flights import AirSearchRoute, normalize_serpapi_response
from backend.app.database import Database
from backend.app.models import HotelRateDetailRow, MarketHotelRow


def test_air_catalog_groups_routes_by_area_and_country() -> None:
    client = flask_app.app.test_client()
    response = client.get("/api/air-data/catalog")

    assert response.status_code == 200
    payload = response.get_json()
    gran_canaria = next(area for area in payload["areas"] if area["id"] == "gran-canaria")
    assert gran_canaria["destination"] == "LPA"
    assert any(group["country"] == "Espana" for group in gran_canaria["countries"])
    assert any(route["routeKey"] == "MAD_LPA" for route in payload["routes"])


def test_air_capture_requires_direct_choice() -> None:
    client = flask_app.app.test_client()
    response = client.post(
        "/api/air-data/capture",
        json={"areaIds": ["gran-canaria"], "outboundDate": "2026-08-24", "nights": 6},
    )

    assert response.status_code == 400
    assert "Payload invalido" in response.get_json()["error"]


def test_air_payload_keeps_price_history_once_per_route() -> None:
    payload = build_air_payload(
        [
            {
                "origin": "MAD",
                "destination": "LPA",
                "market": "Madrid",
                "price": 118,
                "lowest_price": 118,
                "typical_price_avg": 160,
                "stops": 0,
                "price_history": [[1, 140], [2, 118]],
            }
        ]
    )

    assert "price_history" not in payload["flights"][0]
    assert payload["routes"][0]["price_history"] == [[1, 140], [2, 118]]


def test_air_payload_maps_source_market_for_both_route_directions() -> None:
    payload = build_air_payload(
        [
            {"origin": "BHX", "destination": "LPA", "market": "Birmingham", "price": 80, "typical_price_avg": 100, "stops": 0},
            {"origin": "LPA", "destination": "DUB", "market": "Dublin", "price": 90, "typical_price_avg": 100, "stops": 0},
            {"origin": "BRU", "destination": "LPA", "market": "Bruselas", "price": 100, "typical_price_avg": 100, "stops": 0},
        ]
    )

    markets = {row["market"]: (row["market_country"], row["market_segment"]) for row in payload["flights"]}
    assert markets == {
        "Birmingham": ("Reino Unido", "Británico"),
        "Dublin": ("Irlanda", "Irlandés"),
        "Bruselas": ("Belgica", "Belga"),
    }


def test_air_route_signal_distinguishes_entry_price_from_average_market_price() -> None:
    payload = build_air_payload(
        [
            {"origin": "MAD", "destination": "LPA", "market": "Madrid", "price": 100, "lowest_price": 100, "typical_price_min": 150, "typical_price_max": 250, "typical_price_avg": 200, "stops": 0, "airlines": ["Iberia"]},
            {"origin": "MAD", "destination": "LPA", "market": "Madrid", "price": 240, "lowest_price": 240, "typical_price_min": 150, "typical_price_max": 250, "typical_price_avg": 200, "stops": 0, "airlines": ["Air Europa"]},
        ]
    )

    route = payload["routes"][0]
    assert route["entry_price_quality_label"] == "Barato"
    assert route["average_price_quality_label"] == "Normal"
    assert route["revenue_signal"] == "Mercado estable"
    assert payload["summary"]["avg_entry_gap_pct"] == -50.0
    assert payload["summary"]["avg_option_price"] == 170.0


def test_database_persists_air_route_history(tmp_path) -> None:
    db = Database(tmp_path / "air.sqlite")
    run = db.create_air_capture_run(
        {
            "areaIds": ["gran-canaria"],
            "countryIds": ["Espana"],
            "routeKeys": ["MAD_LPA"],
            "direct": True,
            "outboundDate": "2026-08-24",
            "returnDate": "2026-08-30",
        },
        requested_routes=1,
    )
    db.insert_air_route_snapshot(
        run["id"],
        {"areaId": "gran-canaria", "areaName": "Gran Canaria", "country": "Espana"},
        {
            "route_key": "MAD_LPA",
            "origin": "MAD",
            "destination": "LPA",
            "outbound_date": "2026-08-24",
            "return_date": "2026-08-30",
            "lowest_price": 118,
            "avg_price": 128,
            "num_options": 1,
            "num_direct_options": 1,
            "num_airlines": 1,
            "airlines_detected": ["Iberia Express"],
        },
        [
            {
                "search_id": "SERP-TEST",
                "itinerary_id": "MAD-LPA-1",
                "origin": "MAD",
                "destination": "LPA",
                "market": "Madrid",
                "outbound_date": "2026-08-24",
                "return_date": "2026-08-30",
                "price": 118,
                "lowest_price": 118,
                "stops": 0,
                "num_layovers": 0,
                "main_airline": "Iberia Express",
                "airlines": ["Iberia Express"],
                "flight_numbers": ["I2 3838"],
                "aircraft_models": ["Airbus A320"],
                "travel_classes": ["Economy"],
                "is_direct": True,
                "direct_label": "Directo",
                "flight_connection_type": "Directo",
            }
        ],
        direct=True,
        currency="EUR",
    )

    history = db.air_route_history(route_key="MAD_LPA", direct=True)
    latest_flights = db.latest_air_flights()

    assert len(history) == 1
    assert history[0]["lowestPrice"] == 118
    assert latest_flights[0]["route_key"] == "MAD_LPA"
    assert latest_flights[0]["is_direct"] is True
    assert "carbon_emissions_this_flight" not in latest_flights[0]
    assert db.conn.execute("SELECT COUNT(*) AS total FROM flight_price_observations").fetchone()["total"] == 1


def test_air_runs_endpoint_exposes_and_selects_historical_capture(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "air-runs.sqlite")
    older = db.create_air_run("serpapi", 1)
    db.insert_air_flight(older, {
        "origin": "BHX", "destination": "LPA", "market": "Birmingham", "price": 111,
        "lowest_price": 111, "typical_price_avg": 150, "stops": 0, "airlines": ["Ryanair"],
    })
    db.finish_air_run(older, routes_captured=1, flights_captured=1)
    newer = db.create_air_run("serpapi", 1)
    db.insert_air_flight(newer, {
        "origin": "DUB", "destination": "LPA", "market": "Dublin", "price": 222,
        "lowest_price": 222, "typical_price_avg": 200, "stops": 0, "airlines": ["Aer Lingus"],
    })
    db.finish_air_run(newer, routes_captured=1, flights_captured=1)
    monkeypatch.setattr(flask_app, "db", db)
    client = flask_app.app.test_client()

    history = client.get("/api/air-data/runs?limit=10")
    selected = client.get(f"/api/air-data/options?runId={older}&pageSize=25")
    consolidated = client.get("/api/air-data/options?scope=history&pageSize=25")

    assert history.status_code == 200
    assert history.get_json()["totalRuns"] == 2
    assert history.get_json()["totalFlights"] == 2
    assert selected.status_code == 200
    assert selected.get_json()["capture"]["id"] == older
    assert selected.get_json()["rows"][0]["price"] == 111
    assert consolidated.status_code == 200
    assert consolidated.get_json()["scope"] == "history"
    assert consolidated.get_json()["total"] == 2
    assert {row["capture_run_id"] for row in consolidated.get_json()["rows"]} == {older, newer}


def test_database_aggregates_legacy_air_route_history_by_capture(tmp_path) -> None:
    db = Database(tmp_path / "legacy-air-history.sqlite")
    older = db.create_air_run("serpapi", 1)
    newer = db.create_air_run("serpapi", 1)
    db.conn.execute("UPDATE air_runs SET captured_at = ? WHERE id = ?", ("2026-06-01T10:00:00+00:00", older))
    db.conn.execute("UPDATE air_runs SET captured_at = ? WHERE id = ?", ("2026-07-01T10:00:00+00:00", newer))
    db.insert_air_flight(older, {"origin": "MAD", "destination": "LPA", "price": 120, "lowest_price": 120, "stops": 0})
    db.insert_air_flight(older, {"origin": "MAD", "destination": "LPA", "price": 180, "lowest_price": 180, "stops": 1})
    db.insert_air_flight(newer, {"origin": "MAD", "destination": "LPA", "price": 150, "lowest_price": 150, "stops": 0})
    db.insert_air_flight(newer, {"origin": "MAD", "destination": "LPA", "price": 210, "lowest_price": 210, "stops": 1})
    db.conn.commit()

    history = db.air_route_history("MAD_LPA")
    direct_history = db.air_route_history("MAD_LPA", direct=True)

    assert [(item["lowestPrice"], item["avgPrice"], item["numOptions"], item["numDirectOptions"]) for item in history] == [
        (150.0, 180.0, 2, 1),
        (120.0, 150.0, 2, 1),
    ]
    assert [(item["lowestPrice"], item["numOptions"]) for item in direct_history] == [(150.0, 1), (120.0, 1)]
    assert db.latest_air_run() == {
        "id": newer,
        "capturedAt": "2026-07-01T10:00:00+00:00",
        "source": "serpapi",
        "routesRequested": 1,
        "routesCaptured": 0,
        "flightsCaptured": 0,
    }


def test_database_persists_hotel_price_observations(tmp_path) -> None:
    db = Database(tmp_path / "hotel-observations.sqlite")
    target = db.upsert_target("Gran Canaria", "https://www.booking.com/searchresults.es.html?checkin=2026-08-24&checkout=2026-08-30")
    snapshot = db.create_snapshot(target.id, target.url, requested_limit=1, available_results=1, captured_rows=1, raw_hash="hash")
    row = MarketHotelRow(
        hotelKey="/hotel/es/demo.html",
        hotelName="Hotel Demo",
        detailUrl="https://www.booking.com/hotel/es/demo.html",
        roomType="Doble",
        rating=8.8,
        price=1200,
        priceText="EUR 1.200",
        currency="EUR",
        pax=2,
        checkIn="2026-08-24",
        checkOut="2026-08-30",
        nights=6,
        pricePerNight=200,
        pricePerPersonPerNight=100,
        position=1,
    )

    db.upsert_location(row.hotelKey, row.detailUrl, None, None, None)
    db.insert_market_hotel(snapshot.id, row, "location_pending")
    history = db.hotel_price_history(row.hotelKey, target.id)

    assert len(history) == 1
    assert history[0]["pricePerNight"] == 200
    assert "location_pending" in history[0]["dataQualityFlags"]
    stored_snapshot = db.conn.execute("SELECT capture_run_id FROM market_snapshots WHERE id = ?", (snapshot.id,)).fetchone()
    assert stored_snapshot["capture_run_id"] is not None
    observation = db.conn.execute("SELECT capture_run_id FROM hotel_price_observations WHERE snapshot_id = ?", (snapshot.id,)).fetchone()
    assert observation["capture_run_id"] == stored_snapshot["capture_run_id"]


def test_latest_hotel_view_uses_last_successful_capture(tmp_path) -> None:
    db = Database(tmp_path / "latest-hotel-view.sqlite")
    target = db.upsert_target("Gran Canaria", "https://www.booking.com/searchresults.es.html?checkin=2026-08-24&checkout=2026-08-30")
    db.upsert_location("/hotel/es/demo.html", "https://www.booking.com/hotel/es/demo.html", None, None, None)

    first = db.create_snapshot(target.id, target.url, requested_limit=1, available_results=1, captured_rows=1, raw_hash="hash-1")
    db.insert_market_hotel(
        first.id,
        MarketHotelRow(
            hotelKey="/hotel/es/demo.html",
            hotelName="Hotel Demo",
            detailUrl="https://www.booking.com/hotel/es/demo.html",
            price=900,
            currency="EUR",
            checkIn="2026-08-24",
            checkOut="2026-08-30",
            nights=6,
            pricePerNight=150,
            position=1,
        ),
        "location_pending",
    )

    second = db.create_snapshot(target.id, target.url, requested_limit=1, available_results=1, captured_rows=1, raw_hash="hash-2")
    db.insert_market_hotel(
        second.id,
        MarketHotelRow(
            hotelKey="/hotel/es/demo.html",
            hotelName="Hotel Demo",
            detailUrl="https://www.booking.com/hotel/es/demo.html",
            price=1200,
            currency="EUR",
            checkIn="2026-08-24",
            checkOut="2026-08-30",
            nights=6,
            pricePerNight=200,
            position=1,
        ),
        "location_pending",
    )

    latest = db.latest_snapshot(target.id)
    latest_rows = db.conn.execute("SELECT snapshot_id, price_per_night FROM latest_hotel_price_observations").fetchall()

    assert latest is not None
    assert latest.id == second.id
    assert len(latest_rows) == 1
    assert latest_rows[0]["snapshot_id"] == second.id
    assert latest_rows[0]["price_per_night"] == 200


def test_latest_rate_detail_view_keeps_one_coherent_capture_per_hotel(tmp_path) -> None:
    db = Database(tmp_path / "latest-rate-detail-view.sqlite")
    target = db.upsert_target("Gran Canaria", "https://www.booking.com/searchresults.es.html")

    def detail(hotel_key: str, captured_at: str, price: float, room: str, program: str | None = None) -> HotelRateDetailRow:
        return HotelRateDetailRow(
            targetId=target.id,
            hotelKey=hotel_key,
            hotelName=hotel_key.title(),
            roomType=room,
            priceFinal=price,
            currency="EUR",
            board="Todo incluido",
            program=program,
            capturedAt=captured_at,
        )

    db.insert_rate_detail_rows(
        target.id,
        [
            detail("hotel-a", "2026-08-08T10:00:00", 100, "Habitación antigua"),
            detail("hotel-a", "2026-08-09T10:00:00", 120, "Habitación actual", "Genius"),
            detail("hotel-b", "2026-08-08T11:00:00", 90, "Suite actual"),
        ],
    )

    rows = db.latest_rate_details_for_target(target.id)

    assert [(row.hotelKey, row.roomType, row.priceFinal) for row in rows] == [
        ("hotel-a", "Habitación actual", 120),
        ("hotel-b", "Suite actual", 90),
    ]
    assert rows[0].program == "Genius"

    page = db.latest_rate_details_page_for_target(target.id, limit=1, offset=0)
    assert page["total"] == 2
    assert len(page["rows"]) == 1
    assert page["rows"][0].hotelKey == "hotel-a"


def test_air_capture_endpoint_uses_mocked_serpapi_and_stores_rows(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "flask-air.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    monkeypatch.setattr(flask_app, "serpapi_key", lambda: "test-key")

    def fake_fetch_google_flights(route, api_key: str, force_live: bool = False):
        return {
            "search_metadata": {"id": "SERP-MOCK", "created_at": "2026-06-07T10:00:00Z"},
            "price_insights": {"lowest_price": 118, "typical_price_range": [140, 240], "price_level": "low"},
            "best_flights": [
                {
                    "price": 118,
                    "total_duration": 170,
                    "flights": [
                        {
                            "airline": "Iberia Express",
                            "flight_number": "I2 3838",
                            "airplane": "Airbus A320",
                            "travel_class": "Economy",
                            "departure_airport": {"id": route.origin, "name": "Madrid-Barajas", "time": "2026-08-24 09:25"},
                            "arrival_airport": {"id": route.destination, "name": "Gran Canaria", "time": "2026-08-24 11:15"},
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr(flask_app, "fetch_google_flights", fake_fetch_google_flights)

    response = flask_app.app.test_client().post(
        "/api/air-data/capture",
        json={
            "areaIds": ["gran-canaria"],
            "countryIds": ["Espana"],
            "routeKeys": ["MAD_LPA"],
            "direct": True,
            "outboundDate": "2026-08-24",
            "nights": 6,
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["run"]["capturedFlights"] == 1
    assert payload["routeSnapshots"][0]["routeKey"] == "MAD_LPA"
    assert test_db.air_route_history(route_key="MAD_LPA", direct=True)[0]["lowestPrice"] == 118


def test_air_capture_round_trip_runs_two_one_way_legs(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "flask-air-round-trip.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    monkeypatch.setattr(flask_app, "serpapi_key", lambda: "test-key")
    calls = []

    def fake_fetch_google_flights(route, api_key: str, force_live: bool = False):
        calls.append(
            {
                "origin": route.origin,
                "destination": route.destination,
                "outbound_date": route.outbound_date,
                "return_date": route.return_date,
                "leg_direction": route.leg_direction,
                "trip_type": route.trip_type,
            }
        )
        return {
            "search_metadata": {"id": f"SERP-{route.leg_direction}", "created_at": "2026-06-07T10:00:00Z"},
            "price_insights": {"lowest_price": 59, "typical_price_range": [55, 130], "price_level": "typical"},
            "best_flights": [
                {
                    "price": 59 if route.leg_direction == "outbound" else 63,
                    "total_duration": 170,
                    "flights": [
                        {
                            "airline": "Iberia Express",
                            "flight_number": "I2 1631",
                            "airplane": "Airbus A320",
                            "travel_class": "Economy",
                            "departure_airport": {"id": route.origin, "name": route.origin, "time": f"{route.outbound_date} 22:55"},
                            "arrival_airport": {"id": route.destination, "name": route.destination, "time": f"{route.outbound_date} 00:45"},
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr(flask_app, "fetch_google_flights", fake_fetch_google_flights)

    response = flask_app.app.test_client().post(
        "/api/air-data/capture",
        json={
            "areaIds": ["gran-canaria"],
            "countryIds": ["Espana"],
            "routeKeys": ["MAD_LPA"],
            "direct": True,
            "tripType": "round_trip",
            "outboundDate": "2026-08-24",
            "returnDate": "2026-08-30",
            "nights": 6,
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert calls == [
        {"origin": "MAD", "destination": "LPA", "outbound_date": "2026-08-24", "return_date": None, "leg_direction": "outbound", "trip_type": "round_trip"},
        {"origin": "LPA", "destination": "MAD", "outbound_date": "2026-08-30", "return_date": None, "leg_direction": "inbound", "trip_type": "round_trip"},
    ]
    assert payload["run"]["tripType"] == "round_trip"
    assert payload["run"]["capturedFlights"] == 2
    assert {snapshot["routeKey"] for snapshot in payload["routeSnapshots"]} == {"MAD_LPA", "LPA_MAD"}
    assert {flight["leg_direction"] for flight in test_db.latest_air_flights()} == {"outbound", "inbound"}


def test_air_capture_job_persists_progress_and_result(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "flask-air-job.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)

    def fake_capture(payload, progress):
        progress(55, "Consultando Madrid → Gran Canaria")
        return {"run": {"id": 99, "capturedFlights": 1}, "routeSnapshots": []}

    monkeypatch.setattr(flask_app, "capture_air_payload", fake_capture)
    response = flask_app.app.test_client().post(
        "/api/jobs/air-capture",
        json={"areaIds": ["gran-canaria"], "direct": True, "outboundDate": "2026-08-24", "nights": 6},
    )
    assert response.status_code == 202
    job_id = response.get_json()["job"]["id"]

    for _ in range(30):
        job = test_db.get_job(job_id)
        if job and job["status"] == "succeeded":
            break
        time.sleep(0.05)
    assert job["status"] == "succeeded"
    assert job["progress"] == 100
    assert job["result"]["run"]["capturedFlights"] == 1


def test_hotel_capture_job_uses_persistent_queue(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "flask-hotel-job.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)

    def fake_capture(payload, progress):
        progress(65, "Guardando foto de mercado")
        return {"target": {"id": 1}, "snapshot": {"id": 1}, "rows": []}

    monkeypatch.setattr(flask_app, "_run_hotel_capture_job", fake_capture)
    response = flask_app.app.test_client().post(
        "/api/jobs/hotel-capture",
        json={
            "targetName": "Gran Canaria", "url": "https://www.booking.com/searchresults.es.html?ss=Gran+Canaria",
            "limit": 20,
        },
    )
    assert response.status_code == 202
    job_id = response.get_json()["job"]["id"]

    for _ in range(30):
        job = test_db.get_job(job_id)
        if job and job["status"] == "succeeded":
            break
        time.sleep(0.05)
    assert job["status"] == "succeeded"
    assert job["result"]["snapshot"]["id"] == 1


def test_air_option_sort_orders_numeric_fields_and_keeps_unknown_values_last() -> None:
    rows = [
        {"id": "slow", "price": 180, "total_duration_min": 400, "air_accessibility_index": 1.5},
        {"id": "cheap", "price": 70, "total_duration_min": 240, "air_accessibility_index": 0.7},
        {"id": "unknown", "price": None, "total_duration_min": None, "air_accessibility_index": None},
    ]

    assert [row["id"] for row in flask_app._sort_air_option_rows(rows, "price-asc")] == ["cheap", "slow", "unknown"]
    assert [row["id"] for row in flask_app._sort_air_option_rows(rows, "duration-desc")] == ["slow", "cheap", "unknown"]
    assert [row["id"] for row in flask_app._sort_air_option_rows(rows, "aai-asc")] == ["cheap", "slow", "unknown"]


def test_serpapi_normalization_keeps_missing_price_and_full_local_datetimes() -> None:
    route = AirSearchRoute("MAD", "LPA", "Madrid", "2026-10-06")
    payload = {
        "search_metadata": {"id": "S-1", "created_at": "2026-09-08T10:00:00+00:00"},
        "price_insights": {"lowest_price": 80, "typical_price_range": [100, 200]},
        "best_flights": [{
            "flights": [{
                "departure_airport": {"id": "MAD", "time": "2026-10-06 22:30"},
                "arrival_airport": {"id": "LPA", "time": "2026-10-07 00:30"},
                "airline": "Test Air", "flight_number": "TA 1", "travel_class": "Economy",
            }],
        }],
    }
    row = normalize_serpapi_response(payload, route)[0]
    assert row["price"] is None
    assert row["lowest_price"] is None
    assert row["departure_at"] == "2026-10-06 22:30"
    assert row["arrival_at"] == "2026-10-07 00:30"
    assert row["days_ahead"] == 28
    assert row["typical_price_avg"] == 150.0
    assert row["segment_signature"] == row["itinerary_id"]


def test_air_capture_estimate_uses_explicit_gradual_coverage(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "estimate.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    response = flask_app.app.test_client().post(
        "/api/air-data/capture/estimate",
        json={
            "areaIds": ["gran-canaria"], "routeKeys": ["MAD_LPA"], "countryIds": ["Espana"],
            "direct": True, "outboundDate": "2026-09-10", "dailyDays": 3,
            "weeklyUntilDays": 17, "maxQueries": 20,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["dates"] == ["2026-09-10", "2026-09-11", "2026-09-12", "2026-09-13", "2026-09-20"]
    assert payload["queries"] == 5
    assert payload["withinBudget"] is True


def test_queued_capture_without_coverage_fields_remains_single_date(tmp_path, monkeypatch) -> None:
    test_db = Database(tmp_path / "single-date-job.sqlite")
    monkeypatch.setattr(flask_app, "db", test_db)
    captured = {}

    def fake_capture(payload, progress):
        captured["dates"] = flask_app._air_capture_dates(payload)
        return {"run": {"id": 1}, "routeSnapshots": []}

    monkeypatch.setattr(flask_app, "capture_air_payload", fake_capture)
    response = flask_app.app.test_client().post(
        "/api/jobs/air-capture",
        json={"areaIds": ["gran-canaria"], "direct": True, "outboundDate": "2026-10-06"},
    )
    assert response.status_code == 202
    import time as _time
    for _ in range(30):
        if captured.get("dates"):
            break
        _time.sleep(0.02)
    assert captured["dates"] == ["2026-10-06"]


def test_booking_options_are_on_demand_and_keep_provider_provenance(monkeypatch) -> None:
    client = flask_app.app.test_client()
    monkeypatch.setattr(flask_app, "serpapi_key", lambda: "test-key")
    monkeypatch.setattr(
        flask_app,
        "fetch_booking_options",
        lambda token, key, force_live=False: {
            "search_metadata": {"id": "S-BOOK", "created_at": "2026-09-08T10:00:00Z", "cached": True},
            "booking_options": [{"together": True, "book_with": "Example", "price": 199}],
        },
    )

    response = client.post("/api/air-data/booking-options", json={"bookingToken": "token-123456789012345"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["provider"] == "serpapi"
    assert payload["bookingOptions"][0]["price"] == 199
    assert payload["searchMetadata"]["cached"] is True
