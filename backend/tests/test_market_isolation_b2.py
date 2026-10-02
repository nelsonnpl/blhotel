"""Aislamiento por mercado para photos/<id>, inventory y price-history (B2-02/I1-01/W1-11/G1-01)."""

from backend.app import flask_app
from backend.app.database import Database
from backend.app.models import MarketHotelRow

app = flask_app.app


def _client_as(owner_key: str):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["ownerKey"] = owner_key
    return client


def test_private_market_isolation_for_photos_inventory_and_price_history(tmp_path, monkeypatch) -> None:
    isolated = Database(tmp_path / "b2-02-isolation.sqlite")
    try:
        target = isolated.upsert_target(
            "Mercado privado B2-02", "https://booking.com/searchresults.html?private=b2-02-01"
        )
        isolated.ensure_identity("analyst-a-b202", "Analyst A", "analyst")
        isolated.ensure_identity("analyst-b-b202", "Analyst B", "analyst")
        isolated.grant_market_access("analyst-a-b202", target.id, "viewer")

        row = MarketHotelRow(
            hotelKey="hotel-b2-02-01",
            hotelName="Hotel B2 02",
            detailUrl="https://booking.com/hotel/es/b2-02-01.html",
            price=700,
            pricePerNight=100,
            currency="EUR",
            checkIn="2026-10-06",
            checkOut="2026-10-13",
            nights=7,
            pax=2,
            position=1,
        )
        isolated.upsert_location(row.hotelKey, row.detailUrl, 28.0, -15.4, "Gran Canaria")
        isolated.upsert_hotel_inventory(row)
        snapshot = isolated.persist_market_snapshot(
            rows=[row],
            target_id=target.id,
            source_url=target.url,
            requested_limit=10,
            available_results=1,
            captured_rows=1,
            raw_hash="b202hash01",
            capture_profile={},
        )

        monkeypatch.setattr(flask_app, "db", isolated)
        flask_app.clear_cache()

        owner_a = _client_as("analyst-a-b202")
        owner_b = _client_as("analyst-b-b202")

        # GET /api/photos/<id> — resuelve target desde el recurso.
        assert owner_a.get(f"/api/photos/{snapshot.id}").status_code == 200
        denied_photo = owner_b.get(f"/api/photos/{snapshot.id}")
        assert denied_photo.status_code == 403
        assert "mercado" in denied_photo.get_json()["error"].lower()

        # GET /api/hotels/inventory — mercados del hotel.
        ok_inv = owner_a.get("/api/hotels/inventory?hotelKey=hotel-b2-02-01")
        assert ok_inv.status_code == 200
        assert ok_inv.get_json()["inventory"]["hotelKey"] == "hotel-b2-02-01"
        denied_inv = owner_b.get("/api/hotels/inventory?hotelKey=hotel-b2-02-01")
        assert denied_inv.status_code == 403

        # Con targetId explícito también se exige concesión + pertenencia.
        assert owner_a.get(f"/api/hotels/inventory?hotelKey=hotel-b2-02-01&targetId={target.id}").status_code == 200
        assert owner_b.get(f"/api/hotels/inventory?hotelKey=hotel-b2-02-01&targetId={target.id}").status_code == 403

        # GET /api/hotels/price-history — sin targetId válido → 403.
        assert owner_a.get("/api/hotels/price-history?hotelKey=hotel-b2-02-01").status_code == 403
        assert owner_b.get("/api/hotels/price-history?hotelKey=hotel-b2-02-01").status_code == 403
        ok_hist = owner_a.get(f"/api/hotels/price-history?hotelKey=hotel-b2-02-01&targetId={target.id}")
        assert ok_hist.status_code == 200
        assert ok_hist.get_json()["history"]
        assert all(item["hotelKey"] == "hotel-b2-02-01" for item in ok_hist.get_json()["history"])
        denied_hist = owner_b.get(f"/api/hotels/price-history?hotelKey=hotel-b2-02-01&targetId={target.id}")
        assert denied_hist.status_code == 403

        # Recurso inexistente sigue siendo 404, no 403.
        assert owner_a.get("/api/photos/999999999").status_code == 404
    finally:
        isolated.conn.close()
