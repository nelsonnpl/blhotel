"""Capture the three pilot hotels and export observed Google reviews as CSV."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dataset_export import REVIEW_COLUMNS, STATUS_COLUMNS, review_text_fields, write_tsv
from .jev_runner import JevNavigationError, JevUnavailable, collect_with_jev
from .schema import GoogleReviewsResult


HOTELS = (
    ("Servatur Puerto Azul", "servatur-puerto-azul", "CgsI5PHLm5bztcX7ARAB"),
    ("Servatur Monte Feliz", "servatur-monte-feliz", "CgsIwPKo4JSArfaRARAB"),
    ("Servatur Waikiki", "servatur-waikiki", "ChoInI3H9t2BqJDJARoNL2cvMTFjbTE4eWc0MhAB"),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "outputs")
    parser.add_argument("--max-reviews", type=int, default=1000,
                        help="Máximo por hotel (1-10000); usa 0 para agotar los recorridos accesibles")
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    review_rows: list[dict] = []
    status_rows: list[dict] = []
    for requested_name, slug, entity_id in HOTELS:
        url = f"https://www.google.com/travel/hotels/entity/{entity_id}/reviews?gl=es&hl=es"
        try:
            result = collect_with_jev(url, hotel_name=requested_name, max_reviews=args.max_reviews or None)
        except (JevNavigationError, JevUnavailable, ValueError) as exc:
            result = GoogleReviewsResult(
                status="parse_error", sourceUrl=url, hotelName=requested_name, message=str(exc)
            )

        (args.output_dir / f"{slug}.json").write_text(
            result.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        status_rows.append({
            "requested_hotel": requested_name,
            "observed_hotel": result.hotelName,
            "status": result.status,
            "reviews_captured": len(result.reviews),
            "aggregate_rating": result.aggregateRating,
            "google_review_count": result.reviewCount,
            "captured_at": result.capturedAt,
            "source_url": url,
            "final_url": result.finalUrl,
            "message": result.message,
        })
        for review in result.reviews:
            review_rows.append({
                "requested_hotel": requested_name,
                "observed_hotel": result.hotelName,
                "review_id": review.reviewId,
                "author": review.authorName,
                "rating": review.rating,
                **review_text_fields(review.text),
                "published_at": review.publishedAt,
                "relative_published_at": review.relativePublishedAt,
                "captured_at": review.capturedAt,
                "source_url": review.sourceUrl,
            })
        print(json.dumps({"hotel": requested_name, "status": result.status, "reviews": len(result.reviews),
                          "message": result.message}, ensure_ascii=False), flush=True)

    write_tsv(args.output_dir / "google-reviews-results.csv", review_rows, REVIEW_COLUMNS)
    write_tsv(args.output_dir / "hotel-status.csv", status_rows, STATUS_COLUMNS)

    return 0 if all(row["status"] == "ok" for row in status_rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
