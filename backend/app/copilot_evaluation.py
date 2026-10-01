"""Banco de evaluación offline para el enrutamiento de Revenue Copilot.

No llama a proveedores ni usa credenciales. Protege el contrato local que
decide qué modelo interviene y cuándo una decisión debe quedarse bloqueada por
calidad de datos.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from typing import Any

from .assistant import assistant_data_gate
from .config import OpenRouterSettings
from .copilot_gateway import route_request, select_model


@dataclass(frozen=True)
class CopilotEvaluationCase:
    case_id: str
    message: str
    mode: str
    expected_model: str
    expected_strategy: str
    expected_aggregation: str
    expected_experts: tuple[str, ...]


EVALUATION_CASES: tuple[CopilotEvaluationCase, ...] = (
    CopilotEvaluationCase(
        "quick_market_adr",
        "¿Cuál es el ADR medio del mercado?",
        "quick",
        "fast_model",
        "single_expert",
        "direct",
        ("hotel_revenue",),
    ),
    CopilotEvaluationCase(
        "quick_hotel_price",
        "Dime la tarifa observada del hotel RIU Palace Maspalomas.",
        "quick",
        "fast_model",
        "single_expert",
        "direct",
        ("hotel_revenue",),
    ),
    CopilotEvaluationCase(
        "air_market_analysis",
        "Compara la conectividad aérea y los vuelos por mercado emisor.",
        "analysis",
        "air_model",
        "expert_panel",
        "single_call_synthesis",
        ("air_access", "data_quality"),
    ),
    CopilotEvaluationCase(
        "hotel_pricing_decision",
        "¿Puedo subir la tarifa del hotel esta semana?",
        "decision",
        "synthesis_model",
        "expert_panel",
        "multi_call_synthesis",
        ("hotel_revenue", "market_checker", "data_quality"),
    ),
    CopilotEvaluationCase(
        "air_pricing_decision",
        "¿Debo mantener el precio ante la conectividad aérea de Londres?",
        "decision",
        "synthesis_model",
        "expert_panel",
        "multi_call_synthesis",
        ("hotel_revenue", "air_access", "data_quality"),
    ),
)


DECISION_GATE_CASES: tuple[tuple[str, dict[str, Any], bool], ...] = (
    (
        "fresh_matched_context",
        {
            "zonaActiva": {"id": 1, "name": "Gran Canaria"},
            "riu": {"hoteles": [{"nombre": "RIU"}]},
            "calidadAnalisis": {
                "estado": "actualizado",
                "comparabilidadPct": 100,
                "comparacion": {"estado": "matched", "coberturaPct": 100},
            },
        },
        True,
    ),
    (
        "stale_context",
        {
            "zonaActiva": {"id": 1, "name": "Gran Canaria"},
            "riu": {"hoteles": [{"nombre": "RIU"}]},
            "calidadAnalisis": {"estado": "caducado", "comparabilidadPct": 100},
        },
        False,
    ),
    (
        "unmatched_context",
        {
            "zonaActiva": {"id": 1, "name": "Gran Canaria"},
            "riu": {"hoteles": [{"nombre": "RIU"}]},
            "calidadAnalisis": {
                "estado": "actualizado",
                "comparabilidadPct": 100,
                "comparacion": {"estado": "unmatched", "coberturaPct": 0},
            },
        },
        False,
    ),
)


def run_routing_evaluation(settings: OpenRouterSettings) -> list[dict[str, Any]]:
    """Devuelve resultados serializables para CI o revisión de cambios de routing."""
    results: list[dict[str, Any]] = []
    for case in EVALUATION_CASES:
        plan = select_model(route_request(case.message, case.mode), settings)
        expected_model = getattr(settings, case.expected_model)
        passed = (
            plan["model"] == expected_model
            and plan["strategy"] == case.expected_strategy
            and plan["aggregation"] == case.expected_aggregation
            and tuple(plan["experts"]) == case.expected_experts
        )
        results.append(
            {
                "id": case.case_id,
                "passed": passed,
                "model": plan["model"],
                "strategy": plan["strategy"],
                "aggregation": plan["aggregation"],
                "experts": plan["experts"],
            }
        )
    return results


def run_data_gate_evaluation() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case_id, context, expected_permission in DECISION_GATE_CASES:
        gate = assistant_data_gate(context, mode="decision")
        results.append(
            {
                "id": case_id,
                "passed": gate["canRecommend"] is expected_permission,
                "canRecommend": gate["canRecommend"],
                "severity": gate["severity"],
                "warnings": gate["warnings"],
            }
        )
    return results


def run_evaluation(settings: OpenRouterSettings) -> dict[str, Any]:
    routing = run_routing_evaluation(settings)
    data_gate = run_data_gate_evaluation()
    passed = all(item["passed"] for item in [*routing, *data_gate])
    return {"passed": passed, "routing": routing, "dataGate": data_gate}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa el routing y los controles locales de Revenue Copilot.")
    parser.add_argument("--record", action="store_true", help="Guarda el resultado técnico en SQLite, sin contenido de respuestas.")
    args = parser.parse_args()
    from .config import load_settings
    from .database import Database

    runtime = load_settings(require_decodo=False)
    result = run_evaluation(runtime.openrouter)
    if args.record:
        result["profile"] = "offline"
        record = Database(runtime.sqlite_path).record_copilot_evaluation(
            result, source="offline_contract", provider_live=False
        )
        result["record"] = record
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
