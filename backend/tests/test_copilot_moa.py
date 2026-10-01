from backend.app import copilot_moa
from backend.app.assistant import AssistantError
from backend.app.config import OpenRouterSettings


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(api_key="test", model="legacy", base_url="https://example.test")


def _context() -> dict:
    return {
        "zonaActiva": {"id": 2, "name": "Gran Canaria"},
        "calidadAnalisis": {"estado": "vigente", "comparabilidadPct": 100},
        "evidencia": {"records": [{"metric": "adr", "quality": "verified"}]},
    }


def test_moa_calls_two_llm_experts_in_parallel_and_synthesizes(monkeypatch) -> None:
    calls = []

    def fake_ask(settings, message, context, **kwargs):
        calls.append((settings.model, context.get("moaPanel")))
        kwargs["telemetry"].update({
            "usage": {"total_tokens": 10},
            "latencyMs": 1,
            "attempts": 1,
            "toolNames": ["historial_precio_hotel"] if settings.model != settings.synthesis_model else ["listar_competidores"],
        })
        return "síntesis final" if settings.model == settings.synthesis_model else f"informe {settings.model}"

    monkeypatch.setattr(copilot_moa, "ask_openrouter", fake_ask)
    telemetry = {}

    result = copilot_moa.run_moa(
        _settings(),
        "¿Puedo subir el precio?",
        _context(),
        experts=["hotel_revenue", "market_checker", "data_quality"],
        telemetry=telemetry,
    )

    assert result == "síntesis final"
    assert sorted(model for model, _ in calls[:2]) == [
        "google/gemini-3.8-flash",
        "minimax/minimax-m3",
    ]
    assert calls[2][0] == "deepseek/deepseek-v4-pro-0813"
    assert telemetry["moa"]["successfulExperts"] == ["hotel_revenue", "market_checker"]
    assert telemetry["moa"]["synthesis"]["status"] == "success"
    assert telemetry["attempts"] == 3
    assert telemetry["usage"]["total_tokens"] == 30
    assert telemetry["toolNames"] == ["historial_precio_hotel", "listar_competidores"]


def test_moa_isolates_failed_expert_and_keeps_synthesis(monkeypatch) -> None:
    def fake_ask(settings, message, context, **kwargs):
        if settings.model == "google/gemini-3.8-flash":
            raise AssistantError("critic no disponible")
        return "respuesta sintetizada" if settings.model == "deepseek/deepseek-v4-pro-0813" else "informe revenue"

    monkeypatch.setattr(copilot_moa, "ask_openrouter", fake_ask)
    telemetry = {}

    result = copilot_moa.run_moa(
        _settings(),
        "¿Puedo subir el precio?",
        _context(),
        experts=["hotel_revenue", "market_checker", "data_quality"],
        telemetry=telemetry,
    )

    assert result == "respuesta sintetizada"
    assert telemetry["moa"]["failedExperts"] == ["market_checker"]
    assert telemetry["moa"]["synthesis"]["status"] == "success"


def test_moa_returns_expert_when_synthesis_fails(monkeypatch) -> None:
    def fake_ask(settings, message, context, **kwargs):
        if settings.model == "deepseek/deepseek-v4-pro-0813":
            raise AssistantError("síntesis agotada")
        return "informe de respaldo"

    monkeypatch.setattr(copilot_moa, "ask_openrouter", fake_ask)
    telemetry = {}

    result = copilot_moa.run_moa(
        _settings(),
        "¿Puedo subir el precio?",
        _context(),
        experts=["hotel_revenue", "data_quality"],
        telemetry=telemetry,
    )

    assert result == "informe de respaldo"
    assert telemetry["outcome"] == "degraded"
    assert telemetry["moa"]["synthesis"]["status"] == "degraded"


def test_moa_air_expert_falls_back_to_luna_when_glm_fails(monkeypatch) -> None:
    calls = []

    def fake_ask(settings, _message, _context, **_kwargs):
        calls.append(settings.model)
        if settings.model == "z-ai/glm-5.3-flash":
            raise AssistantError("GLM no respondió")
        return "síntesis" if settings.model == "deepseek/deepseek-v4-pro-0813" else "informe aéreo de respaldo"

    monkeypatch.setattr(copilot_moa, "ask_openrouter", fake_ask)
    telemetry = {}

    result = copilot_moa.run_moa(
        _settings(),
        "¿Debo cambiar precio por conectividad aérea?",
        _context(),
        experts=["air_access", "data_quality"],
        telemetry=telemetry,
    )

    assert result == "síntesis"
    assert calls == ["z-ai/glm-5.3-flash", "openai/gpt-5.6-luna", "deepseek/deepseek-v4-pro-0813"]
    assert telemetry["moa"]["airFallbacks"][0]["to"] == "openai/gpt-5.6-luna"
