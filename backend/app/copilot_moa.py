"""Orquestación MoA acotada para decisiones de Revenue.

El router decide cuándo merece la pena pagar el coste de un panel. Este módulo
solo se ejecuta en decisiones que han superado el data gate: dos lecturas
independientes en paralelo y una tercera llamada de síntesis. La calidad de
los datos no se delega al LLM; se adjunta como resultado determinista.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
import logging
import time
from typing import Any

from .assistant import AssistantError, ask_openrouter
from .config import (
    DEFAULT_OPENROUTER_AIR_MODEL,
    DEFAULT_OPENROUTER_CRITIC_MODEL,
    DEFAULT_OPENROUTER_FAST_MODEL,
    DEFAULT_OPENROUTER_HOTEL_MODEL,
    DEFAULT_OPENROUTER_SYNTHESIS_MODEL,
    OpenRouterSettings,
    safe_copilot_model,
)
from .copilot_gateway import project_context_for_experts
from .database import Database

logger = logging.getLogger(__name__)

MOA_EXPERT_TIMEOUT_SECONDS = 12.0
MOA_AIR_PRIMARY_TIMEOUT_SECONDS = 8.0
MOA_AIR_FALLBACK_TIMEOUT_SECONDS = 10.0
MOA_SYNTHESIS_TIMEOUT_SECONDS = 12.0
MAX_EXPERT_RESPONSE_CHARS = 7000

EXPERT_INSTRUCTIONS = {
    "hotel_revenue": (
        "Eres el experto principal de revenue hotelero. Analiza ADR, posición competitiva, "
        "regimenes y evolución observada. Formula una propuesta condicionada y separa hechos "
        "de inferencias. No inventes ocupación, pickup ni PMS."
    ),
    "air_access": (
        "Eres el experto de conectividad aérea. Valora mercados emisores, rutas, frecuencia, "
        "precio y fricción de acceso. Usa estas señales solo como contexto de accesibilidad, "
        "nunca como prueba de demanda hotelera."
    ),
    "market_checker": (
        "Eres un revisor independiente de mercado. Busca sesgos, comparaciones no equivalentes, "
        "muestras insuficientes y conclusiones demasiado tajantes. Comprueba que cada propuesta "
        "está respaldada por la evidencia disponible."
    ),
}


def _expert_prompt(expert: str, original_message: str) -> str:
    instruction = EXPERT_INSTRUCTIONS.get(expert, "Analiza la consulta con rigor y usa solo la evidencia disponible.")
    return (
        f"PANEL MoA · ROL: {expert}\n{instruction}\n\n"
        "Entrega un informe interno breve para otro modelo. Incluye: hallazgos verificables, "
        "riesgos o faltantes y una propuesta condicionada. No menciones que eres un sistema "
        "interno ni generes gráficos.\n\n"
        f"CONSULTA ORIGINAL:\n{original_message}"
    )


def _quality_brief(context: dict[str, Any]) -> dict[str, Any]:
    """Extrae solo el control local que debe conocer el sintetizador."""
    return {
        "calidadAnalisis": context.get("calidadAnalisis"),
        "dataGate": context.get("dataGate"),
        "evidenceCount": len((context.get("evidencia") or {}).get("records") or []),
    }


def _sum_usage(telemetries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Suma los contadores de uso sin asumir que todos los proveedores devuelven lo mismo."""
    totals: dict[str, Any] = {}
    for item in telemetries:
        usage = item.get("usage") if isinstance(item, dict) else None
        if not isinstance(usage, dict):
            continue
        for key, value in usage.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[key] = totals.get(key, 0) + value
            elif key not in totals:
                totals[key] = value
    return totals or None


def _aggregate_telemetry(telemetry: dict[str, Any], reports: list[dict[str, Any]], synthesis: dict[str, Any]) -> None:
    """Expone una única contabilidad del panel al endpoint y a dataMeta."""
    all_telemetries = [report.get("telemetry", {}) for report in reports]
    all_telemetries.append(synthesis)
    for field in ("attempts", "toolRounds", "toolCalls", "toolErrors"):
        telemetry[field] = sum(int(item.get(field, 0) or 0) for item in all_telemetries)
    # Keep the trace useful to the operator without copying tool arguments or
    # model prompts into the response metadata.
    telemetry["toolNames"] = list(dict.fromkeys(
        name
        for item in all_telemetries
        for name in (item.get("toolNames") or [])
        if isinstance(name, str) and name
    ))
    telemetry["toolEvidenceIds"] = list(dict.fromkeys(
        evidence_id
        for item in all_telemetries
        for evidence_id in (item.get("toolEvidenceIds") or [])
        if isinstance(evidence_id, str) and evidence_id
    ))
    evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in all_telemetries:
        for ref in item.get("toolEvidence") or []:
            if not isinstance(ref, dict) or not ref.get("evidenceId") or ref["evidenceId"] in seen:
                continue
            seen.add(ref["evidenceId"])
            evidence.append({
                "evidenceId": ref["evidenceId"],
                "tool": ref.get("tool"),
                "queriedAt": ref.get("queriedAt"),
                "sourceObservedAt": ref.get("sourceObservedAt"),
            })
    telemetry["toolEvidence"] = evidence
    telemetry["usage"] = _sum_usage(all_telemetries)
    telemetry["contextChars"] = synthesis.get("contextChars", 0)
    telemetry["historyTurns"] = synthesis.get("historyTurns", 0)


def run_moa(
    settings: OpenRouterSettings,
    message: str,
    context: dict[str, Any],
    history: list[dict[str, str]] | None = None,
    *,
    db: Database | None = None,
    target_id: int | None = None,
    air_data: dict | None = None,
    mode: str = "decision",
    experts: list[str] | None = None,
    telemetry: dict[str, Any] | None = None,
    on_progress: Any = None,
) -> str:
    """Ejecuta expertos en paralelo y sintetiza sus informes.

    Los errores de un experto quedan aislados. Si queda un informe válido se
    intenta sintetizar; si falla la síntesis, se entrega el mejor informe como
    respuesta degradada. Si fallan todos, se propaga ``AssistantError`` para
    que el endpoint pueda devolver el error estándar.

    I1-19: ``on_progress(pct, mensaje)`` es opcional y solo publica fases
    (0-100 del panel) para que el job async no quede mudo en decisiones
    >60 s. El progreso es consultable vía ``GET /api/assistant/jobs/<id>``.
    Nunca altera el resultado ni genera llamadas de pago extra.
    """
    def _emit(pct: int, message: str) -> None:
        if on_progress is None:
            return
        try:
            on_progress(max(0, min(100, int(pct))), str(message)[:300])
        except Exception:
            logger.debug("MoA on_progress ignorado", exc_info=True)

    started = time.monotonic()
    telemetry = telemetry if telemetry is not None else {}
    settings = replace(
        settings,
        model=safe_copilot_model(settings.model, DEFAULT_OPENROUTER_FAST_MODEL),
        fast_model=safe_copilot_model(settings.fast_model, DEFAULT_OPENROUTER_FAST_MODEL),
        hotel_model=safe_copilot_model(settings.hotel_model, DEFAULT_OPENROUTER_HOTEL_MODEL),
        air_model=safe_copilot_model(settings.air_model, DEFAULT_OPENROUTER_AIR_MODEL),
        air_fallback_model=safe_copilot_model(settings.air_fallback_model, DEFAULT_OPENROUTER_FAST_MODEL),
        critic_model=safe_copilot_model(settings.critic_model, DEFAULT_OPENROUTER_CRITIC_MODEL),
        synthesis_model=safe_copilot_model(settings.synthesis_model, DEFAULT_OPENROUTER_SYNTHESIS_MODEL),
    )
    selected = [name for name in (experts or []) if name in EXPERT_INSTRUCTIONS]
    if not selected:
        raise AssistantError("El panel MoA no tiene expertos configurados.")

    # El control de calidad es determinista y no genera una llamada adicional.
    llm_experts = [name for name in selected if name != "data_quality"]
    telemetry["moa"] = {
        "enabled": True,
        "executed": True,
        "experts": selected,
        "llmExperts": llm_experts,
        "qualityCheck": _quality_brief(context),
        "expertCalls": 0,
        "failedExperts": [],
        "synthesisModel": settings.synthesis_model,
    }
    if not llm_experts:
        raise AssistantError("El panel MoA solo contiene control de calidad y no puede sintetizar.")

    reports: list[dict[str, Any]] = []

    def ask_expert(expert: str) -> dict[str, Any]:
        expert_telemetry: dict[str, Any] = {"requestId": f"moa-{expert}-{time.time_ns()}"}
        expert_settings = replace(
            settings,
            model=(settings.hotel_model if expert == "hotel_revenue" else
                   settings.air_model if expert == "air_access" else
                   settings.critic_model),
        )
        expert_context = project_context_for_experts(context, [expert, "data_quality"])
        primary_budget = MOA_AIR_PRIMARY_TIMEOUT_SECONDS if expert == "air_access" else MOA_EXPERT_TIMEOUT_SECONDS
        try:
            response = ask_openrouter(
                expert_settings,
                _expert_prompt(expert, message),
                expert_context,
                history=(history or [])[-4:],
                db=db,
                target_id=target_id,
                air_data=air_data,
                telemetry=expert_telemetry,
                mode=mode,
                budget_seconds=primary_budget,
            )
            return {
                "expert": expert,
                "model": expert_settings.model,
                "response": response[:MAX_EXPERT_RESPONSE_CHARS],
                "telemetry": expert_telemetry,
            }
        except AssistantError as exc:
            if expert == "air_access" and settings.air_fallback_model != settings.air_model:
                fallback_settings = replace(settings, model=settings.air_fallback_model)
                try:
                    response = ask_openrouter(
                        fallback_settings,
                        _expert_prompt(expert, message),
                        expert_context,
                        history=(history or [])[-4:],
                        db=db,
                        target_id=target_id,
                        air_data=air_data,
                        telemetry=expert_telemetry,
                        mode=mode,
                        budget_seconds=MOA_AIR_FALLBACK_TIMEOUT_SECONDS,
                    )
                    return {
                        "expert": expert,
                        "model": fallback_settings.model,
                        "response": response[:MAX_EXPERT_RESPONSE_CHARS],
                        "fallback": {"from": settings.air_model, "to": fallback_settings.model, "reason": str(exc)},
                        "telemetry": expert_telemetry,
                    }
                except AssistantError as fallback_error:
                    return {
                        "expert": expert,
                        "model": fallback_settings.model,
                        "error": str(fallback_error),
                        "fallback": {"from": settings.air_model, "to": fallback_settings.model, "reason": str(exc)},
                        "telemetry": expert_telemetry,
                    }
            return {
                "expert": expert,
                "model": expert_settings.model,
                "error": str(exc),
                "telemetry": expert_telemetry,
            }
        except Exception as exc:  # noqa: BLE001 - un experto no debe tumbar el panel completo
            logger.warning("MoA expert %s failed unexpectedly: %s", expert, type(exc).__name__)
            return {
                "expert": expert,
                "model": expert_settings.model,
                "error": "fallo inesperado del experto",
                "telemetry": expert_telemetry,
            }

    max_workers = min(2, len(llm_experts))
    _emit(5, f"Panel MoA: lanzando {len(llm_experts)} expertos")
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="copilot-moa") as pool:
        futures = [pool.submit(ask_expert, expert) for expert in llm_experts]
        done = 0
        for future in as_completed(futures):
            report = future.result()
            reports.append(report)
            done += 1
            # 10-70: expertos; mensaje con fase consultable vía job async.
            _emit(10 + int(done * 60 / max(1, len(llm_experts))), f"MoA: experto {done}/{len(llm_experts)} listo")

    reports.sort(key=lambda report: llm_experts.index(report["expert"]))
    successful = [report for report in reports if report.get("response")]
    failed = [report for report in reports if not report.get("response")]
    telemetry["moa"]["expertCalls"] = len(reports)
    telemetry["moa"]["failedExperts"] = [report["expert"] for report in failed]
    telemetry["moa"]["successfulExperts"] = [report["expert"] for report in successful]
    telemetry["moa"]["expertUsage"] = [report.get("telemetry", {}).get("usage") for report in reports]
    telemetry["moa"]["airFallbacks"] = [report["fallback"] for report in reports if report.get("fallback")]

    if not successful:
        raise AssistantError("No se pudo obtener ningún informe del panel MoA.")

    panel_context = {
        **project_context_for_experts(context, selected),
        "moaPanel": {
            "qualityCheck": _quality_brief(context),
            "reports": [
                {
                    "expert": report["expert"],
                    "model": report["model"],
                    "response": report["response"],
                }
                for report in successful
            ],
            "failedExperts": [report["expert"] for report in failed],
        },
    }
    synthesis_prompt = (
        "Eres el sintetizador final de un panel MoA de Revenue. Responde a la consulta original "
        "usando únicamente CONTEXTO y los informes del panel. Contrasta los informes, resuelve "
        "discrepancias con la evidencia y no menciones el proceso interno ni nombres de modelos. "
        "Conserva exactamente los cuatro bloques: Lectura, Evidencia, Acción siguiente y Límite "
        "de confianza. Si faltó un experto, indícalo como limitación.\n\n"
        f"CONSULTA ORIGINAL:\n{message}"
    )
    synthesis_telemetry: dict[str, Any] = {}
    _emit(75, "MoA: sintetizando informes")
    try:
        response = ask_openrouter(
            replace(settings, model=settings.synthesis_model),
            synthesis_prompt,
            panel_context,
            history=(history or [])[-4:],
            telemetry=synthesis_telemetry,
            mode=mode,
            budget_seconds=MOA_SYNTHESIS_TIMEOUT_SECONDS,
        )
        telemetry["moa"]["synthesis"] = {
            "status": "success",
            "usage": synthesis_telemetry.get("usage"),
            "latencyMs": synthesis_telemetry.get("latencyMs"),
        }
        _aggregate_telemetry(telemetry, reports, synthesis_telemetry)
        telemetry["model"] = settings.synthesis_model
        telemetry["moa"]["latencyMs"] = round((time.monotonic() - started) * 1000)
        _emit(95, "MoA: síntesis completada")
        return response
    except AssistantError as exc:
        # La respuesta del experto conserva valor si la última llamada agota
        # presupuesto o falla por rate-limit.
        telemetry["moa"]["synthesis"] = {"status": "degraded", "error": str(exc)}
        _aggregate_telemetry(telemetry, reports, synthesis_telemetry)
        telemetry["model"] = successful[0]["model"]
        telemetry["moa"]["latencyMs"] = round((time.monotonic() - started) * 1000)
        telemetry["outcome"] = "degraded"
        _emit(95, "MoA: respuesta degradada (síntesis no disponible)")
        return successful[0]["response"]
