from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .serpapi_flights import AirSearchRoute


@dataclass(frozen=True)
class AirRouteDefinition:
    area_id: str
    area_name: str
    destination: str
    country: str
    origin: str
    market: str

    @property
    def route_key(self) -> str:
        return f"{self.origin}_{self.destination}"


AREA_DESTINATIONS = {
    "gran-canaria": {"name": "Gran Canaria", "destination": "LPA"},
    "tenerife": {"name": "Tenerife", "destination": "TFS"},
    "lanzarote": {"name": "Lanzarote", "destination": "ACE"},
    "fuerteventura": {"name": "Fuerteventura", "destination": "FUE"},
}

SOURCE_MARKETS = [
    {"country": "Espana", "origin": "MAD", "market": "Madrid"},
    {"country": "Espana", "origin": "BCN", "market": "Barcelona"},
    {"country": "Alemania", "origin": "DUS", "market": "Dusseldorf"},
    {"country": "Alemania", "origin": "FRA", "market": "Frankfurt"},
    {"country": "Reino Unido", "origin": "LHR", "market": "Londres Heathrow"},
    {"country": "Reino Unido", "origin": "MAN", "market": "Manchester"},
    {"country": "Paises Bajos", "origin": "AMS", "market": "Amsterdam"},
    {"country": "Francia", "origin": "CDG", "market": "Paris"},
]

PRESET_AREA_MAP = {
    "gran-canaria-sur": "gran-canaria",
    "gran-canaria-general": "gran-canaria",
    "tenerife-sur": "tenerife",
    "lanzarote": "lanzarote",
    "fuerteventura": "fuerteventura",
}


def all_air_route_definitions() -> list[AirRouteDefinition]:
    return [
        AirRouteDefinition(
            area_id=area_id,
            area_name=area["name"],
            destination=area["destination"],
            country=market["country"],
            origin=market["origin"],
            market=market["market"],
        )
        for area_id, area in AREA_DESTINATIONS.items()
        for market in SOURCE_MARKETS
    ]


def air_route_catalog() -> dict[str, Any]:
    routes = all_air_route_definitions()
    countries = sorted({route.country for route in routes})
    areas = []
    for area_id, area in AREA_DESTINATIONS.items():
        area_routes = [route for route in routes if route.area_id == area_id]
        country_groups = []
        for country in countries:
            country_routes = [route for route in area_routes if route.country == country]
            if not country_routes:
                continue
            country_groups.append(
                {
                    "country": country,
                    "routes": [_route_to_dict(route) for route in country_routes],
                }
            )
        areas.append(
            {
                "id": area_id,
                "name": area["name"],
                "destination": area["destination"],
                "countries": country_groups,
            }
        )
    return {"areas": areas, "countries": countries, "routes": [_route_to_dict(route) for route in routes]}


def routes_for_capture(
    area_ids: list[str],
    country_ids: list[str],
    route_keys: list[str],
    outbound_date: str,
    return_date: str | None,
) -> list[tuple[AirRouteDefinition, AirSearchRoute]]:
    requested_areas = set(area_ids)
    requested_countries = set(country_ids)
    requested_routes = set(route_keys)
    selected = []
    for route in all_air_route_definitions():
        if requested_areas and route.area_id not in requested_areas:
            continue
        if requested_countries and route.country not in requested_countries:
            continue
        if requested_routes and route.route_key not in requested_routes:
            continue
        selected.append((route, AirSearchRoute(route.origin, route.destination, route.market, outbound_date, return_date)))
    return selected


def return_date_from_nights(outbound_date: str, nights: int) -> str:
    from datetime import date

    start = date.fromisoformat(outbound_date)
    return (start + timedelta(days=nights)).isoformat()


def area_ids_from_presets(preset_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    area_ids = []
    for preset_id in preset_ids:
        area_id = PRESET_AREA_MAP.get(preset_id)
        if not area_id or area_id in seen:
            continue
        seen.add(area_id)
        area_ids.append(area_id)
    return area_ids


def _route_to_dict(route: AirRouteDefinition) -> dict[str, str]:
    return {
        "areaId": route.area_id,
        "areaName": route.area_name,
        "country": route.country,
        "origin": route.origin,
        "destination": route.destination,
        "market": route.market,
        "routeKey": route.route_key,
        "label": f"{route.market} ({route.origin}) -> {route.area_name} ({route.destination})",
    }
