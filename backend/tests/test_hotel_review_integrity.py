from __future__ import annotations

import csv
import io

from backend.app import flask_app
from backend.app.database import Database


def _pilot_db(tmp_path):
    database = Database(tmp_path / "reviews.sqlite")
    database.bootstrap_hotel_review_workspace()
    key = "atlas:servatur-monte-feliz"
    database.conn.execute(
        "INSERT INTO app_identities(owner_key,display_name,role,active,created_at,updated_at) "
        "VALUES ('review-tester','Review tester','admin',1,'2026-09-23','2026-09-23')"
    )
    database.conn.commit()
    return database, key


def test_bootstrap_preserves_confirmed_link_and_review_provenance(tmp_path):
    database, key = _pilot_db(tmp_path)
    confirmed = "https://www.google.com/travel/hotels/entity/custom/reviews"
    database.upsert_hotel_source_link(key, "google_hotels", confirmed, verified=True)
    database.bootstrap_hotel_review_workspace()
    link = database.conn.execute(
        "SELECT url,verified FROM hotel_source_links WHERE hotel_key=? AND source='google_hotels'", (key,)
    ).fetchone()
    assert link["url"] == confirmed and link["verified"] == 1

    first = {"sourceReviewId": "review-1", "reviewOriginal": "Habitación amplia", "rating": 5,
             "datePrecision": "relative", "relativePublishedAt": "hace un mes",
             "sourceUrl": "https://www.google.com/maps/reviews/1"}
    assert database.upsert_hotel_reviews(key, "google", None, [first])["inserted"] == 1
    assert database.upsert_hotel_reviews(key, "google", None, [{"sourceReviewId": "review-1",
                                                                 "reviewOriginal": "Habitación amplia"}])["updated"] == 0
    row = database.hotel_review_rows(key)["items"][0]
    assert row["sourceUrl"] == first["sourceUrl"]
    assert row["datePrecision"] == "relative"
    assert row["relativePublishedAt"] == "hace un mes"
    assert row["versionCount"] == 1

    assert database.upsert_hotel_reviews(key, "google", None, [{"sourceReviewId": "review-1",
                                                                 "reviewOriginal": "Habitación más amplia"}])["updated"] == 1
    row = database.hotel_review_rows(key)["items"][0]
    assert row["versionCount"] == 2
    assert len(database.hotel_review_history(key, row["id"])) == 2


def test_api_rejects_invalid_route_budget_and_unverified_booking(tmp_path, monkeypatch):
    database, key = _pilot_db(tmp_path)
    monkeypatch.setattr(flask_app, "db", database)
    monkeypatch.setattr(flask_app, "current_owner_key", lambda: "review-tester")
    client = flask_app.app.test_client()

    assert client.get("/api/hotel-reviews/hk_!!!/profile").status_code == 404
    for budget in ("NaN", "Infinity", "-Infinity"):
        response = client.post("/api/hotel-reviews/captures", json={
            "hotelKeys": [key], "sources": ["google_hotels"], "maxReviews": 2000,
            "budgetUsd": budget, "estimatedDecisionCostUsd": 0.001,
        })
        assert response.status_code == 400
        response = client.post(f"/api/hotel-reviews/{key}/analyses", json={"budgetUsd": budget})
        assert response.status_code == 400

    database.upsert_hotel_source_link(key, "booking", "https://www.booking.com/hotel/es/example.html",
                                      verified=False)
    response = client.post("/api/hotel-reviews/captures", json={
        "hotelKeys": [key], "sources": ["booking"], "maxReviews": 100,
    })
    assert response.status_code == 400
    assert "confirmarse" in response.get_json()["skipped"][0]["reason"]
    assert database.conn.execute("SELECT COUNT(*) FROM hotel_review_runs").fetchone()[0] == 0


def test_analysis_batches_include_booking_and_track_unprocessed_reviews(tmp_path):
    database, key = _pilot_db(tmp_path)
    google = [{"sourceReviewId": f"g-{index}", "reviewOriginal": f"Google {index}", "rating": 4}
              for index in range(81)]
    booking = [{"sourceReviewId": "b-1", "reviewOriginal": "Booking", "rating": 8,
                "ratingScale": 10}]
    database.upsert_hotel_reviews(key, "google", None, google)
    database.upsert_hotel_reviews(key, "booking", None, booking)
    batch, pending = database.hotel_review_analysis_candidates(
        key, ["google", "booking"], "test-model", "hotel-review-analysis.v1"
    )
    assert pending == 82 and len(batch) == 80
    assert {item["source"] for item in batch} == {"google", "booking"}
    database.save_hotel_review_analysis(
        key, sources=["google", "booking"], model="test-model",
        prompt_version="hotel-review-analysis.v1", analysis={},
        evidence=[{"reviewId": item["reviewId"], "source": item["source"],
                   "contentHash": item["contentHash"]} for item in batch],
        input_hash="first", cost_usd=0,
    )
    next_batch, pending = database.hotel_review_analysis_candidates(
        key, ["google", "booking"], "test-model", "hotel-review-analysis.v1"
    )
    assert pending == len(next_batch) == 2
    assert all(item["source"] == "google" for item in next_batch)


def test_attribute_selection_keeps_conflicting_observations(tmp_path, monkeypatch):
    database, key = _pilot_db(tmp_path)
    for value, source in (("4 estrellas", "google"), ("5 estrellas", "booking")):
        database.conn.execute(
            """INSERT INTO hotel_attribute_observations
               (hotel_key,attribute,value_json,source,observed_at,selected)
               VALUES (?, 'category', ?, ?, '2026-09-23', 0)""",
            (key, f'"{value}"', source),
        )
    database.conn.commit()
    observations = database.hotel_review_profile(key)["attributes"]["category"]
    selected_id = observations[0]["id"]
    monkeypatch.setattr(flask_app, "db", database)
    monkeypatch.setattr(flask_app, "current_owner_key", lambda: "review-tester")
    response = flask_app.app.test_client().put(
        f"/api/hotel-reviews/{key}/attributes/selection",
        json={"attribute": "category", "observationId": selected_id},
    )
    assert response.status_code == 200
    result = database.hotel_review_profile(key)["attributes"]["category"]
    assert len(result) == 2
    assert [item["id"] for item in result if item["selected"]] == [selected_id]


def test_tsv_export_roundtrips_booking_text_fields(tmp_path, monkeypatch):
    database, key = _pilot_db(tmp_path)
    positive = 'Muy bien\tubicado, "cerca"\ndel mar'
    negative = "Ruido; tarde: sí."
    database.upsert_hotel_reviews(key, "booking", None, [{
        "sourceReviewId": "booking-1", "positiveText": positive,
        "negativeText": negative, "reviewOriginal": "Reseña\noriginal",
        "reviewEs": "Reseña, español", "rating": 8, "ratingScale": 10,
    }])
    monkeypatch.setattr(flask_app, "db", database)
    monkeypatch.setattr(flask_app, "current_owner_key", lambda: "review-tester")
    response = flask_app.app.test_client().get(f"/api/hotel-reviews/{key}/export.tsv")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.get_data(as_text=True).lstrip("\ufeff")), delimiter="\t"))
    assert len(rows) == 1
    assert rows[0]["positiveText"] == positive
    assert rows[0]["negativeText"] == negative
    assert rows[0]["reviewOriginal"] == "Reseña\noriginal"
    assert rows[0]["reviewEs"] == "Reseña, español"
