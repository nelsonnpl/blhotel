"""Routing local y barato para Revenue Copilot.

La selección de expertos es determinista y auditable. Las consultas rápidas
usan una única llamada; las decisiones complejas se entregan al orquestador MoA.
"""

from __future__ import annotations

import json
from typing import Any
import unicodedata

from .copilot_contracts import RoutingPlan
from .config import (
    DEFAULT_OPENROUTER_CRITIC_MODEL,
    DEFAULT_OPENROUTER_FAST_MODEL,
    DEFAULT_OPENROUTER_HOTEL_MODEL,
    DEFAULT_OPENROUTER_SYNTHESIS_MODEL,
    EXCLUDED_COPILOT_MODELS,
    OpenRouterSettings,
)

MAX_EXPERT_CONTEXT_CHARS = 24000
_OPTIONAL_CONTEXT_SECTIONS = (
    "calidadDatos", "estabilidadCompetitiva", "curvaAdrObservada", "oportunidadesRevenue",
    "rankingCompetitivo", "demanda", "mercado", "riu", "contextoExterno",
)


def _context_chars(value: dict[str, Any]) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str))


def _shrink_section(value: Any, limit: int = 6) -> Any:
    """Recorta listas de presentación manteniendo metadatos y forma del payload."""
    if isinstance(value, list):
        return value[:limit]
    if isinstance(value, dict):
        return {
            key: (_shrink_section(item, limit) if isinstance(item, (list, dict)) else item)
            for key, item in value.items()
        }
    return value


def _bound_expert_context(result: dict[str, Any]) -> dict[str, Any]:
    """Aplica un techo global para que una consulta no desborde el contexto del modelo."""
    if _context_chars(result) <= MAX_EXPERT_CONTEXT_CHARS:
        return result
    bounded = dict(result)
    for key in _OPTIONAL_CONTEXT_SECTIONS:
        if key in bounded:
            bounded[key] = _shrink_section(bounded[key])
            if _context_chars(bounded) <= MAX_EXPERT_CONTEXT_CHARS:
                break
    omitted: list[str] = []
    for key in _OPTIONAL_CONTEXT_SECTIONS:
        if _context_chars(bounded) <= MAX_EXPERT_CONTEXT_CHARS:
            break
        if key in bounded:
            bounded.pop(key)
            omitted.append(key)
    bounded["contextoRecortado"] = {
        "maxChars": MAX_EXPERT_CONTEXT_CHARS,
        "seccionesOmitidas": omitted,
    }
    return bounded


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "")
    return "".join(char for char in folded if not unicodedata.combining(char)).lower()


def _compact_air_signals(value: dict[str, Any]) -> dict[str, Any]:
    """Conserva las rutas representativas sin reenviar el payload aéreo completo."""
    routes = value.get("rutas") or []
    compact_routes = [
        {
            key: route.get(key)
            for key in (
                "mercado", "origen", "destino", "precioMin", "precioMedio", "rangoTipico",
                "gapVsTipicoPct", "opciones", "aerolineas", "directoPct", "salida",
                "diasAntelacion", "nivel", "riesgo",
            )
        }
        for route in routes[:8]
        if isinstance(route, dict)
    ]
    return {
        "resumen": value.get("resumen"),
        "captura": value.get("captura"),
        "notaSemantica": value.get("notaSemantica"),
        "rutas": compact_routes,
        "rutasRecortadas": max(0, len(routes) - len(compact_routes)),
    }


def _compact_evidence(value: dict[str, Any], entities: set[str]) -> dict[str, Any]:
    records = value.get("records") or []
    compact = []
    for record in records:
        if not isinstance(record, dict) or record.get("entityType") not in entities:
            continue
        compact.append(
            {
                key: record.get(key)
                for key in (
                    "evidenceId", "metric", "entityType", "entityId", "targetId", "value", "unit",
                    "period", "sourceId", "datasetId", "observedAt", "snapshotId", "quality",
                    "comparability", "calculation",
                )
            }
        )
    return {"schemaVersion": value.get("schemaVersion"), "records": compact[:24]}


def project_context_for_experts(context: dict[str, Any], experts: list[str] | tuple[str, ...]) -> dict[str, Any]:
    """Minimiza contexto por dominio, conservando trazabilidad y control de calidad.

    El contexto completo se guarda para la aplicación; esta proyección solo es
    el paquete que viaja a un modelo. Los datos que no lleguen siguen pudiendo
    consultarse por herramienta durante un chat normal.
    """
    domains = set(experts)
    needs_hotel = "hotel_revenue" in domains or "market_checker" in domains
    needs_air = "air_access" in domains
    result: dict[str, Any] = {
        key: context.get(key)
        for key in ("zonaActiva", "calidadAnalisis", "dataGate", "orquestacion")
        if context.get(key) is not None
    }
    evidence_entities = {"capture", "data_quality"}
    if needs_hotel:
        for key in (
            "mercado", "demanda", "riu", "rankingCompetitivo", "oportunidadesRevenue",
            "estabilidadCompetitiva", "curvaAdrObservada", "calidadDatos", "contextoExterno",
        ):
            if context.get(key) is not None:
                result[key] = context[key]
        evidence_entities.update({"market", "hotel", "external"})
    if needs_air and isinstance(context.get("senalesAereas"), dict):
        result["senalesAereas"] = _compact_air_signals(context["senalesAereas"])
        evidence_entities.add("route")
    if isinstance(context.get("evidencia"), dict):
        result["evidencia"] = _compact_evidence(context["evidencia"], evidence_entities)
    # Los adjuntos ya llegan extraídos y redactados por el backend. Se
    # conservan en la proyección para que el modelo pueda responder sobre el
    # archivo, con un límite por documento para no desplazar la evidencia de
    # las fotos fuera de la ventana de contexto.
    attachments = context.get("adjuntos") or []
    if isinstance(attachments, list):
        result["adjuntos"] = [
            {
                "id": item.get("id"),
                "filename": item.get("filename"),
                "mediaType": item.get("mediaType"),
                "extractionStatus": item.get("extractionStatus"),
                "text": str(item.get("text") or "")[:30000],
            }
            for item in attachments[:5]
            if isinstance(item, dict)
        ]
    return _bound_expert_context(result)


def route_request(
    message: str,
    requested_mode: str = "quick",
    history: list[dict[str, str]] | None = None,
) -> dict:
    """Devuelve un plan reproducible sin consultar al modelo ni a la red.

    Solo se incorporan mensajes previos del usuario para resolver seguimientos
    (por ejemplo, «compáralo con la anterior») sin dejar que una frase
    generada por el modelo cambie el ámbito del enrutado.
    """
    mode = requested_mode if requested_mode in {"quick", "auto", "analysis", "decision"} else "auto"
    prior_user_messages = [
        str(turn.get("content") or "")
        for turn in (history or [])[-6:]
        if isinstance(turn, dict) and turn.get("role") == "user" and turn.get("content")
    ]
    query = _normalize(" ".join([*prior_user_messages, message]))
    hotel_terms = ("hotel", "adr", "tarifa", "precio", "competidor", "mercado", "habitacion", "booking")
    air_terms = ("vuelo", "aereo", "aerea", "aeropuerto", "ruta", "conectividad", "aerolinea", "origen", "iata")
    quality_terms = ("captura", "comparab", "vigencia", "dato", "evidencia", "pms", "ocupacion", "pickup", "revpar", "compara", "diferencia")
    decision_terms = ("subir", "bajar", "mantener", "recomienda", "recomendacion", "decidir", "pricing", "precio optimo")

    wants_hotel = any(term in query for term in hotel_terms if term != "mercado") or (
        "mercado" in query and "emisor" not in query and "aereo" not in query
    )
    wants_air = any(term in query for term in air_terms)
    wants_quality = any(term in query for term in quality_terms)
    wants_decision = mode == "decision" or any(term in query for term in decision_terms)

    experts: list[str] = []
    if wants_hotel or not wants_air:
        experts.append("hotel_revenue")
    if wants_air:
        experts.append("air_access")
    if wants_decision:
        # Segunda lectura independiente para reducir el riesgo de anclaje del
        # experto principal. La comprobación de calidad sigue siendo local.
        experts.append("market_checker")
    if wants_quality or wants_decision or len(experts) > 1:
        experts.append("data_quality")

    # Keep stable order and the bounded expert set required by RoutingPlan.
    # Si confluyen hotel, conectividad y decisión hay cuatro señales posibles.
    # El control de calidad es obligatorio para pricing, por lo que se conserva
    # y se omite el revisor genérico: ya quedan dos lecturas de dominio.
    experts = list(dict.fromkeys(experts))
    if len(experts) > 3 and "data_quality" in experts:
        experts = [expert for expert in experts if expert != "market_checker"]
    experts = experts[:3]
    complexity = "simple" if len(experts) == 1 and not wants_decision else ("complex" if wants_decision or len(experts) == 3 else "multi_signal")
    strategy = "single_expert" if len(experts) == 1 else "expert_panel"
    aggregation = "direct" if len(experts) == 1 else ("multi_call_synthesis" if wants_decision else "single_call_synthesis")
    reason = "Consulta focalizada en un dominio." if len(experts) == 1 else (
        "Decisión compleja: panel independiente y síntesis final." if wants_decision
        else "Combina señales de revenue y control de calidad."
    )

    return RoutingPlan(
        requestedMode=mode,
        complexity=complexity,
        strategy=strategy,
        experts=experts,
        aggregation=aggregation,
        requiresRecommendation=wants_decision,
        reason=reason,
    ).model_dump()


def select_model(
    plan: dict,
    settings: OpenRouterSettings,
    *,
    capabilities: dict[str, Any] | None = None,
) -> dict:
    """Asigna el modelo adecuado al plan sin consultar al proveedor.

    La elección se basa en la tarea resuelta y las capacidades necesarias. El
    modo legado sólo modifica la longitud de la respuesta en el prompt; nunca
    rebaja una tarea compleja a un modelo rápido.
    """
    experts = set(plan.get("experts") or [])
    capabilities = capabilities or {}
    # Visual/document inputs need multimodal support even for a short question.
    if capabilities.get("hasAttachments") or capabilities.get("needsVision"):
        model = settings.critic_model
        selection_reason = "La consulta incluye archivos o requiere interpretación visual."
    elif plan.get("complexity") == "complex":
        model = settings.synthesis_model
        selection_reason = "La consulta cruza varias señales y necesita síntesis razonada."
    elif "air_access" in experts and "hotel_revenue" not in experts and "market_checker" not in experts:
        model = settings.air_model
        selection_reason = "La consulta está focalizada en conectividad aérea."
    elif plan.get("complexity") == "multi_signal" or len(experts) > 1:
        model = settings.hotel_model
        selection_reason = "La consulta combina señales y requiere análisis con herramientas."
    else:
        model = settings.fast_model
        selection_reason = "La consulta es acotada y puede resolverse con una respuesta directa."

    # Prevent old expensive slugs from entering through an independently
    # constructed settings object (tests, workers or stale process state).
    if model in EXCLUDED_COPILOT_MODELS:
        replacements = {
            settings.synthesis_model: DEFAULT_OPENROUTER_SYNTHESIS_MODEL,
            settings.critic_model: DEFAULT_OPENROUTER_CRITIC_MODEL,
            settings.hotel_model: DEFAULT_OPENROUTER_HOTEL_MODEL,
            settings.fast_model: DEFAULT_OPENROUTER_FAST_MODEL,
        }
        model = replacements.get(model, DEFAULT_OPENROUTER_FAST_MODEL)
        selection_reason += " Se aplicó el modelo económico configurado para este rol."
    return RoutingPlan.model_validate({
        **plan,
        "model": model,
        "selectionReason": selection_reason,
    }).model_dump()
