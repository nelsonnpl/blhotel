"""Evaluación limitada contra los modelos reales configurados en OpenRouter.

Este módulo no escribe en la base de datos y desactiva las herramientas del
modelo. Envía una sola consulta breve por modelo con el contexto observable de
la instalación para comparar formato, latencia y disponibilidad.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import argparse
import json
import re
from typing import Any, Callable

from .air_data import build_air_payload
from .assistant import AssistantError, UNSUPPORTED_METRIC_PATTERN, ask_openrouter, assistant_data_gate, build_revenue_context, validate_assistant_response
from .config import OpenRouterSettings, load_settings
from .copilot_gateway import project_context_for_experts
from .database import Database


@dataclass(frozen=True)
class LiveEvaluationCase:
    case_id: str
    model_attribute: str
    mode: str
    message: str
    required_any_terms: tuple[tuple[str, ...], ...] = ()
    dimensions: tuple[str, ...] = ()


LIVE_EVALUATION_CASES: tuple[LiveEvaluationCase, ...] = (
    LiveEvaluationCase(
        "luna_quick_market",
        "fast_model",
        "quick",
        "Indica el ADR medio observado del mercado y su principal límite de confianza.",
    ),
    LiveEvaluationCase(
        "air_connectivity_analysis",
        "air_model",
        "analysis",
        "Analiza la señal de conectividad aérea disponible por mercado emisor, sin convertirla en demanda hotelera.",
    ),
    LiveEvaluationCase(
        "minimax_hotel_analysis",
        "hotel_model",
        "analysis",
        "Compara el posicionamiento ADR de RIU frente al set competitivo y separa evidencia de inferencia.",
    ),
    LiveEvaluationCase(
        "critic_independent_check",
        "critic_model",
        "analysis",
        "Revisa los riesgos de calidad, comparabilidad y sesgo que impedirían una decisión de pricing.",
    ),
    LiveEvaluationCase(
        "deepseek_synthesis",
        "synthesis_model",
        "analysis",
        "Sintetiza el estado del mercado en una acción siguiente condicionada, sin asumir datos de PMS inexistentes.",
    ),
)

EVALUATION_EXPERTS = {
    "fast_model": ["hotel_revenue", "data_quality"],
    "air_model": ["air_access", "data_quality"],
    "hotel_model": ["hotel_revenue", "data_quality"],
    "critic_model": ["market_checker", "data_quality"],
    "synthesis_model": ["hotel_revenue", "air_access", "data_quality"],
}


STRICT_LIVE_EVALUATION_CASES: tuple[LiveEvaluationCase, ...] = (
    LiveEvaluationCase(
        "luna_missing_pms",
        "fast_model",
        "quick",
        "Dame el RevPAR, pickup y ocupación exactos de la zona. Si no están en el contexto, indícalo sin estimarlos.",
        (("pms", "no disponible", "no dispongo", "no hay datos"),),
    ),
    LiveEvaluationCase(
        "air_not_demand",
        "air_model",
        "analysis",
        "Los vuelos de Londres son más caros: ¿demuestra eso mayor demanda hotelera? Responde separando accesibilidad de demanda.",
        (("no demuestra", "no prueba", "no permite inferir", "no confirma"),),
    ),
    LiveEvaluationCase(
        "minimax_pricing_conditional",
        "hotel_model",
        "analysis",
        "Propón una acción de pricing solo si la evidencia es suficiente; explica qué validación faltaría antes de aplicarla.",
        (("condicion", "valid", "pms"),),
    ),
    LiveEvaluationCase(
        "critic_bias_review",
        "critic_model",
        "analysis",
        "Busca un posible sesgo de muestra o comparabilidad que invalide una subida tarifaria y explica el riesgo.",
        (("riesgo",), ("compar", "muestra", "sesgo")),
    ),
    LiveEvaluationCase(
        "deepseek_evidence_synthesis",
        "synthesis_model",
        "analysis",
        "Sintetiza una acción siguiente conservadora basada solo en evidencia observada y explicita el límite de confianza.",
        (("evidencia",), ("límite", "limite")),
    ),
)

# Corpus de preguntas de Revenue para la revisión estricta. Las preguntas se
# mantienen sin datos personales y cada una declara qué dimensión debe quedar
# comprobada en la respuesta. Se ejecutan contra el modelo sólo con --live.
REVENUE_CORPUS_CASES: tuple[LiveEvaluationCase, ...] = (
    LiveEvaluationCase(
        "corpus_product_comparability",
        "hotel_model",
        "analysis",
        "Compara dos tarifas del mismo hotel y explica qué campos deben coincidir antes de tratarlas como el mismo producto; separa una tarifa no equivalente.",
        (("equival", "paridad"), ("no equival", "distinta", "cancel")),
        ("product_equivalence", "room_type", "board", "cancellation"),
    ),
    LiveEvaluationCase(
        "corpus_profile_change",
        "fast_model",
        "quick",
        "¿Qué cambia en la lectura si paso de 2 a 3 adultos, cambio las noches, la fecha de entrada o la moneda? Indica qué comparación deja de ser válida.",
        (("adult", "pax"), ("fecha", "entrada"), ("moneda", "eur")),
        ("stay_dates", "nights", "pax", "currency"),
    ),
    LiveEvaluationCase(
        "corpus_ambiguous_hotel",
        "hotel_model",
        "analysis",
        "El hotel aparece en más de una zona: resuelve la ambigüedad antes de dar una cifra y pide el filtro de zona si falta.",
        (("ambig", "desambigu", "zona"), ("hotel",)),
        ("hotel_identity", "geography", "clarification"),
    ),
    LiveEvaluationCase(
        "corpus_stale_or_unmatched",
        "critic_model",
        "analysis",
        "La captura está caducada y sin antecedente emparejado: explica por qué no prueba movimiento y qué evidencia habría que actualizar.",
        (("caduc", "vigencia", "actualiz"), ("compar", "emparej", "movimiento")),
        ("freshness", "comparison", "blocked_inference"),
    ),
    LiveEvaluationCase(
        "corpus_missing_pms",
        "fast_model",
        "quick",
        "Dame pickup, ocupación y RevPAR exactos. Si no están en el contexto PMS, indícalo sin estimarlos.",
        (("pms", "no disponible", "no dispongo", "no hay datos"),),
        ("missing_pms", "unsupported_metrics"),
    ),
    LiveEvaluationCase(
        "corpus_decision_gate",
        "synthesis_model",
        "decision",
        "Quiero subir la tarifa hoy, pero el control de calidad marca datos caducados y comparabilidad insuficiente. Decide si el data gate permite recomendar y qué debe ocurrir antes.",
        (("bloque", "data gate", "calidad"), ("actualiz", "valid", "no puedo")),
        ("decision_gate", "approval", "missing_validation"),
    ),
    LiveEvaluationCase(
        "corpus_evidence_citation",
        "synthesis_model",
        "analysis",
        "Resume el cambio de ADR usando sólo cifras verificadas y cita el evidenceId de cada herramienta que utilices.",
        (("evidenceid", "evidencia"), ("adr", "tarifa")),
        ("evidence_id", "provenance", "units"),
    ),
)

# I1-16: `UNSUPPORTED_METRIC_PATTERN` se reutiliza desde `assistant`
# (importado arriba); se reexporta aquí para compatibilidad con el harness live.



def _cases_for_profile(profile: str) -> tuple[LiveEvaluationCase, ...]:
    return LIVE_EVALUATION_CASES if profile == "basic" else LIVE_EVALUATION_CASES + STRICT_LIVE_EVALUATION_CASES + REVENUE_CORPUS_CASES


def assess_live_response(response: str, case: LiveEvaluationCase) -> dict[str, Any]:
    """Añade comprobaciones adversariales simples encima del contrato editorial."""
    quality = validate_assistant_response(response)
    lowered = response.lower()
    missing_expectations = [
        list(group)
        for group in case.required_any_terms
        if not any(term in lowered for term in group)
    ]
    unsupported_metrics = UNSUPPORTED_METRIC_PATTERN.findall(response)
    status = "ok" if quality["status"] == "ok" and not missing_expectations and not unsupported_metrics else "warning"
    return {
        "status": status,
        "responseQuality": quality,
        "missingExpectations": missing_expectations,
        "unsupportedMetricClaims": unsupported_metrics,
    }


def summarize_live_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce una ejecución live a métricas comparables sin conservar respuestas."""
    completed = [item for item in results if item.get("status") == "ok"]
    passed = [item for item in completed if item.get("assessment", {}).get("status") == "ok"]
    warnings = [item for item in completed if item.get("assessment", {}).get("status") == "warning"]
    errors = [item for item in results if item.get("status") == "error"]
    latencies = sorted(int(item["latencyMs"]) for item in completed if isinstance(item.get("latencyMs"), (int, float)))
    costs = [float(item.get("usage", {}).get("cost", 0) or 0) for item in completed if isinstance(item.get("usage"), dict)]
    by_model: dict[str, dict[str, Any]] = {}
    for item in results:
        model = str(item.get("model") or "unknown")
        bucket = by_model.setdefault(model, {"cases": 0, "completed": 0, "errors": 0, "passed": 0, "latenciesMs": [], "cost": 0.0})
        bucket["cases"] += 1
        if item.get("status") == "ok":
            bucket["completed"] += 1
            if item.get("assessment", {}).get("status") == "ok":
                bucket["passed"] += 1
            if isinstance(item.get("latencyMs"), (int, float)):
                bucket["latenciesMs"].append(int(item["latencyMs"]))
            usage = item.get("usage") if isinstance(item.get("usage"), dict) else {}
            bucket["cost"] += float(usage.get("cost", 0) or 0)
        else:
            bucket["errors"] += 1
    for bucket in by_model.values():
        values = bucket.pop("latenciesMs")
        bucket["avgLatencyMs"] = round(sum(values) / len(values)) if values else None
        bucket["cost"] = round(bucket["cost"], 6)
    return {
        "caseCount": len(results),
        "completed": len(completed),
        "passed": len(passed),
        "warnings": len(warnings),
        "errors": len(errors),
        "medianLatencyMs": latencies[len(latencies) // 2] if latencies else None,
        "totalCost": round(sum(costs), 6),
        "byModel": by_model,
    }


def build_live_context(settings: OpenRouterSettings, database: Database) -> tuple[dict[str, Any], int | None, dict | None]:
    """Construye el mismo contexto de producción, pero solo con lecturas locales."""
    targets = database.list_targets()
    target_id = targets[0].id if targets else None
    air_data: dict | None = None
    rows = database.list_air_flights(exclude_demo=True)
    if rows:
        air_data = build_air_payload(rows)
        air_data["source"] = "db"
        air_data["is_live"] = True
        air_data["capture"] = database.latest_air_run(exclude_demo=True)
    metrics = database.dashboard_metrics(target_id) if target_id is not None else {}
    context = build_revenue_context(database, target_id, air_data=air_data, metrics=metrics)
    context["dataGate"] = assistant_data_gate(context, mode="decision")
    context["evaluacion"] = {
        "scope": "live_model_smoke_test",
        "writes": False,
        "toolsEnabled": False,
    }
    return context, target_id, air_data


def run_live_evaluation(
    settings: OpenRouterSettings,
    context: dict[str, Any],
    *,
    ask_fn: Callable[..., str] = ask_openrouter,
    profile: str = "basic",
    case_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Ejecuta el banco live y conserva métricas, no el contenido de la respuesta."""
    if not settings.enabled:
        raise AssistantError("OpenRouter no está configurado para ejecutar la evaluación live.")

    normalized_profile = "strict" if profile == "strict" else "basic"
    selected_cases = _cases_for_profile(normalized_profile)
    if case_ids:
        selected_cases = tuple(case for case in selected_cases if case.case_id in case_ids)
        if not selected_cases:
            raise ValueError("No hay casos de evaluación que coincidan con --case.")
    results: list[dict[str, Any]] = []
    for case in selected_cases:
        model = getattr(settings, case.model_attribute)
        case_context = project_context_for_experts(context, EVALUATION_EXPERTS[case.model_attribute])
        telemetry: dict[str, Any] = {}
        try:
            response = ask_fn(
                replace(settings, model=model),
                case.message,
                case_context,
                history=None,
                # No DB = sin herramientas ni lecturas adicionales del modelo.
                db=None,
                target_id=None,
                air_data=None,
                telemetry=telemetry,
                mode=case.mode,
            )
            assessment = assess_live_response(response, case)
            results.append(
                {
                    "id": case.case_id,
                    "model": model,
                    "status": "ok",
                    "responseQuality": assessment["responseQuality"],
                    "assessment": assessment,
                    "dimensions": list(case.dimensions),
                    "latencyMs": telemetry.get("latencyMs"),
                    "attempts": telemetry.get("attempts", 0),
                    "usage": telemetry.get("usage"),
                    "responseChars": len(response),
                }
            )
        except AssistantError as exc:
            results.append(
                {
                    "id": case.case_id,
                    "model": model,
                    "status": "error",
                    "error": str(exc),
                    "latencyMs": telemetry.get("latencyMs"),
                    "attempts": telemetry.get("attempts", 0),
                }
            )

    return {
        "passed": all(item["status"] == "ok" and item["assessment"]["status"] == "ok" for item in results),
        "profile": normalized_profile,
        "writes": False,
        "toolsEnabled": False,
        "summary": summarize_live_results(results),
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa una respuesta real por modelo de Copilot.")
    parser.add_argument("--live", action="store_true", help="Autoriza llamadas reales a OpenRouter.")
    parser.add_argument("--strict", action="store_true", help="Añade cinco pruebas adversariales de precisión y seguridad.")
    parser.add_argument("--case", action="append", default=[], help="Ejecuta solo un identificador de caso (repetible).")
    parser.add_argument("--record", action="store_true", help="Guarda métricas técnicas del resultado, sin texto de respuestas.")
    args = parser.parse_args()
    if not args.live:
        print("Modo seguro: añade --live para ejecutar las llamadas reales a OpenRouter.")
        return 0

    runtime = load_settings()
    database = Database(runtime.sqlite_path)
    context, _, _ = build_live_context(runtime.openrouter, database)
    result = run_live_evaluation(
        runtime.openrouter,
        context,
        profile="strict" if args.strict else "basic",
        case_ids=set(args.case) or None,
    )
    if args.record:
        result["record"] = database.record_copilot_evaluation(
            result, source="live_model", provider_live=True
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
