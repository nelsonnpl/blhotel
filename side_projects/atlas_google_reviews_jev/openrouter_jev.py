from __future__ import annotations

from contextlib import contextmanager
import os
from typing import Any, Iterator


TYPESAFE_DECISIONS_URL = "https://api.typesafe.ai/v1/systemone"
OPENROUTER_DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_OPENROUTER_JEV_MODEL = "typesafe/jev-1.13"


class JevBudgetExceeded(RuntimeError):
    """The configured decision or estimated spend cap stopped navigation."""


@contextmanager
def route_jev_through_openrouter(
    model_module: Any,
    *,
    budget_usd: float | None = None,
    estimated_decision_cost_usd: float | None = None,
    max_decisions: int | None = None,
    usage: dict[str, Any] | None = None,
    openrouter_api_key: str | None = None,
) -> Iterator[None]:
    """Temporarily route Jev Ultrafast's TypeSafe decision calls via OpenRouter.

    Jev Ultrafast currently hardcodes the TypeSafe URL and expects its API key
    before calling ``post_json``. Its decision request/response schema is
    compatible with OpenRouter's Jev Decisions endpoint, so this small adapter
    rewrites only that request. Other calls (such as the optional text helper)
    keep their own configured endpoint.

    I1-13: la clave viaja por argumento/env del hijo (`openrouter_api_key` o
    `OPENROUTER_API_KEY` del hijo) y nunca se muta `os.environ` global: el
    padre la inyecta solo en el env del hijo (ver `flask_app._jev_child_env`)
    y aquí solo se usa en el cierre `routed_post_json`.
    """

    api_key = (openrouter_api_key or os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("ATLAS_JEV_PROVIDER=openrouter requiere OPENROUTER_API_KEY.")

    original_post_json = model_module.post_json
    model_name = os.environ.get("ATLAS_JEV_OPENROUTER_MODEL", DEFAULT_OPENROUTER_JEV_MODEL)
    usage = usage if usage is not None else {}
    usage.setdefault("decisions", 0)
    usage.setdefault("reportedCostUsd", 0.0)
    usage.setdefault("estimatedCostUsd", 0.0)
    unit_estimate = max(0.0, float(estimated_decision_cost_usd or 0.0))
    hard_estimate_cap = None if budget_usd is None else float(budget_usd)
    if hard_estimate_cap is not None and hard_estimate_cap <= 0:
        raise ValueError("El presupuesto Jev debe ser mayor que cero.")
    if hard_estimate_cap is not None and unit_estimate <= 0:
        raise ValueError("Configura una estimación positiva por decisión para aplicar el presupuesto Jev.")
    hard_decision_cap = max(0, int(max_decisions or 0))

    def routed_post_json(url: str, key: str, body: dict[str, Any]) -> dict[str, Any]:
        if url != TYPESAFE_DECISIONS_URL:
            return original_post_json(url, key, body)
        if hard_decision_cap and int(usage["decisions"]) >= hard_decision_cap:
            raise JevBudgetExceeded("Se alcanzó el máximo de decisiones Jev configurado para este hotel.")
        next_estimate = float(usage.get("reportedCostUsd", 0)) + float(usage.get("estimatedCostUsd", 0)) + unit_estimate
        if hard_estimate_cap is not None and next_estimate > hard_estimate_cap:
            raise JevBudgetExceeded("Se alcanzó el presupuesto estimado para las decisiones Jev.")
        request_body = {**body, "model": model_name}
        result = original_post_json(OPENROUTER_DECISIONS_URL, api_key, request_body)
        usage["decisions"] = int(usage["decisions"]) + 1
        billed = result.get("usage", {}).get("cost") if isinstance(result, dict) and isinstance(result.get("usage"), dict) else None
        try:
            billed = max(0.0, float(billed)) if billed is not None else None
        except (TypeError, ValueError):
            billed = None
        if billed is not None:
            usage["reportedCostUsd"] = round(float(usage["reportedCostUsd"]) + billed, 8)
            if float(usage["estimatedCostUsd"]):
                usage["costBasis"] = "mixed"
            else:
                usage["costBasis"] = "provider_reported"
            if hard_estimate_cap is not None and (
                float(usage["reportedCostUsd"]) + float(usage["estimatedCostUsd"])
            ) > hard_estimate_cap:
                # The provider's reported charge can exceed the operator's
                # estimate for this call. Never make another decision then.
                usage["budgetExceededByProviderCost"] = True
        else:
            usage["estimatedCostUsd"] = round(float(usage["estimatedCostUsd"]) + unit_estimate, 8)
            usage["costBasis"] = (
                "mixed" if float(usage["reportedCostUsd"]) else
                "configured_estimate" if unit_estimate else "unavailable"
            )
        return result

    model_module.post_json = routed_post_json
    try:
        yield
    finally:
        model_module.post_json = original_post_json
