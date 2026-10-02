from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
import os
import re
import time
from typing import Any

import httpx
from dotenv import load_dotenv

from .config import ROOT


SERPAPI_URL = "https://serpapi.com/search.json"

# B2-01: punto único de redacción para que `api_key` de SerpAPI nunca salga
# del proceso en errores persistidos/logueados. El placeholder evita a
# propósito la subcadena `api_key` para que `rg api_key` no dé positivos.
_SERPAPI_KEY_PLACEHOLDER = "[clave oculta]"
_SERPAPI_API_KEY_RE = re.compile(
    r"(?i)[\"']?api[_-]?key[\"']?\s*(?:[:=]|%3D|%253D)\s*[\"']?[^\s&'\"`}\],;]+[\"']?"
)


def redact_serpapi_key_text(value: Any, api_key: str | None = None) -> str:
    """Devuelve `value` sin `api_key=...` ni el valor literal de la clave.

    Cubre URLs de httpx (`...?api_key=SECRETO&...`), JSON
    (`"api_key": "SECRETO"`) y el secreto literal cuando se conoce.
    """
    text = "" if value is None else value if isinstance(value, str) else str(value)
    # Patrón primero: evita que el placeholder (con espacio) se re-procese.
    text = _SERPAPI_API_KEY_RE.sub(_SERPAPI_KEY_PLACEHOLDER, text)
    if api_key:
        key = str(api_key).strip()
        if len(key) >= 4 and key in text:
            text = text.replace(key, _SERPAPI_KEY_PLACEHOLDER)
    return text


@dataclass(frozen=True)
class AirSearchRoute:
    origin: str
    destination: str
    market: str
    outbound_date: str
    return_date: str | None = None
    leg_direction: str = "outbound"
    trip_type: str = "one_way"
    adults: int = 1
    children: int = 0
    travel_class: str = "1"
    currency: str = "EUR"
    point_of_sale: str = "ES"

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
        payload, _attempts = fetch_google_flights_with_retry(route, key, force_live=force_live)
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
        "currency": route.currency or os.getenv("AIR_DATA_CURRENCY", "EUR"),
        "hl": os.getenv("AIR_DATA_HL", "es"),
        "gl": route.point_of_sale or os.getenv("AIR_DATA_GL", "es"),
        "adults": str(route.adults),
        "children": str(route.children),
        "travel_class": route.travel_class,
        "deep_search": "true",
        "show_hidden": "true",
        "sort_by": "2",
    }
    if force_live:
        params["no_cache"] = "true"

    try:
        with httpx.Client(timeout=90) as client:
            response = client.get(SERPAPI_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001 - B2-01: nunca propagar api_key en el mensaje
        raise ValueError(redact_serpapi_key_text(str(exc), api_key)) from None
    if data.get("error"):
        raise ValueError(redact_serpapi_key_text(str(data["error"]), api_key))
    return data


def fetch_booking_options(booking_token: str, api_key: str, *, force_live: bool = False) -> dict[str, Any]:
    """Resolve seller-level booking options for one itinerary on demand.

    This deliberately does not run as part of a market capture: Booking Options
    multiplies provider calls and is only useful after an analyst selects a
    specific itinerary in the inspector.
    """
    params: dict[str, Any] = {
        "engine": "google_flights",
        "api_key": api_key,
        "booking_token": booking_token,
    }
    if force_live:
        params["no_cache"] = "true"
    try:
        with httpx.Client(timeout=90) as client:
            response = client.get(SERPAPI_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001 - B2-01: nunca propagar api_key en el mensaje
        raise ValueError(redact_serpapi_key_text(str(exc), api_key)) from None
    if data.get("error"):
        raise ValueError(redact_serpapi_key_text(str(data["error"]), api_key))
    return data


def fetch_google_flights_with_retry(
    route: AirSearchRoute,
    api_key: str,
    *,
    force_live: bool = False,
    attempts: int = 2,
    fetcher=None,
) -> tuple[dict[str, Any], int]:
    """Bounded retry with a short exponential backoff for transient provider errors."""
    max_attempts = max(1, min(int(attempts), 3))
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            request_fn = fetcher or fetch_google_flights
            return request_fn(route, api_key, force_live=force_live), attempt
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError, ValueError) as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(0.2 * (2 ** (attempt - 1)))
    if last_error is not None:
        # B2-01: punto único de salida; el mensaje re-lanzado ya va redactado
        # para que ningún `str(exc)` posterior (persistencia, API, logs) vea la clave.
        try:
            redacted = redact_serpapi_key_text(str(last_error), api_key)
            if last_error.args:
                last_error.args = (redacted,) + tuple(last_error.args[1:])
            else:
                last_error.args = (redacted,)
            if hasattr(last_error, "_message"):
                try:
                    last_error._message = redacted  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass
    raise last_error or RuntimeError("Error desconocido de SerpAPI")


def normalize_serpapi_response(payload: dict[str, Any], route: AirSearchRoute) -> list[dict[str, Any]]:
    search_metadata = payload.get("search_metadata") or {}
    price_insights = payload.get("price_insights") or {}
    typical_range = price_insights.get("typical_price_range") or []
    typical_min = typical_range[0] if len(typical_range) > 0 else None
    typical_max = typical_range[1] if len(typical_range) > 1 else None
    # Google publishes a range, not an observed average. Keep the midpoint only
    # as an explicitly derived convenience value.
    typical_midpoint = round((typical_min + typical_max) / 2, 1) if typical_min is not None and typical_max is not None else None
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
            # A route-level lowest price is not attributable to every itinerary.
            price = itinerary.get("price")
            departure_at = normalize_datetime(departure_airport.get("time"))
            arrival_at = normalize_datetime(arrival_airport.get("time"))
            segment_signature = stable_segment_signature(legs)
            departure_token = itinerary.get("departure_token")
            booking_token = itinerary.get("booking_token")
            rows.append(
                {
                    "search_id": search_metadata.get("id"),
                    "itinerary_id": segment_signature or itinerary.get("booking_token") or itinerary.get("departure_token") or f"{route.origin}-{route.destination}-{group_name}-{index}",
                    "search_datetime": search_metadata.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    "observed_at": search_metadata.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    "origin": route.origin,
                    "destination": route.destination,
                    "market": route.market,
                    "outbound_date": route.outbound_date,
                    "return_date": route.return_date,
                    "leg_direction": route.leg_direction,
                    "trip_type": route.trip_type,
                    "search_type": "one_way",
                    "days_ahead": days_ahead(route.outbound_date, search_metadata.get("created_at")),
                    "price": price,
                    "lowest_price": price,
                    "price_level": _per_flight_price_level(price, typical_min, typical_max),
                    "google_price_level": google_price_level,
                    "price_history": price_history,
                    "typical_price_min": typical_min,
                    "typical_price_max": typical_max,
                    "typical_price_avg": typical_midpoint,
                    "typical_price_midpoint": typical_midpoint,
                    "currency": route.currency,
                    "provider": "serpapi",
                    "departure_at": departure_at,
                    "arrival_at": arrival_at,
                    "departure_token": departure_token,
                    "booking_token": booking_token,
                    "segment_signature": segment_signature,
                    "baggage": itinerary.get("baggage_prices") or payload.get("baggage_prices"),
                    "extensions": itinerary.get("extensions") or [],
                    "emissions": itinerary.get("carbon_emissions"),
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
                    "departure_time": time_part(departure_at),
                    "arrival_airport_id": arrival_airport.get("id") or route.destination,
                    "arrival_airport_name": arrival_airport.get("name"),
                    "arrival_time": time_part(arrival_at),
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


def normalize_datetime(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip().replace("T", " ")
    return text or None


def time_part(value: str | None) -> str | None:
    if not value:
        return None
    parts = str(value).split()
    return parts[-1] if parts else None


def days_ahead(outbound_date: str, observed_at: str | None = None) -> int | None:
    try:
        outbound = date.fromisoformat(outbound_date)
    except ValueError:
        return None
    try:
        observed = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00")).date() if observed_at else date.today()
    except ValueError:
        observed = date.today()
    return (outbound - observed).days


def stable_segment_signature(legs: list[dict[str, Any]]) -> str:
    """Stable identity for an itinerary independent of provider tokens/order."""
    parts = []
    for leg in legs:
        dep = leg.get("departure_airport") or {}
        arr = leg.get("arrival_airport") or {}
        parts.append("|".join(str(value or "") for value in (
            dep.get("id"), dep.get("time"), arr.get("id"), arr.get("time"),
            leg.get("airline"), leg.get("flight_number"), leg.get("travel_class"),
        )))
    return sha256(";".join(parts).encode("utf-8")).hexdigest()


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
