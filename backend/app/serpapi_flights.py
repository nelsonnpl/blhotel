from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from .config import ROOT


SERPAPI_URL = "https://serpapi.com/search.json"


@dataclass(frozen=True)
class AirSearchRoute:
    origin: str
    destination: str
    market: str
    outbound_date: str
    return_date: str | None = None
    leg_direction: str = "outbound"
    trip_type: str = "one_way"

    @property
    def route_key(self) -> str:
        return f"{self.origin}_{self.destination}"


def serpapi_key() -> str:
    load_dotenv(ROOT / ".env", override=True)
    return (os.getenv("SERPAPI_API_KEY") or os.getenv("SERP_API_KEY") or "").strip()


def should_use_live_air_data(force_live: bool = False) -> bool:
    load_dotenv(ROOT / ".env", override=True)
    configured = (os.getenv("AIR_DATA_SOURCE") or "").strip().lower() in {"live", "serpapi", "real"}
    return bool(serpapi_key()) and (force_live or configured)


def configured_air_routes() -> list[AirSearchRoute]:
    load_dotenv(ROOT / ".env", override=True)
    raw = (os.getenv("AIR_DATA_ROUTES") or "").strip()
    if raw:
        routes = []
        for item in raw.split(";"):
            parts = [part.strip() for part in item.split(",")]
            if len(parts) < 4:
                continue
            origin, destination, outbound_date, *rest = parts
            return_date = rest[0] if rest else None
            market = rest[1] if len(rest) > 1 else origin
            routes.append(AirSearchRoute(origin.upper(), destination.upper(), market, outbound_date, return_date or None))
        if routes:
            return routes

    return [
        AirSearchRoute("MAD", "LPA", "Madrid", "2026-08-24", "2026-08-30"),
        AirSearchRoute("BCN", "LPA", "Barcelona", "2026-08-24", "2026-08-30"),
        AirSearchRoute("DUS", "LPA", "Düsseldorf", "2026-08-24", "2026-08-31"),
        AirSearchRoute("FRA", "LPA", "Frankfurt", "2026-08-24", "2026-08-31"),
        AirSearchRoute("LHR", "LPA", "Londres Heathrow", "2026-08-24", "2026-08-31"),
        AirSearchRoute("AMS", "TFS", "Amsterdam", "2026-08-24", "2026-08-31"),
        AirSearchRoute("CDG", "TFS", "París", "2026-08-24", "2026-08-31"),
        AirSearchRoute("MAN", "LPA", "Manchester", "2026-08-24", "2026-08-31"),
    ]


def fetch_serpapi_air_rows(force_live: bool = False) -> list[dict[str, Any]]:
    key = serpapi_key()
    if not key:
        raise ValueError("Falta SERPAPI_API_KEY en .env")

    rows: list[dict[str, Any]] = []
    for route in configured_air_routes():
        payload = fetch_google_flights(route, key, force_live=force_live)
        rows.extend(normalize_serpapi_response(payload, route))
    return rows


def fetch_google_flights(route: AirSearchRoute, api_key: str, force_live: bool = False) -> dict[str, Any]:
    params: dict[str, Any] = {
        "engine": "google_flights",
        "api_key": api_key,
        "departure_id": route.origin,
        "arrival_id": route.destination,
        "outbound_date": route.outbound_date,
        "type": "2",
        "currency": os.getenv("AIR_DATA_CURRENCY", "EUR"),
        "hl": os.getenv("AIR_DATA_HL", "es"),
        "gl": os.getenv("AIR_DATA_GL", "es"),
        "adults": os.getenv("AIR_DATA_ADULTS", "1"),
        "travel_class": os.getenv("AIR_DATA_TRAVEL_CLASS", "1"),
        "deep_search": "true",
        "show_hidden": "true",
        "sort_by": "2",
    }
    if force_live:
        params["no_cache"] = "true"

    with httpx.Client(timeout=90) as client:
        response = client.get(SERPAPI_URL, params=params)
        response.raise_for_status()
        data = response.json()
    if data.get("error"):
        raise ValueError(str(data["error"]))
    return data


def normalize_serpapi_response(payload: dict[str, Any], route: AirSearchRoute) -> list[dict[str, Any]]:
    search_metadata = payload.get("search_metadata") or {}
    price_insights = payload.get("price_insights") or {}
    typical_range = price_insights.get("typical_price_range") or []
    typical_min = typical_range[0] if len(typical_range) > 0 else None
    typical_max = typical_range[1] if len(typical_range) > 1 else None
    typical_avg = round((typical_min + typical_max) / 2, 1) if typical_min and typical_max else None
    global_lowest = price_insights.get("lowest_price")
    # Route-level demand signals straight from Google Flights price_insights.
    google_price_level = price_insights.get("price_level")
    price_history = price_insights.get("price_history") or []

    groups = [("best", payload.get("best_flights") or []), ("other", payload.get("other_flights") or [])]
    rows: list[dict[str, Any]] = []
    for group_name, itineraries in groups:
        for index, itinerary in enumerate(itineraries, start=1):
            legs = itinerary.get("flights") or []
            if not legs:
                continue
            first_leg = legs[0]
            last_leg = legs[-1]
            departure_airport = first_leg.get("departure_airport") or {}
            arrival_airport = last_leg.get("arrival_airport") or {}
            layovers = itinerary.get("layovers") or []
            airlines = unique_values([leg.get("airline") for leg in legs])
            flight_numbers = unique_values([leg.get("flight_number") for leg in legs])
            aircraft_models = unique_values([leg.get("airplane") for leg in legs])
            travel_classes = unique_values([leg.get("travel_class") for leg in legs])
            price = itinerary.get("price") or global_lowest
            departure_time = time_part(departure_airport.get("time"))
            arrival_time = time_part(arrival_airport.get("time"))
            rows.append(
                {
                    "search_id": search_metadata.get("id"),
                    "itinerary_id": itinerary.get("booking_token") or itinerary.get("departure_token") or f"{route.origin}-{route.destination}-{group_name}-{index}",
                    "search_datetime": search_metadata.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    "origin": route.origin,
                    "destination": route.destination,
                    "market": route.market,
                    "outbound_date": route.outbound_date,
                    "return_date": route.return_date,
                    "leg_direction": route.leg_direction,
                    "trip_type": route.trip_type,
                    "search_type": "one_way",
                    "days_ahead": days_ahead(route.outbound_date),
                    "price": price,
                    "lowest_price": price,
                    "price_level": _per_flight_price_level(price, typical_min, typical_max),
                    "google_price_level": google_price_level,
                    "price_history": price_history,
                    "typical_price_min": typical_min,
                    "typical_price_max": typical_max,
                    "typical_price_avg": typical_avg,
                    "result_group": group_name,
                    "option_index": index,
                    "total_duration_min": itinerary.get("total_duration"),
                    "stops": max(0, len(legs) - 1),
                    "num_layovers": len(layovers) if layovers else max(0, len(legs) - 1),
                    "num_legs": len(legs),
                    "main_airline": airlines[0] if airlines else itinerary.get("airline"),
                    "airlines": airlines,
                    "flight_numbers": flight_numbers,
                    "aircraft_models": aircraft_models,
                    "travel_classes": travel_classes,
                    "departure_airport_id": departure_airport.get("id") or route.origin,
                    "departure_airport_name": departure_airport.get("name"),
                    "departure_time": departure_time,
                    "arrival_airport_id": arrival_airport.get("id") or route.destination,
                    "arrival_airport_name": arrival_airport.get("name"),
                    "arrival_time": arrival_time,
                    "layover_airports": [layover.get("id") or layover.get("name") for layover in layovers if layover.get("id") or layover.get("name")],
                }
            )
    return rows


def _per_flight_price_level(price: float | None, typical_min: float | None, typical_max: float | None) -> str | None:
    if price is None:
        return None
    if typical_max is not None and price > typical_max:
        return "high"
    if typical_min is not None and price < typical_min:
        return "low"
    return "typical"


def time_part(value: str | None) -> str | None:
    if not value:
        return None
    parts = str(value).split()
    return parts[-1] if parts else None


def days_ahead(outbound_date: str) -> int | None:
    try:
        outbound = date.fromisoformat(outbound_date)
    except ValueError:
        return None
    return (outbound - date.today()).days


def unique_values(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value:
            continue
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
