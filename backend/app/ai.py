from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from .config import ROOT

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/owl-alpha"

SYSTEM_PROMPT = (
    "Eres \"Copiloto Revenue\", un asistente experto en revenue management hotelero integrado en "
    "una terminal estilo Bloomberg para RIU Hotels (resorts de las Islas Canarias).\n\n"
    "Dominas: ADR, RevPAR, pickup/pace, comp-set y paridad competitiva, elasticidad de precio, "
    "segmentación por tiers de precio, rate shopping, régimen (todo incluido vs otros) y el uso de "
    "los datos de VUELOS como indicador adelantado de la demanda del destino (precios aéreos al alza = "
    "demanda creciente = margen para sostener/subir tarifa).\n\n"
    "Tienes acceso al SNAPSHOT actual del mercado cargado en la terminal (hoteles y vuelos), que se te "
    "facilita más abajo en JSON. Razona SOBRE esos datos concretos del mercado activo. Si un dato no está "
    "en el snapshot, dilo claramente en vez de inventarlo.\n\n"
    "Estilo: directo, accionable y conciso. Cuando recomiendes una acción de pricing, justifícala con las "
    "cifras del snapshot (gap vs mercado, presión de demanda, momentum aéreo, cuartiles, rating/reseñas, "
    "régimen…). Usa viñetas y números cuando ayuden. Responde SIEMPRE en el idioma del usuario. "
    "No inventes datos que no estén en el contexto."
)


def openai_settings() -> dict[str, str]:
    load_dotenv(ROOT / ".env", override=True)
    # Acepta OPENROUTER_API_KEY o, como respaldo, OPENAI_API_KEY (API compatible).
    key = (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    base = (os.getenv("OPENAI_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/") or DEFAULT_BASE_URL
    return {
        "key": key,
        "model": (os.getenv("OPENAI_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        "url": f"{base}/chat/completions",
    }


def _env_int(name: str, default: int) -> int:
    try:
        value = int((os.getenv(name) or "").strip())
        return value if value > 0 else default
    except (TypeError, ValueError):
        return default


def is_configured() -> bool:
    return bool(openai_settings()["key"])


def ai_chat(messages: list[dict[str, Any]], context: dict[str, Any] | None = None) -> str:
    settings = openai_settings()
    if not settings["key"]:
        raise ValueError("Falta OPENROUTER_API_KEY en .env. Añádela para activar el copiloto IA.")

    # owl-alpha (stealth) tiene una ventana de contexto pequena (~4k tokens
    # input+output). Recortamos snapshot e historial para no superarla; los
    # limites son configurables por si se cambia a un modelo mas grande.
    snapshot_chars = _env_int("AI_SNAPSHOT_CHARS", 6000)
    history_turns = _env_int("AI_HISTORY_TURNS", 8)
    history_chars = _env_int("AI_HISTORY_CHARS", 1500)
    max_tokens = _env_int("AI_MAX_TOKENS", 600)

    system = SYSTEM_PROMPT
    if context:
        snapshot = json.dumps(context, ensure_ascii=False, default=str)[:snapshot_chars]
        system += "\n\n=== SNAPSHOT DEL MERCADO ACTIVO (tiempo real de la terminal) ===\n" + snapshot

    convo: list[dict[str, str]] = [{"role": "system", "content": system}]
    for message in messages[-history_turns:]:
        role = message.get("role")
        content = str(message.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            convo.append({"role": role, "content": content[:history_chars]})
    if len(convo) == 1:
        raise ValueError("No hay ningún mensaje del usuario para el copiloto IA")

    payload = {
        "model": settings["model"],
        "messages": convo,
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {settings['key']}",
        "Content-Type": "application/json",
        # Opcionales de OpenRouter (atribución/ranking); no afectan a la respuesta.
        "HTTP-Referer": "https://riu-revenue-terminal.local",
        "X-Title": "RIU Revenue Terminal",
    }
    with httpx.Client(timeout=60) as client:
        response = client.post(settings["url"], headers=headers, json=payload)

    if response.status_code >= 400:
        try:
            detail = response.json().get("error", {}).get("message") or response.text[:300]
        except Exception:  # noqa: BLE001
            detail = response.text[:300]
        raise RuntimeError(f"OpenRouter {response.status_code}: {detail}")

    data = response.json()
    return ((data.get("choices") or [{}])[0].get("message", {}) or {}).get("content", "").strip()
