from pathlib import Path

from backend.app.booking_parser import parse_booking_location, parse_booking_search_results
from backend.app.booking_graphql.detail import _free_cancellation_from_text
from backend.app.booking_graphql.helpers import currency_from_price_text, parse_price_es
from backend.app.booking_graphql.client import parse_result
from backend.app.booking_graphql.models import SearchContext
from backend.app.booking_graphql.models import TarifaDetalle
from backend.app.graphql_scraper import _tarifa_to_row

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


def test_parse_price_accepts_international_decimal_without_multiplying() -> None:
    assert parse_price_es("EUR 123.45") == 123.45
    assert parse_price_es("€ 1.234") == 1234.0
    assert currency_from_price_text("EUR 123.45") == "EUR"
    assert currency_from_price_text("123.45") is None


def test_cancellation_requires_explicit_positive_language_and_handles_negation() -> None:
    assert _free_cancellation_from_text("Cancelación gratuita hasta el 1 de octubre") is True
    assert _free_cancellation_from_text("La cancelación no es gratis") is False
    assert _free_cancellation_from_text("Sin información sobre cancelación") is None


def test_missing_search_price_is_unknown_not_sold_out() -> None:
    hotel = parse_result(
        {
            "basicPropertyData": {"id": 7, "isClosed": False},
            "displayName": {"text": "Hotel sin precio"},
            "blocks": [],
        },
        SearchContext(checkin="2026-09-10", checkout="2026-09-17", noches=7),
    )
    assert hotel.precio is None
    assert hotel.disponible is False
    assert hotel.sold_out is None
    assert hotel.observation_status == "unknown"


def test_mismatched_display_and_block_prices_do_not_create_discount() -> None:
    hotel = parse_result(
        {
            "basicPropertyData": {"id": 8, "isClosed": False},
            "displayName": {"text": "Hotel con ofertas"},
            "priceDisplayInfoIrene": {
                "displayPrice": {"amountPerStay": {"amount": 900, "currency": "EUR"}}
            },
            "blocks": [{
                "blockId": {"roomId": "a", "mealPlanId": "breakfast"},
                "finalPrice": {"amount": 700, "currency": "EUR"},
                "originalPrice": {"amount": 1000, "currency": "EUR"},
            }],
        },
        SearchContext(checkin="2026-09-10", checkout="2026-09-17", noches=7),
    )
    assert hotel.precio == 900
    assert hotel.precio_original is None
    assert hotel.descuento_pct is None


def test_unreadable_explicit_price_is_parse_error() -> None:
    hotel = parse_result(
        {
            "basicPropertyData": {"id": 10, "isClosed": False},
            "displayName": {"text": "Hotel con importe ilegible"},
            "priceDisplayInfoIrene": {
                "displayPrice": {"amountPerStay": {"amount": "no disponible", "currency": "EUR"}}
            },
        },
        SearchContext(checkin="2026-09-10", checkout="2026-09-17", noches=7),
    )
    assert hotel.precio is None
    assert hotel.observation_status == "parse_error"


def test_multiple_matching_rooms_are_not_collapsed_to_the_first_room() -> None:
    hotel = parse_result(
        {
            "basicPropertyData": {"id": 9, "isClosed": False},
            "displayName": {"text": "Hotel con varias habitaciones"},
            "priceDisplayInfoIrene": {
                "displayPrice": {"amountPerStay": {"amount": 900, "currency": "EUR"}}
            },
            "matchingUnitConfigurations": {
                "unitConfigurations": [
                    {"name": "Doble", "unitTypeNames": []},
                    {"name": "Suite", "unitTypeNames": []},
                ]
            },
        },
        SearchContext(checkin="2026-09-10", checkout="2026-09-17", noches=7),
    )
    assert hotel.tipo_habitacion is None


def test_detail_adapter_keeps_snapshot_provenance() -> None:
    row = _tarifa_to_row(
        TarifaDetalle(hotel_pagename="hotel-demo", checkin="2026-09-10", checkout="2026-09-17"),
        target_id=3,
        hotel_key="/hotel/es/hotel-demo.html",
        hotel_name="Hotel Demo",
        captured_at="2026-09-07 08:00:00",
        snapshot_id=42,
    )
    assert row.snapshotId == 42
