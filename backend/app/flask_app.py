from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import os
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
    return ok(result.model_dump(), 201)


@app.get("/api/snapshots/latest")
def latest_snapshot():
    target_id = parse_int_arg("targetId", minimum=1)
    return ok({"latest": market_service().latest(target_id)})


@app.get("/api/snapshots/history")
def snapshot_history():
    target_id = parse_int_arg("targetId", minimum=1)
    limit = parse_int_arg("limit", default=20, minimum=1, maximum=100)
    return ok({"snapshots": db.snapshot_history(target_id, limit)})


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


@app.get("/api/hotels/map")
def hotels_map():
    snapshot_id = parse_int_arg("snapshotId", minimum=1)
    return ok({"rows": db.snapshot_rows(snapshot_id)})


@app.get("/api/hotels/heatmap")
def hotels_heatmap():
    target_id = parse_int_arg("targetId", minimum=1)
    photos = parse_int_arg("photos", default=6, minimum=1, maximum=24)
    return ok(db.market_heatmap(target_id, photos))


@app.get("/api/dashboard/metrics")
def dashboard_metrics():
    target_id = parse_int_arg("targetId", minimum=1)
    return ok(db.dashboard_metrics(target_id))


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
