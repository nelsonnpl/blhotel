from __future__ import annotations

from backend.app import flask_app
from backend.app.database import Database
from backend.app.models import MarketHotelRow


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
