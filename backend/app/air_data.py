from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any


AIRPORTS: dict[str, dict[str, Any]] = {
    "MAD": {"code": "MAD", "name": "Madrid-Barajas", "city": "Madrid", "country": "España", "lat": 40.4983, "lng": -3.5676},
    "BCN": {"code": "BCN", "name": "Barcelona-El Prat", "city": "Barcelona", "country": "España", "lat": 41.2974, "lng": 2.0833},
    "DUS": {"code": "DUS", "name": "Düsseldorf", "city": "Düsseldorf", "country": "Alemania", "lat": 51.2895, "lng": 6.7668},
    "FRA": {"code": "FRA", "name": "Frankfurt", "city": "Frankfurt", "country": "Alemania", "lat": 50.0379, "lng": 8.5622},
    "LHR": {"code": "LHR", "name": "London Heathrow", "city": "Londres", "country": "Reino Unido", "lat": 51.47, "lng": -0.4543},
    "LGW": {"code": "LGW", "name": "London Gatwick", "city": "Londres", "country": "Reino Unido", "lat": 51.1537, "lng": -0.1821},
    "AMS": {"code": "AMS", "name": "Amsterdam Schiphol", "city": "Amsterdam", "country": "Países Bajos", "lat": 52.3105, "lng": 4.7683},
    "CDG": {"code": "CDG", "name": "Paris Charles de Gaulle", "city": "París", "country": "Francia", "lat": 49.0097, "lng": 2.5479},
    "MAN": {"code": "MAN", "name": "Manchester", "city": "Manchester", "country": "Reino Unido", "lat": 53.365, "lng": -2.2728},
    "LPA": {"code": "LPA", "name": "Gran Canaria", "city": "Gran Canaria", "country": "España", "lat": 27.9319, "lng": -15.3866},
    "TFS": {"code": "TFS", "name": "Tenerife Sur", "city": "Tenerife", "country": "España", "lat": 28.0445, "lng": -16.5725},
    "ACE": {"code": "ACE", "name": "Lanzarote", "city": "Lanzarote", "country": "España", "lat": 28.9455, "lng": -13.6052},
    "FUE": {"code": "FUE", "name": "Fuerteventura", "city": "Fuerteventura", "country": "España", "lat": 28.4527, "lng": -13.8638},
}


AIR_DATA_MOCK: list[dict[str, Any]] = [
    {"search_id": "SERP-001", "itinerary_id": "MAD-LPA-IB-1", "search_datetime": "2026-06-01T09:00:00Z", "origin": "MAD", "destination": "LPA", "market": "Madrid", "outbound_date": "2026-08-24", "return_date": "2026-08-30", "days_ahead": 84, "price": 118, "lowest_price": 118, "price_level": "low", "typical_price_min": 140, "typical_price_max": 245, "typical_price_avg": 184, "total_duration_min": 170, "stops": 0, "num_layovers": 0, "num_legs": 1, "main_airline": "Iberia Express", "airlines": ["Iberia Express"], "flight_numbers": ["I2 3838"], "aircraft_models": ["Airbus A320"], "travel_classes": ["Economy"], "departure_airport_id": "MAD", "departure_airport_name": "Madrid-Barajas", "departure_time": "09:25", "arrival_airport_id": "LPA", "arrival_airport_name": "Gran Canaria", "arrival_time": "11:15", "estimated_option_capacity": 180, "google_price_level": "low", "price_history": [[1745000000, 184], [1745518400, 176], [1746036800, 170], [1746555200, 162], [1747073600, 150], [1747592000, 142], [1748110400, 136], [1748628800, 128], [1749147200, 122], [1749665600, 118]]},
    {"search_id": "SERP-001", "itinerary_id": "MAD-LPA-UX-2", "origin": "MAD", "destination": "LPA", "market": "Madrid", "outbound_date": "2026-08-24", "return_date": "2026-08-30", "days_ahead": 84, "price": 136, "lowest_price": 136, "price_level": "typical", "typical_price_min": 140, "typical_price_max": 245, "typical_price_avg": 184, "total_duration_min": 175, "stops": 0, "num_layovers": 0, "main_airline": "Air Europa", "airlines": ["Air Europa"], "flight_numbers": ["UX 9164"], "aircraft_models": ["Boeing 737-800"], "departure_airport_id": "MAD", "departure_time": "15:05", "arrival_airport_id": "LPA", "arrival_time": "16:55", "estimated_option_capacity": 186},
    {"search_id": "SERP-001", "itinerary_id": "BCN-LPA-VY-1", "origin": "BCN", "destination": "LPA", "market": "Barcelona", "outbound_date": "2026-08-24", "return_date": "2026-08-30", "days_ahead": 84, "price": 128, "lowest_price": 128, "price_level": "low", "typical_price_min": 150, "typical_price_max": 260, "typical_price_avg": 196, "total_duration_min": 205, "stops": 0, "num_layovers": 0, "main_airline": "Vueling", "airlines": ["Vueling"], "flight_numbers": ["VY 3002"], "aircraft_models": ["Airbus A321"], "departure_airport_id": "BCN", "departure_time": "07:30", "arrival_airport_id": "LPA", "arrival_time": "10:00", "estimated_option_capacity": 220},
    {"search_id": "SERP-001", "itinerary_id": "BCN-LPA-IB-2", "origin": "BCN", "destination": "LPA", "market": "Barcelona", "outbound_date": "2026-08-24", "return_date": "2026-08-30", "days_ahead": 84, "price": 172, "lowest_price": 172, "price_level": "typical", "typical_price_min": 150, "typical_price_max": 260, "typical_price_avg": 196, "total_duration_min": 325, "stops": 1, "num_layovers": 1, "main_airline": "Iberia", "airlines": ["Iberia", "Iberia Express"], "flight_numbers": ["IB 3011", "I2 3834"], "aircraft_models": ["Airbus A320"], "departure_airport_id": "BCN", "departure_time": "12:10", "arrival_airport_id": "LPA", "arrival_time": "17:35", "layover_airports": ["MAD"], "estimated_option_capacity": 180},
    {"search_id": "SERP-001", "itinerary_id": "DUS-LPA-EW-1", "origin": "DUS", "destination": "LPA", "market": "Düsseldorf", "outbound_date": "2026-08-24", "return_date": "2026-08-31", "days_ahead": 84, "price": 154, "lowest_price": 154, "price_level": "low", "typical_price_min": 190, "typical_price_max": 330, "typical_price_avg": 242, "total_duration_min": 285, "stops": 0, "num_layovers": 0, "main_airline": "Eurowings", "airlines": ["Eurowings"], "flight_numbers": ["EW 9542"], "aircraft_models": ["Airbus A320"], "departure_airport_id": "DUS", "departure_time": "10:45", "arrival_airport_id": "LPA", "arrival_time": "14:30", "estimated_option_capacity": 180},
    {"search_id": "SERP-001", "itinerary_id": "FRA-LPA-DE-1", "origin": "FRA", "destination": "LPA", "market": "Frankfurt", "outbound_date": "2026-08-24", "return_date": "2026-08-31", "days_ahead": 84, "price": 202, "lowest_price": 202, "price_level": "typical", "typical_price_min": 185, "typical_price_max": 320, "typical_price_avg": 248, "total_duration_min": 280, "stops": 0, "num_layovers": 0, "main_airline": "Condor", "airlines": ["Condor"], "flight_numbers": ["DE 1404"], "aircraft_models": ["Airbus A321"], "departure_airport_id": "FRA", "departure_time": "13:35", "arrival_airport_id": "LPA", "arrival_time": "17:15", "estimated_option_capacity": 215},
    {"search_id": "SERP-001", "itinerary_id": "LHR-LPA-BA-1", "origin": "LHR", "destination": "LPA", "market": "Londres Heathrow", "outbound_date": "2026-08-24", "return_date": "2026-08-31", "days_ahead": 84, "price": 322, "lowest_price": 322, "price_level": "high", "typical_price_min": 160, "typical_price_max": 285, "typical_price_avg": 220, "total_duration_min": 465, "stops": 1, "num_layovers": 1, "main_airline": "British Airways", "airlines": ["British Airways", "Iberia Express"], "flight_numbers": ["BA 456", "I2 3838"], "aircraft_models": ["Airbus A320"], "departure_airport_id": "LHR", "departure_time": "05:55", "arrival_airport_id": "LPA", "arrival_time": "14:15", "layover_airports": ["MAD"], "estimated_option_capacity": 180, "google_price_level": "high", "price_history": [[1745000000, 220], [1745518400, 235], [1746036800, 248], [1746555200, 262], [1747073600, 278], [1747592000, 290], [1748110400, 305], [1748628800, 312], [1749147200, 318], [1749665600, 322]]},
    {"search_id": "SERP-002", "itinerary_id": "AMS-TFS-HV-1", "origin": "AMS", "destination": "TFS", "market": "Amsterdam", "outbound_date": "2026-08-24", "return_date": "2026-08-31", "days_ahead": 84, "price": 176, "lowest_price": 176, "price_level": "low", "typical_price_min": 210, "typical_price_max": 340, "typical_price_avg": 260, "total_duration_min": 285, "stops": 0, "num_layovers": 0, "main_airline": "Transavia", "airlines": ["Transavia"], "flight_numbers": ["HV 6673"], "aircraft_models": ["Boeing 737-800"], "departure_airport_id": "AMS", "departure_time": "08:40", "arrival_airport_id": "TFS", "arrival_time": "12:25", "estimated_option_capacity": 186},
    {"search_id": "SERP-002", "itinerary_id": "CDG-TFS-AF-1", "origin": "CDG", "destination": "TFS", "market": "París", "outbound_date": "2026-08-24", "return_date": "2026-08-31", "days_ahead": 84, "price": 284, "lowest_price": 284, "price_level": "high", "typical_price_min": 180, "typical_price_max": 290, "typical_price_avg": 225, "total_duration_min": 520, "stops": 2, "num_layovers": 2, "main_airline": "Air France", "airlines": ["Air France", "Iberia"], "flight_numbers": ["AF 1348", "IB 3025"], "aircraft_models": ["Airbus A220", "Airbus A320"], "departure_airport_id": "CDG", "departure_time": "06:10", "arrival_airport_id": "TFS", "arrival_time": "14:50", "layover_airports": ["BCN", "MAD"], "estimated_option_capacity": 150},
    {"search_id": "SERP-001", "itinerary_id": "MAN-LPA-LS-1", "origin": "MAN", "destination": "LPA", "market": "Manchester", "outbound_date": "2026-08-24", "return_date": "2026-08-31", "days_ahead": 84, "price": 214, "lowest_price": 214, "price_level": "typical", "typical_price_min": 180, "typical_price_max": 310, "typical_price_avg": 238, "total_duration_min": 270, "stops": 0, "num_layovers": 0, "main_airline": "Jet2", "airlines": ["Jet2"], "flight_numbers": ["LS 781"], "aircraft_models": ["Boeing 737-800"], "departure_airport_id": "MAN", "departure_time": "16:30", "arrival_airport_id": "LPA", "arrival_time": "20:00", "estimated_option_capacity": 189},
]


def connection_type(stops: int | None, num_layovers: int | None) -> tuple[bool, str, str]:
    if stops == 0 or num_layovers == 0:
        return True, "Directo", "Directo"
    layovers = num_layovers if num_layovers is not None else stops or 0
    if layovers == 1:
        return False, "No directo", "1 escala"
    if layovers == 2:
        return False, "No directo", "2 escalas"
    return False, "No directo", "3+ escalas"


def price_signal(row: dict[str, Any]) -> str:
    lowest = row.get("lowest_price") or row.get("price")
    if lowest is None:
        return "Sin dato"
    price_min = row.get("typical_price_min")
    price_max = row.get("typical_price_max")
    # Numeric range is authoritative — SerpApi's price_level is route-level context, not per-flight
    if price_max is not None and lowest > price_max:
        return "Caro"
    if price_min is not None and lowest < price_min:
        return "Barato"
    if price_min is not None or price_max is not None:
        # Within the typical range — definitionally normal
        return "Normal"
    # No range data at all: fall back to stored string as last resort
    level = str(row.get("price_level") or "").lower()
    if level in {"low", "barato"}:
        return "Barato"
    if level in {"high", "caro"}:
        return "Caro"
    return "Normal"


def schedule_score(row: dict[str, Any]) -> int:
    score = 100
    dep = hour(row.get("departure_time"))
    arr = hour(row.get("arrival_time"))
    if dep is not None and dep < 6:
        score -= 22
    if dep is not None and 6 <= dep < 8:
        score -= 8
    if arr is not None and arr < 6:
        score -= 24
    if arr is not None and arr >= 23:
        score -= 14
    duration = row.get("total_duration_min") or 0
    if duration > 300:
        score -= min(22, (duration - 300) / 18)
    score -= min(28, (row.get("stops") or 0) * 12)
    return round(max(0, min(100, score)))


def normalize_flight(row: dict[str, Any]) -> dict[str, Any]:
    origin = str(row.get("origin") or row.get("departure_airport_id") or "NA").upper()
    destination = str(row.get("destination") or row.get("arrival_airport_id") or "NA").upper()
    stops = int(row.get("stops") or row.get("num_layovers") or 0)
    layovers = int(row.get("num_layovers") if row.get("num_layovers") is not None else stops)
    is_direct, direct_label, flight_connection_type = connection_type(stops, layovers)
    lowest = row.get("lowest_price") or row.get("price")
    typical_avg = row.get("typical_price_avg")
    accessibility = round(lowest / typical_avg, 2) if lowest and typical_avg else None
    gap = lowest - typical_avg if lowest is not None and typical_avg else None
    gap_pct = round((gap / typical_avg) * 100, 1) if gap is not None and typical_avg else None
    quality = row.get("schedule_quality_score") or schedule_score(row)
    price_quality = price_signal(row)

    result = dict(row)
    result.update(
        {
            "origin": origin,
            "destination": destination,
            "market": row.get("market") or origin,
            "leg_direction": row.get("leg_direction") or "outbound",
            "search_type": row.get("search_type") or "one_way",
            "trip_type": row.get("trip_type") or "one_way",
            "air_accessibility_index": row["air_accessibility_index"] if row.get("air_accessibility_index") is not None else accessibility,
            "price_gap_vs_typical": row["price_gap_vs_typical"] if row.get("price_gap_vs_typical") is not None else gap,
            "price_gap_pct_vs_typical": row["price_gap_pct_vs_typical"] if row.get("price_gap_pct_vs_typical") is not None else gap_pct,
            "stops": stops,
            "num_layovers": layovers,
            "is_direct": is_direct,
            "direct_label": direct_label,
            "flight_connection_type": flight_connection_type,
            "route_key": f"{origin}_{destination}",
            "market_route_label": f"{row.get('market') or origin} → {destination}",
            "price_quality_label": price_quality,
            "schedule_quality_score": quality,
            "departure_hour_bucket": row.get("departure_hour_bucket") or hour_bucket(row.get("departure_time")),
            "arrival_hour_bucket": row.get("arrival_hour_bucket") or hour_bucket(row.get("arrival_time")),
            "revenue_signal": classify_revenue(price_quality, 1 if is_direct else 0, quality),
        }
    )
    result["route_risk_level"] = route_risk(result["revenue_signal"])
    result["route_score"] = route_score(result, 1 if is_direct else 0, len(set(result.get("airlines") or [])), 100 if is_direct else 40)
    return result


def aggregate_air_data(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["origin"], row["destination"], row["market"], row.get("outbound_date"), row.get("return_date"), row.get("days_ahead"))].append(row)

    routes = []
    for options in groups.values():
        first = options[0]
        prices = [item.get("lowest_price") or item.get("price") for item in options if item.get("lowest_price") or item.get("price")]
        direct_share = sum(1 for item in options if item["is_direct"]) / len(options)
        airlines = sorted({airline for item in options for airline in item.get("airlines", []) if airline})
        aircraft = sorted({model for item in options for model in item.get("aircraft_models", []) if model})
        avg_schedule = round(mean(item.get("schedule_quality_score") or 0 for item in options), 1)
        supply = round(mean(100 if item["is_direct"] else 40 if item["num_layovers"] == 1 else 15 for item in options), 1)
        aai_values = [item["air_accessibility_index"] for item in options if item.get("air_accessibility_index") is not None]
        # Use actual numeric range from options (not the route-level price_level string)
        typical_mins = [item["typical_price_min"] for item in options if item.get("typical_price_min") is not None]
        typical_maxs = [item["typical_price_max"] for item in options if item.get("typical_price_max") is not None]
        typical_avgs = [item["typical_price_avg"] for item in options if item.get("typical_price_avg") is not None]
        route_typical_min = min(typical_mins) if typical_mins else None
        route_typical_max = max(typical_maxs) if typical_maxs else None
        route_typical_avg = round(mean(typical_avgs), 1) if typical_avgs else None
        route_lowest = min(prices) if prices else None
        route_avg = round(mean(prices), 1) if prices else None
        price_gap_pct = round(((route_avg - route_typical_avg) / route_typical_avg) * 100, 1) if route_avg and route_typical_avg else None
        price_quality = price_signal({"lowest_price": route_lowest, "typical_price_min": route_typical_min, "typical_price_max": route_typical_max})
        signal = classify_revenue(price_quality, direct_share, avg_schedule)
        score = route_score({"air_accessibility_index": mean(aai_values) if aai_values else None, "schedule_quality_score": avg_schedule}, direct_share, len(airlines), supply)
        routes.append(
            {
                "route_key": first["route_key"],
                "origin": first["origin"],
                "destination": first["destination"],
                "market": first["market"],
                "outbound_date": first.get("outbound_date"),
                "return_date": first.get("return_date"),
                "leg_direction": first.get("leg_direction") or "outbound",
                "trip_type": first.get("trip_type") or "one_way",
                "days_ahead": first.get("days_ahead"),
                "lowest_price": route_lowest,
                "avg_price": route_avg,
                "typical_price_min": route_typical_min,
                "typical_price_max": route_typical_max,
                "typical_price_avg": route_typical_avg,
                "price_gap_pct": price_gap_pct,
                "price_quality_label": price_quality,
                # Route-level demand signals from Google Flights price_insights (same for all options of a route).
                "google_price_level": next((item.get("google_price_level") for item in options if item.get("google_price_level")), None),
                "price_history": next((item.get("price_history") for item in options if item.get("price_history")), []),
                "air_accessibility_index": round(mean(aai_values), 2) if aai_values else None,
                "direct_share": direct_share,
                "direct_flight_available": any(item["is_direct"] for item in options),
                "num_options": len(options),
                "num_direct_options": sum(1 for item in options if item["is_direct"]),
                "num_airlines": len(airlines),
                "airlines_detected": airlines,
                "num_aircraft_models": len(aircraft),
                "aircraft_models_detected": aircraft,
                "avg_schedule_quality_score": avg_schedule,
                "flight_supply_score": supply,
                "route_score": score,
                "route_risk_level": route_risk(signal),
                "revenue_signal": signal,
            }
        )
    return sorted(routes, key=lambda item: item["route_score"], reverse=True)


def build_air_payload(raw_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    source_rows = AIR_DATA_MOCK if raw_rows is None else raw_rows
    flights = [normalize_flight(row) for row in source_rows]
    routes = aggregate_air_data(flights)
    airlines = {airline for row in flights for airline in row.get("airlines", [])}
    gap_values = [r["price_gap_pct"] for r in routes if r.get("price_gap_pct") is not None]
    signal_counts: dict[str, int] = {}
    for route in routes:
        signal_counts[route["route_risk_level"]] = signal_counts.get(route["route_risk_level"], 0) + 1
    quality_counts: dict[str, int] = {}
    for flight in flights:
        lbl = flight.get("price_quality_label", "Sin dato")
        quality_counts[lbl] = quality_counts.get(lbl, 0) + 1
    summary = {
        "total_routes": len({route["route_key"] for route in routes}),
        "total_options": len(flights),
        "direct_pct": round(sum(1 for row in flights if row["is_direct"]) / len(flights), 3) if flights else 0,
        "avg_lowest_price": round(mean(route["lowest_price"] for route in routes if route["lowest_price"] is not None), 1) if routes else None,
        "avg_air_accessibility_index": round(mean(route["air_accessibility_index"] for route in routes if route["air_accessibility_index"] is not None), 2) if routes else None,
        "airlines_detected": len(airlines),
        "avg_schedule_quality_score": round(mean(row["schedule_quality_score"] for row in flights), 1) if flights else None,
        "avg_price_gap_pct": round(mean(gap_values), 1) if gap_values else None,
        "opportunities_count": signal_counts.get("Oportunidad", 0),
        "risks_count": signal_counts.get("Riesgo", 0),
        "price_quality_distribution": quality_counts,
    }
    return {"flights": flights, "routes": routes, "summary": summary, "airports": AIRPORTS, "geojson": route_geojson(routes)}


def route_geojson(routes: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for route in routes:
        origin = AIRPORTS.get(route["origin"])
        destination = AIRPORTS.get(route["destination"])
        if not origin or not destination:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": route,
                "geometry": {"type": "LineString", "coordinates": [[origin["lng"], origin["lat"]], [destination["lng"], destination["lat"]]]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def classify_revenue(price_quality: str, direct_share: float, schedule_quality: float) -> str:
    if price_quality == "Sin dato":
        return "Sin señal"
    if price_quality == "Barato" and direct_share >= 0.5:
        # Cheap + well-connected = pricing opportunity regardless of schedule detail
        return "Oportunidad pricing"
    if price_quality == "Barato" and direct_share < 0.5:
        # Cheap but poor direct connectivity: marketing effort needed to convert demand
        return "Oportunidad marketing limitada"
    if price_quality == "Caro":
        # Expensive flights → access barrier → demand risk for the hotel
        return "Riesgo de demanda"
    if direct_share >= 0.45:
        return "Mercado estable"
    # Normal prices but limited direct options: functional but not ideal
    return "Mercado con fricción"


def route_score(row: dict[str, Any], direct_share: float, airline_count: int, supply: float) -> int:
    aai = row.get("air_accessibility_index")
    # AAI=1.0 (at typical avg) → 100 pts; AAI=2.0 (twice typical) → 0 pts; linear
    accessibility = max(0, min(100, (2.0 - aai) * 100)) if aai else 45
    schedule = max(0, min(100, row.get("schedule_quality_score") or 55))
    diversity = max(0, min(100, airline_count * 24))
    return round(accessibility * 0.35 + direct_share * 100 * 0.25 + schedule * 0.20 + diversity * 0.10 + supply * 0.10)


def route_risk(signal: str) -> str:
    if "Oportunidad" in signal:
        return "Oportunidad"
    if "Riesgo" in signal:
        return "Riesgo"
    if signal == "Sin señal":
        return "Sin dato"
    return "Neutro"


def hour(value: str | None) -> int | None:
    if not value or ":" not in value:
        return None
    try:
        return int(value.split(":", 1)[0])
    except ValueError:
        return None


def hour_bucket(value: str | None) -> str:
    value_hour = hour(value)
    if value_hour is None:
        return "Sin dato"
    if value_hour < 5:
        return "Madrugada"
    if value_hour < 8:
        return "Muy temprano"
    if value_hour < 12:
        return "Mañana"
    if value_hour < 17:
        return "Mediodía/tarde"
    if value_hour < 21:
        return "Tarde/noche"
    return "Noche"
