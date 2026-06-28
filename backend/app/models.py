from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SearchTarget(BaseModel):
    id: int
    name: str
    url: str
    createdAt: str
    updatedAt: str


class MarketSnapshot(BaseModel):
    id: int
    targetId: int
    sourceUrl: str
    requestedLimit: int
    availableResults: int
    capturedRows: int
    scrapedAt: str


class MarketHotelRow(BaseModel):
    id: int | None = None
    snapshotId: int | None = None
    hotelKey: str
    hotelName: str
    detailUrl: str
    roomType: str | None = None
    rating: float | None = None
    price: float | None = None
    priceText: str | None = None
    currency: str | None = None
    pax: int | None = None
    checkIn: str | None = None
    checkOut: str | None = None
    nights: int | None = None
    pricePerNight: float | None = None
    pricePerPersonPerNight: float | None = None
    position: int
    locationStatus: Literal["ready", "location_pending"] = "location_pending"
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    # Comparability signals extracted from the search card.
    board: str | None = None
    reviewCount: int | None = None
    freeCancellation: bool | None = None


class ScrapeSearchPayload(BaseModel):
    targetId: int | None = None
    targetName: str | None = Field(default=None, max_length=120)
    url: HttpUrl
    limit: int = Field(default=120, ge=1, le=500)


class CreateTargetPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: HttpUrl


class RevenueInsight(BaseModel):
    id: str
    type: str
    severity: Literal["info", "warning", "critical"]
    title: str
    message: str
    hotelName: str | None = None
    value: float | None = None
    benchmark: float | None = None
    changePct: float | None = None


class ScrapeSearchResponse(BaseModel):
    target: SearchTarget
    snapshot: MarketSnapshot
    rows: list[MarketHotelRow]


# ---------------------------------------------------------------------------
# Revenue Management Analytics models
# ---------------------------------------------------------------------------


class PickupEntry(BaseModel):
    hotelKey: str
    hotelName: str
    checkIn: str | None = None
    observedAt: str
    previousObservedAt: str | None = None
    currentPrice: float | None = None
    previousPrice: float | None = None
    pricePerNight: float | None = None
    previousPricePerNight: float | None = None
    pickupAbsolute: float | None = None
    pickupPct: float | None = None


class DemandCurvePoint(BaseModel):
    daysUntilCheckIn: int
    avgAdr: float
    medianAdr: float
    minAdr: float
    maxAdr: float
    observations: int


class CompetitiveStabilityEntry(BaseModel):
    hotelKey: str
    hotelName: str
    avgPricePerNight: float
    stddevPricePerNight: float
    consistencyScore: float
    positioningLabel: str
    avgGapVsMarketPct: float
    observations: int


class RevenueOpportunity(BaseModel):
    id: str
    type: str
    severity: Literal["info", "warning", "critical"]
    title: str
    message: str
    score: float
    checkIn: str | None = None
    hotelKey: str | None = None
    hotelName: str | None = None
    currentAdr: float | None = None
    marketAdr: float | None = None
    flightAvgPrice: float | None = None
