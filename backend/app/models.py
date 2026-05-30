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


class DashboardMetrics(BaseModel):
    latestSnapshot: MarketSnapshot | None
    cards: list[dict]
    ratingDistribution: list[dict]
    topPrices: list[dict]
    bottomPrices: list[dict]
    trend: list[dict]
    locationCoverage: dict
    market: dict
    movement: dict
    dataQuality: dict
    competitiveSet: list[dict]
    insights: list[RevenueInsight]


class ScrapeSearchResponse(BaseModel):
    target: SearchTarget
    snapshot: MarketSnapshot
    rows: list[MarketHotelRow]


class HealthResponse(BaseModel):
    ok: bool = True
    at: datetime
