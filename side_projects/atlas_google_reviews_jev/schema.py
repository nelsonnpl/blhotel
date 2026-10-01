from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GoogleReview(BaseModel):
    """A normalized review observation.

    ``reviewId`` is optional because public Google pages do not expose a
    stable identifier consistently. The future Atlas adapter can deduplicate
    by source URL, hotel key, publish time, author and content hash.
    """

    model_config = ConfigDict(extra="forbid")

    reviewId: str | None = None
    hotelName: str | None = None
    authorName: str | None = None
    rating: float | None = Field(default=None, ge=1, le=5)
    text: str | None = None
    language: str | None = None
    publishedAt: str | None = None
    relativePublishedAt: str | None = None
    discoveryContexts: list[dict] = Field(default_factory=list)
    sourceUrl: str
    capturedAt: str
    source: Literal["google_reviews_jev"] = "google_reviews_jev"


class GoogleReviewsResult(BaseModel):
    """Stable side-project contract for a future Atlas ingestion adapter."""

    model_config = ConfigDict(extra="forbid")

    schemaVersion: Literal["atlas.google-reviews.v1"] = "atlas.google-reviews.v1"
    status: Literal["ok", "empty", "blocked", "parse_error", "partial", "exhausted", "budget_exhausted"]
    sourceUrl: str
    finalUrl: str | None = None
    hotelName: str | None = None
    aggregateRating: float | None = Field(default=None, ge=1, le=5)
    reviewCount: int | None = Field(default=None, ge=0)
    hotelAttributes: dict = Field(default_factory=dict)
    reviews: list[GoogleReview] = Field(default_factory=list)
    capturedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    navigationSteps: int = Field(default=0, ge=0)
    message: str | None = None
    coverage: dict = Field(default_factory=dict)
    modelDecisions: int = Field(default=0, ge=0)
    estimatedCostUsd: float | None = Field(default=None, ge=0)
    costBasis: Literal["provider_reported", "configured_estimate", "mixed", "unavailable"] = "unavailable"

    def atlas_records(self) -> list[dict]:
        """Return rows suitable for a future Atlas repository adapter.

        This method does not write to the production database. It gives the
        eventual adapter one stable, explicit boundary to depend on.
        """

        return [review.model_dump(mode="json") for review in self.reviews]
