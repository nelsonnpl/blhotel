from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, computed_field, model_validator
import json
from .capture_profile import HotelCaptureProfile, profile_from_url
from .hotel_traits import detect_chain, is_adults_only


class SearchTarget(BaseModel):
    id: int
    name: str
    url: str
    createdAt: str
    updatedAt: str


class MarketSnapshot(BaseModel):
    captureProfile: dict | None = None
    captureGroupId: str | None = None
    captureStatus: str | None = None
    captureProfileHash: str | None = None

    @model_validator(mode='before')
    @classmethod
    def read_capture_profile(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            raw = value.get('captureProfile')
            value['captureProfile'] = json.loads(raw) if isinstance(raw, str) else raw
            if value['captureProfile'] is None:
                value['captureProfile'] = profile_from_url(value.get('sourceUrl', ''))
        return value

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
    # --- señales de revenue adicionales (backend graphql; None con decodo) ---
    hotelId: str | None = None            # id estable de Booking (basicPropertyData.id)
    priceOriginal: float | None = None    # precio de referencia de la misma oferta
    discountPct: float | None = None      # % calculable sobre esa referencia
    soldOut: bool | None = None           # aparece en resultados pero sin disponibilidad
    observationStatus: Literal["available", "unavailable_for_query", "closed", "parse_error", "unknown"] | None = None
    closed: bool | None = None            # propiedad cerrada temporalmente (isClosed)
    unitsLeft: int | None = None          # "Nos quedan N a este precio" (escasez)
    accommodationType: str | None = None  # Hotel, Apartamento, Villa, Hostal...
    beachDistance: str | None = None
    topLocation: bool | None = None       # isWithinBestLocationScoreArea
    popularDistrict: str | None = None
    childrenFree: bool | None = None      # blockMatchTags.childStaysForFree
    thirdParty: bool | None = None        # inventario de un tercero (TPI), no directo del hotel
    occupancyRate: int | None = None      # nº de personas que cubre la tarifa
    # Ficha estable del alojamiento. Se mantiene en el inventario y se mezcla
    # con cada captura para que precio/disponibilidad no obliguen a re-scrapear
    # siempre los mismos atributos.
    description: str | None = None
    stars: float | None = None
    city: str | None = None
    countryCode: str | None = None
    ufi: str | None = None
    displayLocation: str | None = None
    mainDistance: str | None = None
    nearbyBeachNames: list[str] = Field(default_factory=list)
    photoUrl: str | None = None
    reviewScoreText: str | None = None
    noPrepayment: bool | None = None
    inventoryCompleteness: float | None = None
    inventoryUpdatedAt: str | None = None

    # Rasgos derivados del nombre (ver hotel_traits): no se guardan, se calculan
    # al serializar, así que no hace falta migrar ninguna foto histórica.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def chain(self) -> str | None:
        return detect_chain(self.hotelName)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def adultsOnly(self) -> bool:
        return is_adults_only(self.hotelName)


class ScrapeSearchPayload(BaseModel):
    arrivalWeeks: int = Field(default=1, ge=1, le=26)
    profile: HotelCaptureProfile | None = None
    targetId: int | None = None
    targetName: str | None = Field(default=None, max_length=120)
    url: HttpUrl
    limit: int = Field(default=120, ge=1, le=500)


class AirCapturePayload(BaseModel):
    """Explicit capture contract for the air-intelligence workflow.

    The UI deliberately requires a direct/non-direct choice; keeping it
    required here prevents a capture from silently mixing two different
    products and making the resulting trend unusable.
    """

    areaIds: list[str] = Field(min_length=1, max_length=8)
    countryIds: list[str] = Field(default_factory=list, max_length=12)
    routeKeys: list[str] = Field(default_factory=list, max_length=64)
    provider: Literal["serpapi"] = "serpapi"
    direct: bool
    # Round trips remain readable for historical captures; the new UI sends
    # one_way and all planned comparisons use the outbound leg only.
    tripType: Literal["one_way", "round_trip"] = "one_way"
    outboundDate: date
    returnDate: date | None = None
    nights: int = Field(default=6, ge=1, le=30)
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=8)
    travelClass: Literal["economy"] = "economy"
    currency: Literal["EUR"] = "EUR"
    pointOfSale: str = Field(default="ES", min_length=2, max_length=2)
    dailyDays: int = Field(default=14, ge=1, le=90)
    weeklyUntilDays: int = Field(default=90, ge=14, le=90)
    maxQueries: int = Field(default=500, ge=1, le=5000)
    # Manual photos default to a fresh provider query; callers may explicitly
    # opt into SerpAPI's one-hour cache and the run records that choice.
    forceLive: bool = True
    # Internal queue marker: a request that omitted coverage fields is a single
    # date capture, even after Pydantic materialises its defaults.
    singleDate: bool = False


class AirBookingOptionsPayload(BaseModel):
    """On-demand SerpAPI booking-options lookup for one selected itinerary."""

    provider: Literal["serpapi"] = "serpapi"
    bookingToken: str = Field(min_length=16, max_length=20000)
    forceLive: bool = False


class CreateTargetPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: HttpUrl


class WorkspacePayload(BaseModel):
    """Persisted analyst board. Layers remain declarative so the server never
    executes arbitrary SQL or client-provided expressions."""

    name: str = Field(min_length=1, max_length=120)
    targetIds: list[int] = Field(default_factory=list, max_length=12)
    globalFilters: dict[str, Any] = Field(default_factory=dict)
    layers: list[dict[str, Any]] = Field(default_factory=list, max_length=40)
    expectedVersion: int | None = Field(default=None, ge=1)


class AssistantChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class AssistantWorkspaceContext(BaseModel):
    """A narrow, reproducible BI scope supplied by the workspace UI.

    It carries identifiers and filters only. The server calculates the values
    from those identifiers; clients never submit analytical figures to Copilot.
    """

    snapshotId: int = Field(ge=1)
    checkIn: date | None = None


class AssistantChatPayload(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    targetId: int | None = None
    sessionId: int | None = Field(default=None, ge=1)
    requestId: str | None = Field(default=None, max_length=120)
    mode: Literal["quick", "auto", "analysis", "decision"] = "auto"
    # Keep the request budget explicit: four recent user/assistant pairs.
    history: list[AssistantChatTurn] = Field(default_factory=list, max_length=8)
    workspaceContext: AssistantWorkspaceContext | None = None
    # La visualización es una intención explícita de la interfaz. El modelo nunca
    # construye valores para un gráfico: el servidor los calcula desde la captura.
    visualize: bool = False
    attachmentIds: list[int] = Field(default_factory=list, max_length=5)


class AssistantSessionCreatePayload(BaseModel):
    title: str = Field(default="Nueva consulta", min_length=1, max_length=120)
    targetId: int | None = Field(default=None, ge=1)
    mode: Literal["quick", "auto", "analysis", "decision"] = "auto"


class AssistantSessionPatchPayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    targetId: int | None = Field(default=None, ge=1)
    mode: Literal["quick", "auto", "analysis", "decision"] | None = None
    pinned: bool | None = None
    status: Literal["active", "archived"] | None = None
    expectedVersion: int | None = Field(default=None, ge=1)


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


class HotelRateDetailRow(BaseModel):
    """Una fila del grid COMPLETO de tarifas de la ficha de un hotel (modo
    detalle): habitación x régimen x condiciones, no solo el precio
    "cabecera" de la búsqueda. Más lento de capturar (HTML de la ficha, no
    GraphQL) -> el usuario elige a mano a qué hoteles se le pide, tras ver
    los resultados de una búsqueda normal."""

    snapshotId: int | None = None
    id: int | None = None
    targetId: int
    hotelKey: str
    hotelName: str | None = None
    hotelPagename: str | None = None
    roomType: str | None = None
    maxOccupancy: int | None = None
    priceOriginal: float | None = None
    priceFinal: float | None = None
    currency: str | None = None
    board: str | None = None
    prepaymentText: str | None = None
    program: str | None = None
    cancellationText: str | None = None
    freeCancellation: bool | None = None
    unitsLeft: int | None = None
    blockUid: str | None = None
    soldOut: bool | None = None          # ficha sin ninguna tarifa disponible
    genius: bool | None = None
    breakfastScore: float | None = None
    breakfastTypeId: int | None = None
    bedComfortScore: float | None = None
    bedComfortReviews: int | None = None
    stars: float | None = None
    checkIn: str | None = None
    checkOut: str | None = None
    adults: int | None = None
    children: int | None = None
    rooms: int | None = None
    capturedAt: str | None = None


class ScrapeDetailPayload(BaseModel):
    snapshotId: int | None = Field(default=None, ge=1)
    targetId: int
    hotels: list[dict] = Field(default_factory=list)  # [{hotelKey, detailUrl}, ...]
    checkIn: str
    checkOut: str
    adults: int = Field(default=2, ge=1, le=10)
    children: int = Field(default=0, ge=0, le=10)
    rooms: int = Field(default=1, ge=1, le=10)


class ScrapeDetailResponse(BaseModel):
    targetId: int
    hotelsRequested: int
    hotelsCaptured: int
    rows: list[HotelRateDetailRow]


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
