from pathlib import Path

from backend.app.booking_parser import parse_booking_location, parse_booking_search_results

ROOT = Path(__file__).resolve().parents[2]


def test_parse_booking_search_results_sample() -> None:
    html = (ROOT / "backend" / "tests" / "fixtures" / "booking-search-sample.html").read_text(encoding="utf-8")
    rows = parse_booking_search_results(
        html,
        "https://www.booking.com/searchresults.es.html?checkin=2026-07-06&checkout=2026-07-12&group_adults=2",
    )

    assert len(rows) == 1
    first = rows[0]
    assert first.hotelName == "Hotel Demo Playa"
    assert first.roomType and "Habitacion Doble" in first.roomType
    assert first.rating == 8.7
    assert first.price == 1247
    assert first.currency == "EUR"
    assert first.pax == 2
    assert first.checkIn == "2026-07-06"
    assert first.checkOut == "2026-07-12"
    assert first.nights == 6
    assert first.pricePerNight == 207.83


def test_parse_booking_location() -> None:
    location = parse_booking_location(
        '<div data-atlas-latlng="27.764511470995064,-15.560991168022156"></div>'
        '<script>{"formattedAddress":"Av. de Italia 2, Playa del Ingles"}</script>'
    )
    assert round(location["latitude"], 5) == 27.76451
    assert round(location["longitude"], 5) == -15.56099
    assert "Playa del Ingles" in location["address"]
