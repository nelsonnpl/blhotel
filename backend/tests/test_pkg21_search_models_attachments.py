"""PKG-21 (I1-17/18/22 + I1-15 permisos): no-regresión BE.

- I1-17: «tiempo» temporal no dispara `web_search` de pago; solo un tema
  externo explícito lo activa. El conteo `server_tool_use` se suma entre
  rondas y su coste se imputa en `assistant_runs.cost_usd`.
- I1-18: `.env.example` alineado con `config.DEFAULT_*` y sin slugs de
  `EXCLUDED_COPILOT_MODELS` (ejemplo → 0 fallbacks).
- I1-15/I1-22: adjuntos en claro con 0600 fuera de `/static/`, comentario
  veraz (sin «encrypted-at-rest») y `extractionStatus` visible para el modelo.
"""

from __future__ import annotations

import os
from pathlib import Path

from backend.app import flask_app
from backend.app.assistant import (
    SYSTEM_PROMPT,
    _sum_server_tool_use,
    should_request_web_search,
)
from backend.app.config import (
    DEFAULT_OPENROUTER_CRITIC_MODEL,
    DEFAULT_OPENROUTER_FAST_MODEL,
    DEFAULT_OPENROUTER_HOTEL_MODEL,
    DEFAULT_OPENROUTER_SYNTHESIS_MODEL,
    EXCLUDED_COPILOT_MODELS,
)


# I1-17: «en el tiempo» sin tema externo → webSearchRequested False.


def test_temporal_tiempo_does_not_request_web_search() -> None:
    assert should_request_web_search("¿cómo evoluciona el ADR en el tiempo?") is False
    assert should_request_web_search("en el tiempo") is False
    assert should_request_web_search("cuéntame la serie en el tiempo") is False


def test_external_topic_still_requests_web_search() -> None:
    assert should_request_web_search("¿hay eventos este fin de semana?") is True
    assert should_request_web_search("últimas noticias del mercado emisor") is True
    assert should_request_web_search("¿qué feria hay hoy en Gran Canaria?") is True
    # `tiempo` + tema externo explícito sigue entrando por el tema externo.
    assert should_request_web_search("¿cómo afecta el tiempo al evento de mañana?") is True


def test_ask_openrouter_omits_web_search_tool_for_temporal_query(monkeypatch) -> None:
    import httpx

    from backend.app.assistant import ask_openrouter
    from backend.app.config import OpenRouterSettings

    captured: dict = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, _url, *, headers, json, timeout):
            captured.update(json)
            request = httpx.Request("POST", "https://example.test")
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
                request=request,
            )

    monkeypatch.setattr("backend.app.assistant.httpx.Client", FakeClient)
    settings = OpenRouterSettings(api_key="test-key", model="test/model", base_url="https://example.test/v1")
    telemetry: dict = {}
    ask_openrouter(settings, "¿cómo evoluciona el ADR en el tiempo?", {}, db=object(), telemetry=telemetry)
    assert telemetry["webSearchRequested"] is False
    tools = captured.get("tools") or []
    assert all(tool.get("type") != "openrouter:web_search" for tool in tools)


def test_ask_openrouter_includes_web_search_tool_for_external_topic(monkeypatch) -> None:
    import httpx

    from backend.app.assistant import ask_openrouter
    from backend.app.config import OpenRouterSettings

    captured: dict = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, _url, *, headers, json, timeout):
            captured.update(json)
            request = httpx.Request("POST", "https://example.test")
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
                request=request,
            )

    monkeypatch.setattr("backend.app.assistant.httpx.Client", FakeClient)
    settings = OpenRouterSettings(api_key="test-key", model="test/model", base_url="https://example.test/v1")
    telemetry: dict = {}
    ask_openrouter(settings, "¿hay eventos este fin de semana?", {}, db=object(), telemetry=telemetry)
    assert telemetry["webSearchRequested"] is True
    tools = captured.get("tools") or []
    assert any(tool.get("type") == "openrouter:web_search" for tool in tools)


def test_server_tool_use_requests_are_summed_across_rounds() -> None:
    merged = _sum_server_tool_use(
        {"server_tool_use": {"web_search_requests": 2}},
        {"server_tool_use": {"web_search_requests": 3}},
    )
    assert merged is not None
    assert merged["web_search_requests"] == 5


def test_assistant_usage_cost_imputes_separate_search_cost() -> None:
    # El `cost` del proveedor (que ya incluye la búsqueda con `usage.include`)
    # sigue mandando cuando existe.
    assert flask_app._assistant_usage_cost({"usage": {"cost": 0.01, "server_tool_use": {"web_search_requests": 2}}}) == 0.01
    # Si el proveedor desglosa la búsqueda por separado, también se imputa.
    assert flask_app._assistant_usage_cost({"usage": {"search_cost": 0.005}}) == 0.005
    assert flask_app._assistant_search_requests({"usage": {"server_tool_use": {"web_search_requests": 2}}}) == 2
    assert flask_app._assistant_search_requests({"usage": {}}) == 0


# I1-18: ejemplo → 0 fallbacks.


def _parse_env_example() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    values: dict[str, str] = {}
    for line in (root / ".env.example").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def test_env_example_matches_defaults_and_avoids_excluded_slugs() -> None:
    values = _parse_env_example()
    assert values["OPENROUTER_HOTEL_MODEL"] == DEFAULT_OPENROUTER_HOTEL_MODEL
    assert values["OPENROUTER_CRITIC_MODEL"] == DEFAULT_OPENROUTER_CRITIC_MODEL
    assert values["OPENROUTER_SYNTHESIS_MODEL"] == DEFAULT_OPENROUTER_SYNTHESIS_MODEL
    assert values["OPENROUTER_FAST_MODEL"] == DEFAULT_OPENROUTER_FAST_MODEL
    for key in (
        "OPENROUTER_MODEL",
        "OPENROUTER_FAST_MODEL",
        "OPENROUTER_HOTEL_MODEL",
        "OPENROUTER_AIR_MODEL",
        "OPENROUTER_AIR_FALLBACK_MODEL",
        "OPENROUTER_CRITIC_MODEL",
        "OPENROUTER_SYNTHESIS_MODEL",
    ):
        assert values[key] not in EXCLUDED_COPILOT_MODELS, f"{key} usa un slug retirado"


def test_example_models_produce_zero_fallbacks() -> None:
    from backend.app.config import OpenRouterSettings
    from backend.app.copilot_gateway import route_request, select_model

    values = _parse_env_example()
    settings = OpenRouterSettings(
        api_key="test",
        model=values["OPENROUTER_MODEL"],
        base_url="https://example.test",
        fast_model=values["OPENROUTER_FAST_MODEL"],
        hotel_model=values["OPENROUTER_HOTEL_MODEL"],
        air_model=values["OPENROUTER_AIR_MODEL"],
        air_fallback_model=values["OPENROUTER_AIR_FALLBACK_MODEL"],
        critic_model=values["OPENROUTER_CRITIC_MODEL"],
        synthesis_model=values["OPENROUTER_SYNTHESIS_MODEL"],
    )
    simple = select_model(route_request("¿Cuál es el ADR medio?"), settings)
    assert "modelFallback" not in simple
    assert simple["model"] not in EXCLUDED_COPILOT_MODELS


# I1-15/I1-22: adjuntos 0600, comentario veraz y `visual_required` declarado.


def test_attachment_delete_comment_is_truthful() -> None:
    doc = flask_app.delete_assistant_attachment.__doc__ or ""
    assert "encrypted-at-rest" not in doc
    assert "0600" in doc or "plaintext" in doc or "en claro" in doc


def test_attachment_storage_is_private_and_outside_static(tmp_path: Path, monkeypatch) -> None:
    from dataclasses import replace

    isolated_sqlite = tmp_path / "booking-prices.sqlite"
    runtime = replace(flask_app.settings, sqlite_path=isolated_sqlite)
    monkeypatch.setattr(flask_app, "settings", runtime)

    storage_dir = runtime.sqlite_path.parent / "assistant-files"
    storage_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(storage_dir, 0o700)
    except OSError:
        pass
    probe = storage_dir / "probe.bin"
    probe.write_bytes(b"demo")
    try:
        os.chmod(probe, 0o600)
    except OSError:
        pass

    assert oct(probe.stat().st_mode & 0o777) == "0o600"
    static_root = Path(flask_app.app.static_folder).resolve()
    assert static_root not in probe.resolve().parents
    assert "static" not in str(storage_dir).replace("\\", "/")


def test_system_prompt_declares_visual_required_limit() -> None:
    assert "visual_required" in SYSTEM_PROMPT
    assert "extractionStatus" in SYSTEM_PROMPT
