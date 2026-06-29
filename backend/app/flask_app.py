from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import os
import time
from typing import Any

from flask import Flask, jsonify, render_template, request
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from .config import load_settings
from .database import Database
from .decodo import DecodoClient
from .models import CreateTargetPayload, ScrapeSearchPayload
from .services import MarketService

settings = load_settings(require_decodo=False)
db = Database(settings.sqlite_path)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True


# ---------------------------------------------------------------------------
# Lightweight in-process TTL cache for expensive read endpoints.
# Inputs only change on a manual capture, so a short TTL is safe and we also
# clear the cache explicitly whenever new data is written.
# ---------------------------------------------------------------------------
_CACHE: dict[tuple, tuple[float, Any]] = {}
_CACHE_TTL = 30.0  # seconds


def cached(key: tuple, producer):
    now = time.monotonic()
    hit = _CACHE.get(key)
    if hit and (now - hit[0]) < _CACHE_TTL:
        return hit[1]
    value = producer()
    _CACHE[key] = (now, value)
    return value


def clear_cache() -> None:
    _CACHE.clear()


def market_service(require_decodo: bool = False) -> MarketService:
    runtime = load_settings(require_decodo=require_decodo)
    return MarketService(db, DecodoClient(runtime.decodo))


def serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, tuple):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value


def ok(payload: dict[str, Any] | None = None, status: int = 200):
    return jsonify(serialize(payload or {})), status


def error_response(message: str, status: int = 400, **extra: Any):
    body: dict[str, Any] = {"error": message}
    body.update(extra)
    return jsonify(serialize(body)), status


def parse_int_arg(name: str, default: int | None = None, minimum: int | None = None, maximum: int | None = None) -> int:
    raw = request.args.get(name)
    if raw is None:
        if default is None:
            raise ValueError(f"{name} es obligatorio")
        value = default
    else:
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{name} debe ser numerico") from exc
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} debe ser mayor o igual a {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} debe ser menor o igual a {maximum}")
    return value


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return ok(
        {
            "ok": True,
            "at": datetime.now(timezone.utc).isoformat(),
            "stack": "python-flask",
            "database": str(settings.sqlite_path),
        }
    )


@app.get("/api/targets")
def targets():
    return ok({"targets": db.list_targets()})


@app.post("/api/targets")
def create_target():
    payload = CreateTargetPayload.model_validate(request.get_json(silent=True) or {})
    target = db.upsert_target(payload.name, str(payload.url))
    return ok({"target": target}, 201)


@app.post("/api/scrape/search")
def scrape_search():
    try:
        service = market_service(require_decodo=True)
    except ValueError as exc:
        return error_response(str(exc), 400)

    payload = ScrapeSearchPayload.model_validate(request.get_json(silent=True) or {})
    result = asyncio.run(service.scrape_search(payload))
    clear_cache()  # new snapshot written — drop stale cached reads
    return ok(result.model_dump(), 201)


@app.get("/api/snapshots/latest")
def latest_snapshot():
    target_id = parse_int_arg("targetId", minimum=1)
    return ok({"latest": market_service().latest(target_id)})


@app.get("/api/photos/history")
def photo_history():
    target_id = parse_int_arg("targetId", minimum=1)
    limit = parse_int_arg("limit", default=24, minimum=1, maximum=100)
    return ok({"photos": db.photo_history(target_id, limit)})


@app.get("/api/photos/<int:snapshot_id>")
def photo_detail(snapshot_id: int):
    detail = db.photo_detail(snapshot_id)
    if detail is None:
        return error_response("Foto no encontrada", 404)
    return ok(detail)


@app.get("/api/hotels/heatmap")
def hotels_heatmap():
    target_id = parse_int_arg("targetId", minimum=1)
    photos = parse_int_arg("photos", default=6, minimum=1, maximum=24)
    return ok(cached(("heatmap", target_id, photos), lambda: db.market_heatmap(target_id, photos)))


@app.get("/api/dashboard/metrics")
def dashboard_metrics():
    target_id = parse_int_arg("targetId", minimum=1)
    return ok(cached(("dashboard", target_id), lambda: db.dashboard_metrics(target_id)))


# ---------------------------------------------------------------------------
# Revenue Management Analytics endpoints
# ---------------------------------------------------------------------------


@app.get("/api/analytics/pickup")
def analytics_pickup():
    target_id = parse_int_arg("targetId", minimum=1)
    hotel_key = request.args.get("hotelKey")
    check_in = request.args.get("checkIn")
    limit = parse_int_arg("limit", default=50, minimum=1, maximum=200)
    pickup = cached(
        ("pickup", target_id, hotel_key, check_in, limit),
        lambda: db.pickup_analysis(target_id, hotel_key=hotel_key, check_in=check_in, limit=limit),
    )
    return ok({"pickup": pickup})


@app.get("/api/analytics/demand-curve")
def analytics_demand_curve():
    target_id = parse_int_arg("targetId", minimum=1)
    return ok({"demandCurve": cached(("demand", target_id), lambda: db.demand_curve(target_id))})


@app.get("/api/analytics/competitive-stability")
def analytics_competitive_stability():
    target_id = parse_int_arg("targetId", minimum=1)
    snapshots = parse_int_arg("snapshots", default=10, minimum=2, maximum=30)
    stability = cached(
        ("stability", target_id, snapshots),
        lambda: db.competitive_stability(target_id, snapshots_count=snapshots),
    )
    return ok({"stability": stability})


@app.get("/api/analytics/revenue-opportunities")
def analytics_revenue_opportunities():
    target_id = parse_int_arg("targetId", minimum=1)
    air_payload = _get_air_payload()
    return ok({"opportunities": db.revenue_opportunities(target_id, air_data=air_payload)})


def _get_air_payload() -> dict | None:
    """Try to load air data (mock or live) for analytics endpoints."""
    try:
        from .air_data import build_air_payload
        return build_air_payload()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Air Data endpoints
# ---------------------------------------------------------------------------


@app.get("/api/air-data")
def air_data():
    from .air_data import build_air_payload, AIR_DATA_MOCK
    from .serpapi_flights import fetch_serpapi_air_rows, configured_air_routes, should_use_live_air_data

    raw_rows = db.list_air_flights()
    source = "db" if raw_rows else "mock"
    warning = ""

    # Si la BD está vacía y SerpApi está configurado, captura automática y persiste
    if not raw_rows and should_use_live_air_data():
        try:
            routes = configured_air_routes()
            raw_rows = fetch_serpapi_air_rows()
            run_id = db.create_air_run("serpapi", len(routes))
            for row in raw_rows:
                db.insert_air_flight(run_id, row)
            routes_captured = len({f"{r.get('origin')}_{r.get('destination')}" for r in raw_rows})
            db.finish_air_run(run_id, routes_captured=routes_captured, flights_captured=len(raw_rows))
            source = "serpapi"
        except Exception as exc:
            logger.warning("Auto air-data fetch failed: %s", exc)
            raw_rows = []
            source = "mock"
            warning = f"SerpApi no disponible: {exc}. Mostrando datos de demostración."

    payload = build_air_payload(raw_rows if raw_rows else None)
    payload["source"] = source
    payload["is_live"] = source in ("serpapi", "db")
    if warning:
        payload["warning"] = warning
    return ok(payload)


@app.get("/api/air-data/catalog")
def air_data_catalog():
    from .air_catalog import air_route_catalog
    return ok(air_route_catalog())


@app.get("/api/air-data/history")
def air_data_history():
    route_key = request.args.get("routeKey", "")
    if not route_key:
        return ok({"history": []})
    history = db.air_route_history(route_key)
    return ok({"history": history})


@app.post("/api/air-data/capture")
def air_data_capture():
    from .air_data import build_air_payload, AIR_DATA_MOCK
    from .serpapi_flights import fetch_serpapi_air_rows, configured_air_routes, should_use_live_air_data
    body = request.get_json(silent=True) or {}
    force_live = bool(body.get("forceLive", False))

    if should_use_live_air_data(force_live=force_live):
        source = "serpapi"
        routes = configured_air_routes()
        try:
            raw_rows = fetch_serpapi_air_rows(force_live=force_live)
        except Exception as exc:
            return error_response(f"SerpApi error: {exc}", 502)
    else:
        source = "mock"
        routes = []
        raw_rows = list(AIR_DATA_MOCK)

    run_id = db.create_air_run(source, len(routes))
    for row in raw_rows:
        db.insert_air_flight(run_id, row)
    routes_captured = len({f"{r.get('origin')}_{r.get('destination')}" for r in raw_rows})
    db.finish_air_run(run_id, routes_captured=routes_captured, flights_captured=len(raw_rows))
    clear_cache()  # new air run written — drop stale cached analytics

    payload = build_air_payload(raw_rows)
    payload["source"] = source
    payload["is_live"] = source == "serpapi"
    return ok({"run": {"id": run_id, "source": source, "capturedFlights": len(raw_rows)}, "data": payload}, 201)


# ---------------------------------------------------------------------------
# Copiloto IA de revenue
# ---------------------------------------------------------------------------


@app.get("/api/ai/status")
def ai_status():
    from .ai import is_configured, openai_settings
    return ok({"configured": is_configured(), "model": openai_settings()["model"]})


@app.post("/api/ai/chat")
def ai_chat_endpoint():
    from .ai import ai_chat
    body = request.get_json(silent=True) or {}
    messages = body.get("messages")
    context = body.get("context")
    if not isinstance(messages, list) or not messages:
        return error_response("Faltan mensajes para el copiloto IA", 400)
    try:
        reply = ai_chat(messages, context if isinstance(context, dict) else None)
    except ValueError as exc:
        return error_response(str(exc), 503)
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the terminal
        logger.exception("AI chat error")
        return error_response(f"Error del copiloto IA: {exc}", 502)
    return ok({"reply": reply})


@app.errorhandler(ValidationError)
def validation_error(error: ValidationError):
    return error_response("Payload invalido", 400, details=error.errors())


@app.errorhandler(ValueError)
def value_error(error: ValueError):
    return error_response(str(error), 400)


@app.errorhandler(HTTPException)
def http_error(error: HTTPException):
    return error_response(error.description or error.name, error.code or 500)


@app.errorhandler(Exception)
def unhandled_error(error: Exception):
    logger.exception("Unhandled Flask error")
    message = str(error) or error.__class__.__name__
    safe_message = message if app.debug else "Error interno del servidor"
    return error_response(safe_message, 500)


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
