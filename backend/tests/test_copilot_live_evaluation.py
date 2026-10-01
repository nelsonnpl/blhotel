from backend.app.config import OpenRouterSettings
from backend.app.copilot_live_evaluation import (
    LIVE_EVALUATION_CASES,
    REVENUE_CORPUS_CASES,
    STRICT_LIVE_EVALUATION_CASES,
    assess_live_response,
    run_live_evaluation,
    summarize_live_results,
)


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(api_key="test", model="legacy", base_url="https://example.test")


def test_live_evaluation_uses_each_configured_model_without_tools() -> None:
    calls = []

    def fake_ask(settings, message, context, **kwargs):
        calls.append((settings.model, kwargs["db"], kwargs["mode"], message))
        kwargs["telemetry"].update({"latencyMs": 4, "attempts": 1, "usage": {"total_tokens": 12}})
        return "**Lectura**\nOK\n**Evidencia**\nOK\n**Acción siguiente**\nOK\n**Límite de confianza**\nOK"

    result = run_live_evaluation(_settings(), {"zonaActiva": {"id": 1}}, ask_fn=fake_ask)

    assert result["passed"] is True
    assert len(calls) == len(LIVE_EVALUATION_CASES)
    assert all(db is None for _, db, _, _ in calls)
    assert [model for model, _, _, _ in calls] == [
        "openai/gpt-5.6-luna",
        "z-ai/glm-5.3-flash",
        "minimax/minimax-m3",
        "google/gemini-3.8-flash",
        "deepseek/deepseek-v4-pro-0813",
    ]


def test_live_evaluation_keeps_other_model_results_when_one_fails() -> None:
    def fake_ask(settings, message, _context, **_kwargs):
        if "riesgos de calidad" in message:
            from backend.app.assistant import AssistantError

            raise AssistantError("critic unavailable")
        return "**Lectura**\nOK\n**Evidencia**\nOK\n**Acción siguiente**\nOK\n**Límite de confianza**\nOK"

    result = run_live_evaluation(_settings(), {}, ask_fn=fake_ask)

    assert result["passed"] is False
    assert next(item for item in result["cases"] if item["id"] == "critic_independent_check")["status"] == "error"
    assert sum(item["status"] == "ok" for item in result["cases"]) == len(LIVE_EVALUATION_CASES) - 1


def test_revenue_corpus_is_versioned_across_the_seven_required_dimensions() -> None:
    ids = {case.case_id for case in REVENUE_CORPUS_CASES}
    dimensions = {dimension for case in REVENUE_CORPUS_CASES for dimension in case.dimensions}

    assert len(REVENUE_CORPUS_CASES) == 7
    assert len(ids) == 7
    assert {"product_equivalence", "stay_dates", "nights", "pax", "currency"} <= dimensions
    assert {"hotel_identity", "freshness", "comparison", "missing_pms", "decision_gate", "evidence_id"} <= dimensions
    assert all(case.mode in {"quick", "analysis", "decision"} for case in REVENUE_CORPUS_CASES)


def test_strict_cases_keep_a_valid_mode_after_manifest_changes() -> None:
    assert all(case.mode in {"quick", "analysis", "decision"} for case in STRICT_LIVE_EVALUATION_CASES)


def test_live_summary_aggregates_latency_cost_and_provider_errors_without_text() -> None:
    summary = summarize_live_results(
        [
            {"id": "ok", "model": "luna", "status": "ok", "latencyMs": 100, "assessment": {"status": "ok"}, "usage": {"cost": 0.25}},
            {"id": "warning", "model": "luna", "status": "ok", "latencyMs": 300, "assessment": {"status": "warning"}, "usage": {"cost": 0.15}},
            {"id": "error", "model": "glm", "status": "error", "error": "timeout"},
        ]
    )

    assert summary == {
        "caseCount": 3,
        "completed": 2,
        "passed": 1,
        "warnings": 1,
        "errors": 1,
        "medianLatencyMs": 300,
        "totalCost": 0.4,
        "byModel": {
            "luna": {"cases": 2, "completed": 2, "errors": 0, "passed": 1, "avgLatencyMs": 200, "cost": 0.4},
            "glm": {"cases": 1, "completed": 0, "errors": 1, "passed": 0, "avgLatencyMs": None, "cost": 0.0},
        },
    }


def test_strict_live_evaluation_checks_adversarial_expectations() -> None:
    response = (
        "**Lectura**\nNo hay datos PMS. La comparación exige hotel y zona; una tarifa equivalente debe conservar producto, habitación, régimen y cancelación, y una no equivalente no se puede emparejar.\n"
        "El cambio de fecha de entrada, noches, adultos o moneda rompe la comparación. La captura está caducada y la comparabilidad no demuestra movimiento. El data gate bloquea la decisión.\n"
        "**Evidencia**\nLa conectividad no demuestra demanda y existe riesgo de sesgo de muestra. La evidencia y el evidenceId deben acompañar cada ADR o tarifa.\n"
        "**Acción siguiente**\nDesambiguar el hotel y la zona, actualizar la captura, validar antes de una acción condicionada y pedir el filtro que falta.\n"
        "**Límite de confianza**\nLímite por comparabilidad, vigencia, moneda y ausencia de PMS."
    )

    result = run_live_evaluation(_settings(), {}, ask_fn=lambda *_args, **_kwargs: response, profile="strict")

    assert result["profile"] == "strict"
    assert result["passed"] is True
    assert len(result["cases"]) == len(LIVE_EVALUATION_CASES) + len(STRICT_LIVE_EVALUATION_CASES) + len(REVENUE_CORPUS_CASES)


def test_live_assessment_flags_unsupported_pms_metric() -> None:
    assessment = assess_live_response(
        "**Lectura**\nOcupación 85%.\n**Evidencia**\nOK\n**Acción siguiente**\nOK\n**Límite de confianza**\nOK",
        STRICT_LIVE_EVALUATION_CASES[0],
    )

    assert assessment["status"] == "warning"
    assert assessment["unsupportedMetricClaims"]
