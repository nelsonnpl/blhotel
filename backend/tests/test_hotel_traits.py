import pytest

from backend.app.database import Database
from backend.app.hotel_traits import detect_chain, is_adults_only
from backend.app.models import MarketHotelRow

URL = "https://www.booking.com/searchresults.html?dest_id=1&selected_currency=EUR"


@pytest.mark.parametrize(
    ("name", "chain"),
    [
        ("Abora Catarina by Lopesan Hotels", "Lopesan"),
        ("Corallium Dunamar by Lopesan Hotels - Adults Only", "Lopesan"),  # «Dunamar» no es Dunas
        ("Kumara Serenoa By Lopesan Hotels", "Lopesan"),  # mayúsculas indiferentes
        ("Don Gregory by Dunas - Adults Only", "Dunas"),
        ("Suites & Villas by Dunas", "Dunas"),
        ("Servatur Waikiki", "Servatur"),
        ("BARCELÓ Margaritas", "Barceló"),  # sin depender de acentos ni mayúsculas
        ("Barcelo Margaritas Royal Level Adults Only", "Barceló"),
        ("H10 Playa Meloneras Horizons Collection", "H10"),
        ("HL Suite Nardos - Only Adults", "HL"),
        ("Hotel Riu Vistamar Gran Canaria - All Inclusive", "Riu"),
        ("Hotel LIVVO Lago Taurito & Aquapark", "LIVVO"),
        ("Seaside Palm Beach", "Seaside"),
        ("Gloria Palace San Agustín Thalasso & Hotel", "Gloria Palace"),
        ("Paradisus Gran Canaria - All Inclusive", "Paradisus"),  # la marca que figura en el nombre, sin deducir el grupo
        ("HD Parque Cristobal Gran Canaria", "HD"),
        ("Hotel Gran Canaria Princess - Adults Only", "Princess"),
        ("eó Suite Hotel Jardin Dorado", "eó"),
    ],
)
def test_chain_is_detected_only_from_a_literal_brand_in_the_name(name, chain):
    assert detect_chain(name) == chain


@pytest.mark.parametrize(
    "name",
    [
        "Hotel Sahara Playa",
        "Bungalows Maspalomas Oasis Club - All Inclusive.",
        "Leo Beach Hotel",  # «eó» solo cuenta al inicio del nombre
        "Hotel Green Field",
        "Hilarious Riuxe Club",  # «riu» solo cuenta como palabra completa
        "Chlorine Hotel",  # «hl» solo cuenta al inicio del nombre
        "",
        None,
    ],
)
def test_chain_is_unknown_instead_of_guessed(name):
    assert detect_chain(name) is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Barceló Margaritas Royal Level Adults Only", True),
        ("HL Suite Nardos - Only Adults", True),
        ("Hotel Gran Canaria Princess - ADULTS ONLY", True),
        ("Hotel Solo Adultos Maspalomas", True),
        ("Barceló Margaritas", False),  # el nombre no lo indica: no se afirma lo contrario
        ("Family Adultsonlyland", False),
        ("", False),
        (None, False),
    ],
)
def test_adults_only_is_true_only_when_the_name_declares_it(name, expected):
    assert is_adults_only(name) is expected


def test_market_rows_serialise_the_derived_traits():
    row = MarketHotelRow(hotelKey="a", hotelName="Don Gregory by Dunas - Adults Only", detailUrl=URL, position=1)
    dumped = row.model_dump()
    assert dumped["chain"] == "Dunas"
    assert dumped["adultsOnly"] is True
    # Son rasgos calculados, no datos de entrada: no se aceptan al construir la fila.
    assert MarketHotelRow(hotelKey="b", hotelName="Hotel Sahara Playa", detailUrl=URL, position=2, chain="Invent").model_dump()["chain"] is None


def test_latest_snapshot_endpoint_exposes_chain_and_adults_only(tmp_path, monkeypatch):
    from backend.app import flask_app

    db = Database(tmp_path / "traits.sqlite")
    target = db.upsert_target("Test", URL)
    photo = db.create_snapshot(target.id, URL, 10, 2, 2, "hash")
    for key, name in [("a", "Servatur Waikiki"), ("b", "Don Gregory by Dunas - Adults Only"), ("c", "Hotel Sahara Playa")]:
        db.upsert_location(key, URL, 28, -15, None)
        db.insert_market_hotel(photo.id, MarketHotelRow(hotelKey=key, hotelName=name, detailUrl=URL, price=700, pricePerNight=100, nights=7, currency="EUR", position=1), "ready")

    monkeypatch.setattr(flask_app, "db", db)
    monkeypatch.setattr(flask_app, "market_service", lambda: flask_app.MarketService(db, None))
    try:
        response = flask_app.app.test_client().get(f"/api/snapshots/latest?targetId={target.id}")
        assert response.status_code == 200
        rows = {row["hotelKey"]: row for row in response.get_json()["latest"]["rows"]}
        assert rows["a"]["chain"] == "Servatur" and rows["a"]["adultsOnly"] is False
        assert rows["b"]["chain"] == "Dunas" and rows["b"]["adultsOnly"] is True
        assert rows["c"]["chain"] is None
    finally:
        db.conn.close()
