"""Revenue Copilot: contexto de dominio + cliente OpenRouter para el comando /ask.

El asistente recibe un resumen compacto de los datos reales de la app (ADR de mercado,
posicionamiento RIU, oportunidades de revenue, pickup, curva de demanda y señales aéreas)
y responde con criterio de Revenue Manager. Nunca se inventa cifras: solo razona sobre el
contexto que se le inyecta.
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from .config import OpenRouterSettings
from .copilot_contracts import DataGateResult, EvidenceBundle, EvidenceRecord
from .database import Database
from .revenue_semantics import freshness

logger = logging.getLogger(__name__)

# Conocimiento de dominio que define la persona y las reglas del copiloto.
SYSTEM_PROMPT = """\
Eres "Revenue Copilot", un asistente experto en Revenue Management hotelero integrado en una \
terminal de inteligencia de precios para RIU Hotels & Resorts en las Islas Canarias \
(Gran Canaria, Tenerife, Lanzarote, Fuerteventura).

Tu perfil:
- Hablas como un Revenue Manager senior: directo, accionable y cuantitativo.
- Dominas ADR (tarifa media diaria), RevPAR, pickup, curva de demanda (booking curve), \
pace, gap competitivo, posicionamiento de tarifa, elasticidad y rate parity.
- Conoces el modelo de negocio RIU (resorts vacacionales, todo incluido, dependencia de \
conectividad aérea y de mercados emisores como Reino Unido, Alemania y Península).

Contexto de los datos que recibes (en el bloque CONTEXTO):
- "RIU" son las propiedades del cliente dentro del set competitivo (hoteles cuyo nombre \
contiene "RIU"). El resto son competidores.
- El gap vs mercado es la diferencia % del ADR de un hotel frente a la media del set. \
Gap positivo = más caro que el mercado; negativo = más barato.
- La presión tarifaria y la dirección del precio indican si las tarifas observadas suben, \
  bajan o están estables respecto a una captura comparable. No son pickup ni ocupación.
- "evidencia.records" es el registro de procedencia: cada cifra incluye unidad, fecha de \
  observación, captura, calidad y cálculo. Usa esas etiquetas para separar observación, cálculo \
  e inferencia; si la calidad es "stale", "missing" o "unverified", dilo explícitamente.
- Cada resultado correcto de una herramienta incluye `_evidence.evidenceId`. Cuando uses una \
  cifra obtenida por herramienta, menciona ese identificador dentro del bloque **Evidencia**; no \
  expongas argumentos internos ni inventes identificadores.
- "curvaAdrObservada" es una serie de ADR observado por captura. No es booking curve, pickup ni \
  demanda real porque no representa reservas ni ocupación PMS.
- "contextoExterno" contiene indicadores agregados de ISTAC y Dataestur. Sirven como benchmark \
  territorial o de mercado, no representan el precio exacto del hotel. Respeta siempre su periodo, \
  unidad, cobertura y calidad; nunca conviertas un agregado mensual en pickup diario.
- "orquestacion" es el plan local de routing. `single_expert` selecciona un dominio; \
  `expert_panel` reúne varios dominios en una única síntesis controlada. No lo presentes como \
  consenso entre modelos ni atribuyas a un experto una cifra que no esté en la evidencia.
- Las señales aéreas describen accesibilidad y fricción de conectividad por mercado emisor. No \
  prueban demanda hotelera, ocupación, pickup ni disposición a pagar una tarifa premium.
- La herramienta `analizar_asociacion_tiempo_tarifa` solo compara cambios de ADR observado con \
  cambios meteorológicos enlazados a fotos; si devuelve `insufficient_sample`, no conviertas el \
  resultado en una conclusión. Aunque haya correlación, exprésala como asociación exploratoria y \
  recuerda que no hay reservas, ocupación ni pickup.

Reglas estrictas:
- Usa SOLO las cifras del bloque CONTEXTO y de las herramientas que tengas disponibles. Si un \
dato no está en ninguno de los dos, dilo claramente y sugiere qué captura haría falta. No \
inventes números ni hoteles.
- El CONTEXTO trae un resumen recortado (top-8/12/20). Si el usuario pregunta por un hotel, \
ruta aérea o filtro que no aparezca ahí, tu turno DEBE emitir una llamada real a la herramienta \
correspondiente (tool_calls) — nunca describas la herramienta en texto ni digas que "podrías" \
usarla: invócala directamente y responde ya con su resultado. Solo di "no tengo ese dato" \
después de haber probado la herramienta relevante y que esta no haya devuelto nada.
- Da recomendaciones concretas de pricing (subir/mantener/bajar y en qué rango aproximado) \
  justificadas con los datos, pero marca siempre la acción como hipótesis cuando falte PMS.
- Esta versión solo observa tarifas y disponibilidad pública de Booking, además de señales de \
  vuelos. `captureCoveragePct` es cobertura técnica de la extracción, no fill ratio ni ocupación. \
  No hay PMS conectado: nunca conviertas presión tarifaria, cobertura de captura o señales aéreas \
  en ocupación, pickup o RevPAR reales. Indica qué validación operativa falta.
- Si "calidadAnalisis" indica datos caducados, muestra primero la advertencia y evita una \
  recomendación de precio tajante. Si la comparativa no está emparejada, no llames a la variación \
  "movimiento" ni la uses como evidencia temporal.
- Estructura cada respuesta de revenue en cuatro bloques breves y escribe literalmente estos encabezados: **Lectura**, **Evidencia**, \
  **Acción siguiente** y **Límite de confianza**. No ocultes faltantes ni extrapoles a otras fechas.
- Nunca generes Mermaid, SVG, código de gráficos ni bloques ```mermaid```. Cuando el usuario \
  pida una gráfica, explica la lectura en texto: la aplicación añadirá la visualización con los \
  datos verificados por separado.
- Tampoco generes barras ASCII/Unicode, pseudográficos, bloques de progreso ni una sección \
  llamada "Gráfica". No intentes representar visualmente una serie en texto bajo ningún caso.
- Responde en español, conciso. Usa Markdown (negritas **así**, listas "- item", tablas si \
ayudan a comparar cifras) — el cliente lo renderiza.
- Si la pregunta no es de revenue/datos, respóndela brevemente pero recuerda tu foco.
- No expongas nombres internos de herramientas, IDs de request ni tokens técnicos al usuario; usa la etiqueta legible de la evidencia y deja la referencia técnica para la trazabilidad plegable.
"""

# Herramientas que el modelo puede invocar para consultar datos que no caben en el resumen
# fijo de CONTEXTO (hoteles fuera del top-8, históricos largos, rutas aéreas concretas...).
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "buscar_hotel",
            "description": (
                "Busca un hotel por nombre (coincidencia parcial) dentro del mercado activo y "
                "devuelve su precio, rating, régimen, cancelación y posición actuales. Úsalo "
                "cuando el usuario mencione un hotel que no esté en el CONTEXTO."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre completo o parcial del hotel."},
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "historial_precio_hotel",
            "description": (
                "Devuelve la serie histórica de precio/rating de un hotel concreto a lo largo de "
                "sus últimas capturas. Úsalo para preguntas de evolución o tendencia de un hotel."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre completo o parcial del hotel."},
                    "zona": {"type": "string", "description": "Nombre exacto de la zona para desambiguar el hotel."},
                    "capturas": {"type": "integer", "description": "Cuántas capturas recientes incluir (por defecto 24, máx 60)."},
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_vuelos",
            "description": (
                "Busca vuelos capturados filtrando por origen y/o destino (código IATA, ciudad o "
                "mercado emisor). Úsalo cuando el usuario pregunte por una ruta aérea concreta que "
                "no esté en el resumen de señales aéreas del CONTEXTO."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origen": {"type": "string", "description": "Código IATA, ciudad o mercado de origen (opcional)."},
                    "destino": {"type": "string", "description": "Código IATA o ciudad de destino (opcional)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_competidores",
            "description": (
                "Devuelve el listado COMPLETO (sin recortar a 8) de hoteles del set competitivo de "
                "la zona activa, con filtros opcionales. Úsalo cuando pidan 'todos los hoteles' o "
                "un filtro (régimen, cancelación gratis, rating mínimo) fuera del top-8 del CONTEXTO."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "regimen": {"type": "string", "description": "Filtra por régimen exacto, p.ej. 'Todo incluido'."},
                    "cancelacionGratis": {"type": "boolean", "description": "Si es true, solo hoteles con cancelación gratuita."},
                    "ratingMinimo": {"type": "number", "description": "Rating mínimo (0-10)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_asociacion_tiempo_tarifa",
            "description": (
                "Calcula una asociación descriptiva entre cambios consecutivos del ADR observado "
                "y la meteorología enlazada a las fotos del mercado. Úsalo cuando el usuario "
                "pregunte si el tiempo se relaciona con cambios de precio. No representa demanda "
                "ni demuestra causalidad."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "capturas": {"type": "integer", "description": "Número máximo de fotos recientes a revisar (2-60)."},
                },
            },
        },
    },
]

MODE_POLICIES: dict[str, dict[str, Any]] = {
    "auto": {
        "label": "Automático",
        "instruction": "Selecciona la profundidad adecuada. Responde con evidencia, separa inferencias y pide aclaración si faltan datos.",
        "max_tokens": 1600,
    },
    "quick": {
        "label": "Consulta",
        "instruction": "Responde de forma breve y operativa. Prioriza una cifra, ranking o hecho verificable.",
        "max_tokens": 1200,
    },
    "analysis": {
        "label": "Análisis",
        "instruction": "Contrasta señales, explica relaciones y separa evidencia, inferencia y datos faltantes.",
        "max_tokens": 1800,
    },
    "decision": {
        "label": "Decisión",
        "instruction": "Formula una recomendación condicionada. No autorices pricing si la vigencia, comparabilidad o validación PMS no son suficientes.",
        "max_tokens": 2000,
    },
}

# Límites defensivos para no disparar coste ni tokens.
MAX_HISTORY_TURNS = 8
REQUEST_TIMEOUT = 30.0
TURN_BUDGET_SECONDS = 30.0
# Reintentos ante rate-limit (429) o errores transitorios (5xx). Útil sobre todo con
# modelos ":free" de OpenRouter, que sufren rate-limit upstream con frecuencia.
MAX_RETRIES = 3
RETRY_BACKOFF = 2.5  # segundos (lineal: 2.5, 5, 7.5)
# Rondas de tool-calling permitidas antes de forzar una respuesta final. Cada ronda es una
# llamada extra a OpenRouter, así que se mantiene bajo para no agravar el rate-limit del
# modelo gratuito.
# A tool round may contain several calls; keep both limits explicit so a
# malformed or over-eager model cannot create an unbounded agent loop.
MAX_TOOL_ROUNDS = 6
MAX_TOOL_CALLS = 12
REQUIRED_RESPONSE_BLOCKS = ("Lectura", "Evidencia", "Acción siguiente", "Límite de confianza")
FORBIDDEN_RESPONSE_ARTIFACTS = ("```mermaid", "<svg", "</svg>")

# I1-16: patrón canónico para cifras PMS sin evidencia (ocupación/pickup/RevPAR
# con número). Reutilizado por `copilot_live_evaluation` para no duplicar la
# expresión; la validación solo avisa (`warning`), nunca bloquea la respuesta.
UNSUPPORTED_METRIC_PATTERN = re.compile(
    r"\b(?:ocupaci[oó]n|pickup|revpar)\b[^\n.!?]{0,40}\b\d+(?:[,.]\d+)?\s*(?:%|€|eur\b)",
    re.IGNORECASE,
)


class AssistantError(Exception):
    """Fallo recuperable al hablar con OpenRouter (se traduce a un error de API claro)."""


def _round(value: Any) -> Any:
    return round(value, 2) if isinstance(value, (int, float)) else value


def _freshness_meta(raw: Any) -> dict[str, Any]:
    return freshness(raw)


def _target_external_province(target_name: str | None) -> str | None:
    """Mapeo conservador para filtrar Dataestur sin inventar una geografía."""
    folded = unicodedata.normalize("NFKD", str(target_name or "")).lower()
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    if any(token in folded for token in ("gran canaria", "fuerteventura", "lanzarote")):
        return "Las Palmas"
    if any(token in folded for token in ("tenerife", "la gomera", "el hierro")):
        return "Santa Cruz de Tenerife"
    return None


def _compact_external_observations(rows: list[dict], limit: int = 24) -> list[dict]:
    """Proyección pequeña para el Copilot; nunca incluye payloads originales."""
    compact: list[dict] = []
    for row in rows[:limit]:
        compact.append(
            {
                "evidenceId": f"external-{row.get('sourceId')}-{row.get('id')}",
                "sourceId": row.get("sourceId"),
                "datasetId": row.get("datasetId"),
                "metric": row.get("metric"),
                "unit": row.get("unit"),
                "geographyType": row.get("geographyType"),
                "geographyCode": row.get("geographyCode"),
                "segment": row.get("segment"),
                "period": row.get("periodStart"),
                "value": _round(row.get("value")),
                "fetchedAt": row.get("fetchedAt"),
                "qualityStatus": row.get("qualityStatus"),
            }
        )
    return compact


def _add_external_context(context: dict[str, Any], db: Database, target_name: str | None) -> None:
    """Añade sólo la fracción relevante de la caché externa al contexto base."""
    province = _target_external_province(target_name)
    dataestur = _safe(
        lambda: db.list_external_observations(
            source_id="dataestur-segittur",
            dataset_id="PRECIOS_ALOJAMIENTOS_HOTELEROS_DL",
            geography_code=province,
            limit=24,
        ) if province else db.list_external_observations(
            source_id="dataestur-segittur",
            dataset_id="PRECIOS_ALOJAMIENTOS_HOTELEROS_DL",
            limit=12,
        ),
        default=[],
    )
    istac = _safe(
        lambda: db.list_external_observations(
            source_id="istac-accommodation", limit=24
        ),
        default=[],
    )
    if not dataestur and not istac:
        return
    context["contextoExterno"] = {
        "dataesturPrecios": _compact_external_observations(dataestur),
        "istacAlojamiento": _compact_external_observations(istac),
        "filtroProvincia": province,
        "notaSemantica": (
            "Indicadores agregados y publicados; sirven como benchmark de contexto. "
            "No equivalen al precio del hotel, pickup, ocupación PMS ni demanda diaria."
        ),
    }


def _attach_evidence(context: dict[str, Any]) -> None:
    """Añade un paquete pequeño de cifras trazables al contexto del modelo.

    Los agregados no tienen una fila única de origen: se enlazan a la captura que
    los produjo y explican el cálculo. Esto evita presentar un promedio como si
    fuera una observación individual.
    """
    records: list[dict[str, Any]] = []
    quality = context.get("calidadAnalisis") or {}
    market = context.get("mercado") or {}
    snapshot_id = quality.get("snapshotId")
    observed_at = quality.get("scrapedAt")
    quality_state = quality.get("estado")
    comparison_status = (quality.get("comparacion") or {}).get("estado") or "not_applicable"
    evidence_quality = (
        "stale" if quality_state in {"caducado", "revisar"}
        else "missing" if quality_state == "sin_fecha"
        else "unverified" if not observed_at else "verified"
    )

    for metric, value, unit, calculation in (
        ("adrMedio", market.get("adrMedio"), "EUR/noche", "media de pricePerNight de filas comparables"),
        ("adrMediano", market.get("adrMediano"), "EUR/noche", "mediana de pricePerNight de filas comparables"),
        ("minPorNoche", market.get("minPorNoche"), "EUR/noche", "mínimo de pricePerNight de filas comparables"),
        ("maxPorNoche", market.get("maxPorNoche"), "EUR/noche", "máximo de pricePerNight de filas comparables"),
    ):
        if value is not None:
            records.append(
                EvidenceRecord(
                    evidenceId=f"hotel-market-{metric}", metric=metric, entityType="market",
                    targetId=(context.get("zonaActiva") or {}).get("id"), value=value, unit=unit,
                    observedAt=observed_at, snapshotId=snapshot_id,
                    sourceTable="market_snapshot_hotels", quality=evidence_quality,
                    comparability=comparison_status,
                    calculation=calculation,
                ).model_dump()
            )

    external = context.get("contextoExterno") or {}
    external_rows = [
        row
        for section in ("dataesturPrecios", "istacAlojamiento")
        for row in (external.get(section) or [])
        if isinstance(row, dict)
    ]
    for row in external_rows[:24]:
        status = str(row.get("qualityStatus") or "unverified")
        quality_value = (
            "stale" if status in {"stale", "expired", "caducado"}
            else "partial" if status in {"partial", "parcial"}
            else "verified" if status == "ok" else "unverified"
        )
        records.append(
            EvidenceRecord(
                evidenceId=str(row.get("evidenceId") or "external-unknown"),
                metric=str(row.get("metric") or "external_value"),
                entityType="external",
                entityId=str(row.get("geographyCode") or "") or None,
                targetId=(context.get("zonaActiva") or {}).get("id"),
                value=row.get("value"),
                unit=row.get("unit"),
                period=row.get("period"),
                sourceId=row.get("sourceId"),
                datasetId=row.get("datasetId"),
                observedAt=row.get("fetchedAt"),
                sourceTable="external_observations",
                sourceRowIds=[int(row["evidenceId"].rsplit("-", 1)[-1])]
                if str(row.get("evidenceId", "")).rsplit("-", 1)[-1].isdigit()
                else [],
                quality=quality_value,
                calculation="valor agregado publicado por la fuente externa",
            ).model_dump()
        )

    for metric, value, unit, calculation in (
        ("comparabilidadPct", quality.get("comparabilidadPct"), "%", "filas con precio, noches y producto comparable / filas de captura"),
        ("comparisonCoveragePct", (quality.get("comparacion") or {}).get("coberturaPct"), "%", "filas actuales emparejadas con la captura anterior / filas comparables actuales"),
    ):
        if value is not None:
            records.append(
                EvidenceRecord(
                    evidenceId=f"hotel-quality-{metric}", metric=metric, entityType="data_quality",
                    targetId=(context.get("zonaActiva") or {}).get("id"), value=value, unit=unit,
                    observedAt=observed_at, snapshotId=snapshot_id,
                    sourceTable="market_snapshots", quality=evidence_quality,
                    comparability=(quality.get("comparacion") or {}).get("estado") or "not_applicable",
                    calculation=calculation,
                ).model_dump()
            )

    air = context.get("senalesAereas") or {}
    air_capture = air.get("captura") or {}
    air_freshness = _freshness_meta(air_capture.get("capturedAt"))
    air_quality = (
        "stale" if air_freshness.get("estado") in {"caducado", "revisar"}
        else "missing" if air_freshness.get("estado") == "sin_fecha"
        else "unverified" if not air_capture else "verified"
    )
    summary = air.get("resumen") or {}
    for metric, value, unit, calculation in (
        ("airRouteCount", summary.get("rutas"), "rutas", "número de rutas agregadas en la captura aérea"),
        ("airOptionCount", summary.get("opciones"), "opciones", "número de opciones de vuelo observadas"),
        ("airAvgLowestPrice", summary.get("precioMedioMin"), "EUR", "media del precio mínimo observado por ruta"),
    ):
        if value is not None:
            records.append(
                EvidenceRecord(
                    evidenceId=f"air-{metric}", metric=metric, entityType="capture",
                    value=value, unit=unit, observedAt=air_capture.get("capturedAt"),
                    snapshotId=air_capture.get("id"), sourceTable="air_runs", quality=air_quality,
                    calculation=calculation,
                ).model_dump()
            )

    context["evidencia"] = EvidenceBundle.model_validate({"records": records}).model_dump()


def build_revenue_context(
    db: Database,
    target_id: int | None,
    air_data: dict | None = None,
    metrics: dict | None = None,
) -> dict[str, Any]:
    """Resume el estado de mercado/RIU del target activo en un dict compacto para el LLM.

    Cada sección va protegida: si una consulta falla o no hay datos, se omite en vez de
    romper la respuesta del asistente.
    """
    context: dict[str, Any] = {}

    targets = _safe(lambda: [t.model_dump() for t in db.list_targets()], default=[])
    context["zonasDisponibles"] = [{"id": t["id"], "name": t["name"]} for t in targets]

    # Las señales aéreas son globales (rutas hacia Canarias): se incluyen siempre,
    # haya o no zona de hotel activa.
    _add_air_signals(context, air_data)

    if target_id is None:
        if not targets:
            context["aviso"] = (
                "No hay capturas de hoteles todavía (search_targets vacío). Solo hay datos aéreos. "
                "Para análisis de ADR/competencia hace falta ejecutar una captura de hoteles."
            )
        else:
            context["aviso"] = "No hay zona de hotel activa seleccionada; usa los datos aéreos o selecciona una zona."
        _attach_evidence(context)
        return context

    target = _safe(lambda: db.get_target(target_id))
    if target is not None:
        context["zonaActiva"] = {"id": target.id, "name": target.name}
        _add_external_context(context, db, target.name)

    metrics = metrics if metrics is not None else _safe(lambda: db.dashboard_metrics(target_id))
    if metrics:
        market = metrics.get("market", {})
        demand = metrics.get("demandIndicators", {})
        movement = metrics.get("movement", {})
        competitive = metrics.get("competitiveSet", []) or []

        context["mercado"] = {
            "adrMedio": market.get("avgPricePerNight"),
            "adrMediano": market.get("medianPricePerNight"),
            "minPorNoche": market.get("minPricePerNight"),
            "maxPorNoche": market.get("maxPricePerNight"),
            "competidoresComparables": metrics.get("rateShoppingIndex", {}).get("totalCompetitors"),
        }
        context["demanda"] = {
            "presionTarifaria": demand.get("bookingPressure"),
            "direccionPrecio": demand.get("priceDirection"),
            "subidasCompetidores": demand.get("competitorIncreases"),
            "bajadasCompetidores": demand.get("competitorDrops"),
            "captureCoveragePct": demand.get("fillRatio"),
            "variacionAdrPct": movement.get("avgPricePerNightChangePct"),
            "nota": "captureCoveragePct es cobertura técnica de la extracción; no equivale a fill ratio, pickup u ocupación PMS.",
        }
        latest_snapshot = metrics.get("latestSnapshot") or {}
        quality = metrics.get("dataQuality") or {}
        comparison = metrics.get("comparison") or {}
        context["calidadAnalisis"] = {
            **_freshness_meta(latest_snapshot.get("scrapedAt")),
            "snapshotId": latest_snapshot.get("id"),
            "comparabilidadPct": quality.get("productComparablePct", quality.get("comparablePct")),
            "filasObservadas": quality.get("totalRows"),
            "notas": quality.get("notes") or [],
            "comparacion": {
                "estado": (
                    "matched_partial"
                    if comparison.get("status") == "matched" and comparison.get("matchedCoveragePct", 100) < 100
                    else comparison.get("status")
                ),
                "coberturaPct": comparison.get("matchedCoveragePct"),
                "motivo": comparison.get("reason"),
            },
        }

        # Posicionamiento RIU dentro del set (hoteles cuyo nombre contiene "riu").
        riu = [c for c in competitive if "riu" in str(c.get("hotelName", "")).lower()]
        if riu:
            riu_ppn = [c["pricePerNight"] for c in riu if isinstance(c.get("pricePerNight"), (int, float))]
            context["riu"] = {
                "hoteles": [
                    {
                        "nombre": c.get("hotelName"),
                        "adrNoche": c.get("pricePerNight"),
                        "gapVsMercadoPct": c.get("gapVsMarketPct"),
                        "rankingMercado": c.get("marketRank"),
                        "variacionPct": c.get("priceChangePct"),
                        "rating": c.get("rating"),
                    }
                    for c in riu[:12]
                ],
                "adrMedioRiu": _round(sum(riu_ppn) / len(riu_ppn)) if riu_ppn else None,
            }

        # Top y bottom del ranking competitivo (recortado).
        context["rankingCompetitivo"] = [
            {
                "nombre": c.get("hotelName"),
                "adrNoche": c.get("pricePerNight"),
                "gapVsMercadoPct": c.get("gapVsMarketPct"),
                "rankingMercado": c.get("marketRank"),
            }
            for c in competitive[:8]
        ]
        context["calidadDatos"] = metrics.get("dataQuality", {}).get("notes", [])

    opportunities = _safe(lambda: db.revenue_opportunities(target_id, air_data=air_data), default=[])
    if opportunities:
        context["oportunidadesRevenue"] = [
            {
                "tipo": o.get("type"),
                "severidad": o.get("severity"),
                "titulo": o.get("title"),
                "mensaje": o.get("message"),
                "hotel": o.get("hotelName"),
            }
            for o in opportunities[:8]
        ]

    stability = _safe(lambda: db.competitive_stability(target_id, snapshots_count=8), default=[])
    if stability:
        context["estabilidadCompetitiva"] = [
            {
                "hotel": s.get("hotelName"),
                "adrMedioNoche": s.get("avgPricePerNight"),
                "posicionamiento": s.get("positioningLabel"),
                "gapVsMercadoPct": s.get("avgGapVsMarketPct"),
                "consistencia": s.get("consistencyScore"),
            }
            for s in stability[:8]
        ]

    demand_curve = _safe(lambda: db.demand_curve(target_id, limit_snapshots=12), default=[])
    if demand_curve:
        context["curvaAdrObservada"] = [
            {
                "diasHastaCheckIn": p.get("daysUntilCheckIn"),
                "adrMedio": p.get("avgAdr"),
                "observaciones": p.get("observations"),
            }
            for p in demand_curve[:12]
        ]

    _attach_evidence(context)
    return context


def _add_air_signals(context: dict[str, Any], air_data: dict | None) -> None:
    """Añade el resumen y las rutas aéreas al contexto (datos globales hacia Canarias)."""
    if not air_data or not isinstance(air_data, dict):
        return
    summary = air_data.get("summary", {})
    routes = air_data.get("routes", []) or []
    context["senalesAereas"] = {
        "resumen": {
            "rutas": summary.get("total_routes"),
            "opciones": summary.get("total_options"),
            "precioMedioMin": summary.get("avg_lowest_price"),
            "precioMedioOpcion": summary.get("avg_option_price"),
            "rangoMedioTipico": summary.get("avg_typical_price"),
            "gapMedioVsTipicoPct": summary.get("avg_entry_gap_pct"),
            "directoPct": summary.get("direct_pct"),
            "aerolineas": summary.get("airlines_detected"),
            "oportunidades": summary.get("opportunities_count"),
            "riesgos": summary.get("risks_count"),
        },
        "captura": air_data.get("capture"),
        "notaSemantica": "Señal de accesibilidad aérea por mercado emisor; no es demanda hotelera ni margen.",
        "rutas": [
            {
                "mercado": r.get("market") or r.get("origin"),
                "origen": r.get("origin"),
                "destino": r.get("destination"),
                "precioMin": r.get("lowest_price"),
                "precioMedio": r.get("avg_price"),
                "rangoTipico": [r.get("typical_price_min"), r.get("typical_price_max")],
                "gapVsTipicoPct": r.get("price_gap_pct"),
                "opciones": r.get("num_options"),
                "aerolineas": r.get("airlines_detected"),
                "directoPct": r.get("direct_share"),
                "salida": r.get("outbound_date"),
                "diasAntelacion": r.get("days_ahead"),
                "nivel": r.get("price_level") or r.get("google_price_level"),
                "riesgo": r.get("route_risk_level"),
            }
            for r in routes[:20]
        ],
    }


def build_assistant_visualization(
    db: Database,
    target_id: int | None,
    air_data: dict | None,
    message: str,
    enabled: bool,
    metrics: dict | None = None,
) -> dict[str, Any] | None:
    """Crea un único gráfico de soporte usando solamente datos calculados en el backend.

    La IA redacta la interpretación; esta función entrega el conjunto de puntos verificable.
    Así no se confunden una visualización útil y una cifra inventada por el modelo.
    """
    if not enabled:
        return None
    query = (message or "").lower()
    asks_air = any(word in query for word in ("vuelo", "aéreo", "aereo", "ruta", "conectividad", "mercado emisor"))

    if asks_air:
        routes = (air_data or {}).get("routes", []) or []
        valid = [route for route in routes if isinstance(route.get("lowest_price"), (int, float))]
        if not valid:
            return None
        ordered = sorted(valid, key=lambda route: float(route["lowest_price"]))[:8]
        return {
            "type": "bar",
            "scope": "air",
            "title": "Precio mínimo aéreo por mercado",
            "subtitle": "Ocho rutas más accesibles de la última extracción aérea.",
            "unit": "€",
            "points": [
                {
                    "label": f"{route.get('market') or route.get('origin') or 'Origen'} · {route.get('destination') or ''}".strip(" ·"),
                    "value": _round(route["lowest_price"]),
                    "detail": route.get("revenue_signal") or route.get("price_quality_label") or "Sin señal",
                    "tone": "positive" if str(route.get("price_quality_label", "")).lower() == "barato" else "neutral",
                }
                for route in ordered
            ],
            "source": "Vuelos capturados",
        }

    if target_id is None:
        return None
    metrics = metrics if metrics is not None else (_safe(lambda: db.dashboard_metrics(target_id), default={}) or {})
    hotels = [
        hotel for hotel in (metrics.get("competitiveSet") or [])
        if isinstance(hotel.get("pricePerNight"), (int, float))
    ]
    if not hotels:
        return None
    wants_low = any(word in query for word in ("barato", "bajo", "mínimo", "minimo", "descuento"))
    ordered = sorted(hotels, key=lambda hotel: float(hotel["pricePerNight"]), reverse=not wants_low)[:8]
    market_adr = (metrics.get("market") or {}).get("avgPricePerNight")
    return {
        "type": "bar",
        "scope": "hotel",
        "title": "Posicionamiento ADR del set",
        "subtitle": "Tarifa pública por habitación y noche; muestra 8 hoteles comparables.",
        "unit": "€ / noche",
        "benchmark": market_adr,
        "points": [
            {
                "label": hotel.get("hotelName") or "Hotel",
                "value": hotel.get("pricePerNight"),
                "detail": f"{hotel.get('gapVsMarketPct', 0):+.1f}% vs. ADR de mercado" if isinstance(hotel.get("gapVsMarketPct"), (int, float)) else "Sin gap comparable",
                "tone": "positive" if isinstance(hotel.get("gapVsMarketPct"), (int, float)) and hotel["gapVsMarketPct"] <= 0 else "attention",
            }
            for hotel in ordered
        ],
        "source": "Última captura de Booking",
    }


def assistant_data_meta(
    context: dict[str, Any],
    visualization: dict[str, Any] | None,
    *,
    mode: str = "quick",
) -> dict[str, Any]:
    """Metadatos mínimos que el cliente muestra junto a la conclusión del modelo."""
    market = context.get("mercado") or {}
    quality = context.get("calidadAnalisis") or {}
    comparison = quality.get("comparacion") or {}
    workspace = context.get("contextoWorkspace") or {}
    evidence_records = (context.get("evidencia") or {}).get("records") or []
    references = [
        {
            "evidenceId": record.get("evidenceId"),
            "metric": record.get("metric"),
            "entityType": record.get("entityType"),
            "observedAt": record.get("observedAt") or record.get("sourceObservedAt"),
            "snapshotId": record.get("snapshotId"),
            "sourceId": record.get("sourceId") or record.get("datasetId"),
        }
        for record in evidence_records
        if isinstance(record, dict) and record.get("evidenceId")
    ][:40]
    verification = {
        "status": "verified" if references and all(record.get("quality") == "verified" for record in evidence_records if isinstance(record, dict) and record.get("evidenceId")) else ("partial" if references else "insufficient"),
        "method": "comprobación determinista del paquete de evidencia",
        "recordCount": len(references),
    }
    return {
        "zone": (context.get("zonaActiva") or {}).get("name"),
        "comparableHotels": market.get("competidoresComparables"),
        "hasAirData": bool((context.get("senalesAereas") or {}).get("rutas")),
        "hasExternalData": bool(
            (context.get("contextoExterno") or {}).get("dataesturPrecios")
            or (context.get("contextoExterno") or {}).get("istacAlojamiento")
        ),
        "externalEvidenceRecords": sum(
            len((context.get("contextoExterno") or {}).get(section) or [])
            for section in ("dataesturPrecios", "istacAlojamiento")
        ),
        "visualizationSource": visualization.get("source") if visualization else None,
        "freshnessLabel": quality.get("etiqueta"),
        "freshnessState": quality.get("estado"),
        "comparisonStatus": comparison.get("estado"),
        "comparisonCoveragePct": comparison.get("coberturaPct"),
        "workspaceContext": {
            "anchorSnapshotId": (workspace.get("extraction") or {}).get("anchorSnapshotId"),
            "checkIn": workspace.get("checkIn"),
            "comparableRows": (workspace.get("population") or {}).get("comparableRows"),
        } if workspace else None,
        "evidenceSchemaVersion": ((context.get("evidencia") or {}).get("schemaVersion")),
        "evidenceRecords": len((context.get("evidencia") or {}).get("records") or []),
        "references": references,
        "verification": verification,
        "routing": context.get("orquestacion"),
        "mode": mode if mode in MODE_POLICIES else "auto",
        "dataGate": assistant_data_gate(context, mode=mode),
    }


def assistant_data_gate(context: dict[str, Any], *, mode: str = "quick") -> dict[str, Any]:
    """Control determinista previo al razonamiento del modelo.

    ``blocked`` conserva la señal de calidad que ya consume la interfaz. La
    decisión operativa se expresa con ``canRecommend``: en modo decisión una
    advertencia de vigencia, comparabilidad o ausencia de RIU impide llamar al
    proveedor y emitir pricing concluyente.
    """
    quality = context.get("calidadAnalisis") or {}
    state = quality.get("estado")
    comparable = quality.get("comparabilidadPct")
    comparison = quality.get("comparacion") or {}
    warnings: list[str] = []
    no_zone = not context.get("zonaActiva")
    if not context.get("zonaActiva"):
        warnings.append("No hay una zona hotelera activa seleccionada.")
    if state in {"caducado", "revisar", "sin_fecha"}:
        warnings.append(f"Los datos están en estado: {quality.get('etiqueta') or 'vigencia no verificada'}.")
    if isinstance(comparable, (int, float)) and comparable < 70:
        warnings.append(f"La comparabilidad de la captura es del {comparable:g}%, por debajo del 70%.")
    comparison_coverage = comparison.get("coberturaPct")
    partial_comparison = isinstance(comparison_coverage, (int, float)) and comparison_coverage < 70
    if comparison.get("estado") == "unmatched" or (comparison.get("estado") == "matched_partial" and partial_comparison):
        warnings.append("La comparativa no está emparejada con una captura anterior; no prueba movimiento temporal.")
    if mode == "decision" and not context.get("riu"):
        warnings.append("No hay propiedades RIU identificadas en el set actual para sostener una decisión de pricing.")
    can_recommend = not no_zone and (mode != "decision" or not warnings)
    result = DataGateResult(
        blocked=bool(warnings),
        canRecommend=can_recommend,
        warnings=warnings,
        severity="blocked" if mode == "decision" and not can_recommend else ("warning" if warnings else "ok"),
    )
    return result.model_dump()


def blocked_decision_reply(gate: dict[str, Any]) -> str:
    """Respuesta segura cuando el modo decisión no supera el data gate."""
    warnings = gate.get("warnings") or ["La calidad de los datos no permite recomendar pricing."]
    bullets = "\n".join(f"- {warning}" for warning in warnings)
    return (
        "**Lectura**\n"
        "No puedo emitir una recomendación de pricing en modo decisión porque el contexto no supera el control de calidad.\n\n"
        "**Evidencia**\n"
        f"{bullets}\n\n"
        "**Acción siguiente**\n"
        "Actualiza la captura y confirma que el producto sea comparable; valida además ocupación, pickup y restricciones en el PMS.\n\n"
        "**Límite de confianza**\n"
        "Sin vigencia y comparabilidad suficientes, cualquier subida o bajada sería una hipótesis no autorizable."
    )


def _fold_metric_text(value: str) -> str:
    """Normaliza texto para comparar cifras frente a evidencia (sin tildes, `,`→`.`)."""
    folded = unicodedata.normalize("NFKD", (value or "").lower())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return folded.replace(",", ".")


def _evidence_covers_claim(evidence_folded: str, claim: str) -> bool:
    """Indica si la evidencia ya contiene la misma métrica y cifra del claim."""
    claim_folded = _fold_metric_text(claim)
    numbers = re.findall(r"\d+(?:\.\d+)?", claim_folded)
    metrics = re.findall(r"ocupacion|pickup|revpar", claim_folded)
    if not numbers or not metrics:
        return False
    for metric in metrics:
        if metric not in evidence_folded:
            continue
        for number in numbers:
            if re.search(r"(?<!\d)" + re.escape(number) + r"(?!\d)", evidence_folded):
                return True
    return False


def validate_assistant_response(response: str, evidence: Any | None = None) -> dict[str, Any]:
    """Comprueba el contrato editorial sin alterar el texto generado por el modelo.

    Reutiliza `UNSUPPORTED_METRIC_PATTERN`: una cifra de ocupación/pickup/RevPAR
    con número sin respaldo en `evidence` deja `status` en `warning` con
    `unsupportedMetricClaims`, sin bloquear la respuesta. Si la misma métrica y
    cifra aparecen en la evidencia aportada, el claim se considera verificado.
    """
    text = response or ""
    lowered = text.lower()
    missing_blocks = [block for block in REQUIRED_RESPONSE_BLOCKS if block.lower() not in lowered]
    forbidden_artifacts = [artifact for artifact in FORBIDDEN_RESPONSE_ARTIFACTS if artifact.lower() in lowered]
    unsupported_claims = UNSUPPORTED_METRIC_PATTERN.findall(text)
    if unsupported_claims and evidence is not None:
        try:
            raw_evidence = evidence if isinstance(evidence, str) else json.dumps(evidence, ensure_ascii=False, default=str)
        except Exception:  # noqa: BLE001 - evidencia no serializable: se trata como ausente
            raw_evidence = ""
        evidence_folded = _fold_metric_text(raw_evidence)
        if evidence_folded:
            unsupported_claims = [claim for claim in unsupported_claims if not _evidence_covers_claim(evidence_folded, claim)]
    return {
        "schemaVersion": "revenue-response-quality.v1",
        "status": "ok" if not missing_blocks and not forbidden_artifacts and not unsupported_claims else "warning",
        "requiredBlocks": list(REQUIRED_RESPONSE_BLOCKS),
        "missingBlocks": missing_blocks,
        "forbiddenArtifacts": forbidden_artifacts,
        "unsupportedMetricClaims": list(unsupported_claims),
    }


def _safe(producer, default=None):
    try:
        return producer()
    except Exception as exc:  # noqa: BLE001 - una sección sin datos no debe tumbar el asistente
        logger.warning("build_revenue_context: sección omitida: %s", exc)
        return default


def _find_hotel_rows(db: Database, nombre: str, target_id: int | None = None) -> list[tuple[str, Any]]:
    """Busca `nombre` (substring, case-insensitive) solo dentro del mercado activo.

    Sin `target_id` no se barre ningún mercado: el llamador debe exigir que el
    usuario seleccione mercado antes de consultar herramientas de hoteles."""
    needle = (nombre or "").strip().lower()
    if not needle:
        return []
    if target_id is None:
        return []
    matches: list[tuple[str, Any]] = []
    targets = _safe(lambda: db.list_targets(), default=[])
    targets = [target for target in targets if target.id == target_id]
    for target in targets:
        snapshot = _safe(lambda t=target: db.latest_snapshot(t.id))
        if not snapshot:
            continue
        rows = _safe(lambda s=snapshot: db.snapshot_rows(s.id), default=[])
        for row in rows:
            if needle in row.hotelName.lower():
                matches.append((target.name, row))
    return matches


def _tool_buscar_hotel(db: Database, arguments: dict) -> dict:
    nombre = str(arguments.get("nombre") or "")
    requested_target = arguments.get("targetId")
    target_id = int(requested_target) if isinstance(requested_target, (int, float)) else None
    if target_id is None:
        return {"error": "Selecciona un mercado antes de buscar hoteles."}
    matches = _find_hotel_rows(db, nombre, target_id=target_id)
    if not matches:
        return {"encontrados": 0, "mensaje": f"No se encontró ningún hotel que contenga '{nombre}'."}
    return {
        "encontrados": len(matches),
        "muestraCompleta": True,
        "hoteles": [
            {
                "zona": zone_name,
                "nombre": row.hotelName,
                "hotelKey": row.hotelKey,
                "checkIn": row.checkIn, "checkOut": row.checkOut, "nights": row.nights,
                "pax": row.pax, "roomType": row.roomType, "currency": row.currency,
                "adrNoche": row.pricePerNight,
                "adrPersonaNoche": row.pricePerPersonPerNight,
                "regimen": row.board,
                "rating": row.rating,
                "resenas": row.reviewCount,
                "cancelacionGratis": row.freeCancellation,
                "posicion": row.position,
            }
            for zone_name, row in matches[:200]
        ],
        "hotelesRecortados": max(0, len(matches) - 200),
    }


def _tool_historial_precio_hotel(db: Database, arguments: dict) -> dict:
    nombre = str(arguments.get("nombre") or "")
    capturas = arguments.get("capturas")
    limit = max(1, min(60, int(capturas))) if isinstance(capturas, (int, float)) else 24
    requested_target = arguments.get("targetId")
    target_id = int(requested_target) if isinstance(requested_target, (int, float)) else None
    if target_id is None:
        return {"error": "Selecciona un mercado antes de consultar el historial."}
    matches = _find_hotel_rows(db, nombre, target_id=target_id)
    zone = str(arguments.get("zona") or "").strip().casefold()
    if zone:
        matches = [(name, row) for name, row in matches if name.casefold() == zone]
    if not matches:
        return {"encontrados": 0, "mensaje": f"No se encontró ningún hotel que contenga '{nombre}'."}
    if len(matches) != 1:
        return {"requiereAclaracion": True, "mensaje": "Especifica hotel y zona antes de consultar la evolución.",
                "candidatos": [{"hotel": row.hotelName, "zona": name, "hotelKey": row.hotelKey} for name, row in matches]}
    zone_name, row = matches[0]
    target = next((target for target in db.list_targets() if target.name == zone_name), None)
    if target is None:
        return {"error": "No se pudo verificar la zona del hotel."}
    history = _safe(lambda: db.hotel_price_history(row.hotelKey, target_id=target.id, limit=limit), default=[])
    compact_history = [
        {
            "snapshotId": h.get("snapshotId"),
            "fechaObservacion": h.get("scrapedAt"),
            "entrada": h.get("checkIn"), "salida": h.get("checkOut"),
            "noches": h.get("nights"), "adultos": h.get("pax"),
            "habitacion": h.get("roomType"), "regimen": h.get("board"),
            "moneda": h.get("currency"), "cancelacionGratis": h.get("freeCancellation"),
            "tarifaNoche": h.get("pricePerNight"),
        }
        for h in history[:36]
    ]
    return {
        "hotel": row.hotelName, "hotelKey": row.hotelKey,
        "zona": zone_name, "targetId": target.id,
        "limites": "Tarifas públicas observadas, no ADR realizado ni pickup de reservas. Comparar solo productos equivalentes; no inferir ocupación.",
        "capturas": compact_history,
        "capturasRecortadas": max(0, len(history) - len(compact_history)),
    }


def _tool_buscar_vuelos(air_data: dict | None, arguments: dict) -> dict:
    if not air_data:
        return {"encontrados": 0, "mensaje": "No hay datos aéreos cargados en esta sesión."}
    flights = air_data.get("flights", []) or []
    origen = str(arguments.get("origen") or "").strip().lower()
    destino = str(arguments.get("destino") or "").strip().lower()

    def keep(flight: dict) -> bool:
        if origen and origen not in str(flight.get("origin", "")).lower() and origen not in str(flight.get("market", "")).lower():
            return False
        if destino and destino not in str(flight.get("destination", "")).lower():
            return False
        return True

    found = [flight for flight in flights if keep(flight)][:15]
    return {
        "encontrados": len(found),
        "vuelos": [
            {
                "mercado": f.get("market"),
                "origen": f.get("origin"),
                "destino": f.get("destination"),
                "aerolinea": f.get("main_airline"),
                "precio": f.get("price"),
                "minimoConsulta": f.get("lowest_price"),
                "directo": f.get("is_direct"),
                "salida": f.get("outbound_date"),
            }
            for f in found
        ],
    }


def _tool_listar_competidores(db: Database, target_id: int | None, arguments: dict) -> dict:
    if target_id is None:
        return {"error": "Selecciona un mercado antes de listar competidores."}
    snapshot = _safe(lambda: db.latest_snapshot(target_id))
    if not snapshot:
        return {"error": "No hay capturas para la zona activa."}
    rows = _safe(lambda: db.snapshot_rows(snapshot.id), default=[])
    regimen = str(arguments.get("regimen") or "").strip().lower()
    cancelacion_gratis = arguments.get("cancelacionGratis")
    rating_minimo = arguments.get("ratingMinimo")

    def keep(row: Any) -> bool:
        if regimen and regimen not in str(row.board or "").lower():
            return False
        if cancelacion_gratis is True and row.freeCancellation is not True:
            return False
        if isinstance(rating_minimo, (int, float)) and (row.rating is None or row.rating < rating_minimo):
            return False
        return True

    filtered = [row for row in rows if keep(row)]
    return {
        "total": len(filtered),
        "observedAt": snapshot.scrapedAt,
        "snapshotId": snapshot.id,
        "hoteles": [
            {
                "nombre": row.hotelName,
                "adrNoche": row.pricePerNight,
                "regimen": row.board,
                "rating": row.rating,
                "cancelacionGratis": row.freeCancellation,
                "posicion": row.position,
            }
            for row in filtered[:200]
        ],
        "hotelesRecortados": max(0, len(filtered) - 200),
    }


def _tool_analizar_asociacion_tiempo_tarifa(db: Database, target_id: int | None, arguments: dict) -> dict:
    if target_id is None:
        return {"error": "Selecciona un mercado antes de analizar la asociación tiempo-tarifa."}
    capturas = arguments.get("capturas")
    limit = max(2, min(60, int(capturas))) if isinstance(capturas, (int, float)) else 12
    return db.weather_price_association(target_id, limit_snapshots=limit)


def _source_observed_at(value: Any) -> str | None:
    """Find the source observation instant without confusing it with query time.

    Tool envelopes are deliberately small and heterogeneous. We inspect only
    known provenance keys and stop after the first usable ISO-like value. The
    chat query time is always stored separately by ``_run_tool``.
    """
    preferred = ("sourceObservedAt", "observedAt", "capturedAt", "scrapedAt", "captureAt", "fechaObservacion")
    if isinstance(value, dict):
        for key in preferred:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        for key, nested in value.items():
            if key == "_evidence":
                continue
            found = _source_observed_at(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _source_observed_at(nested)
            if found:
                return found
    return None


def _run_tool(
    db: Database | None,
    target_id: int | None,
    air_data: dict | None,
    name: str,
    arguments: dict,
    telemetry: dict[str, Any] | None = None,
) -> dict:
    if db is None:
        return {"error": "Herramientas no disponibles en este contexto."}
    # El mercado activo es una frontera de autorización, no una pista
    # conversacional. Sin mercado no se barre ningún otro: se exige elegirlo.
    # Nunca se deja que el modelo amplíe el alcance con su propio targetId.
    if target_id is None and name in {
        "buscar_hotel",
        "historial_precio_hotel",
        "listar_competidores",
        "analizar_asociacion_tiempo_tarifa",
    }:
        return {"error": "Selecciona un mercado antes de consultar herramientas de hoteles."}
    if target_id is not None:
        arguments = {**arguments, "targetId": target_id}
    started = time.monotonic()
    if telemetry is not None:
        telemetry["toolCalls"] = telemetry.get("toolCalls", 0) + 1
        names = telemetry.setdefault("toolNames", [])
        if name and name not in names:
            names.append(name)
    logger.info("assistant tool call: %s(%s)", name, arguments)
    try:
        if name == "buscar_hotel":
            result = _tool_buscar_hotel(db, arguments)
        elif name == "historial_precio_hotel":
            result = _tool_historial_precio_hotel(db, arguments)
        elif name == "buscar_vuelos":
            result = _tool_buscar_vuelos(air_data, arguments)
        elif name == "listar_competidores":
            result = _tool_listar_competidores(db, target_id, arguments)
        elif name == "analizar_asociacion_tiempo_tarifa":
            result = _tool_analizar_asociacion_tiempo_tarifa(db, target_id, arguments)
        else:
            result = {"error": f"Herramienta desconocida: {name}"}
        if isinstance(result, dict) and result.get("error"):
            if telemetry is not None:
                telemetry["toolErrors"] = telemetry.get("toolErrors", 0) + 1
        elif isinstance(result, dict):
            evidence_id = f"tool-{name}-{uuid.uuid4().hex[:12]}"
            queried_at = datetime.now(timezone.utc).isoformat()
            result = {
                **result,
                "_evidence": {
                    "evidenceId": evidence_id,
                    "tool": name,
                    "queriedAt": queried_at,
                    "sourceObservedAt": _source_observed_at(result),
                },
            }
            if telemetry is not None:
                telemetry.setdefault("toolEvidenceIds", []).append(evidence_id)
                telemetry.setdefault("toolEvidence", []).append({
                    "evidenceId": evidence_id,
                    "tool": name,
                    "queriedAt": queried_at,
                    "sourceObservedAt": (result.get("_evidence") or {}).get("sourceObservedAt"),
                })
        return result
    except Exception as exc:  # noqa: BLE001 - un fallo de herramienta no debe tumbar el chat
        if telemetry is not None:
            telemetry["toolErrors"] = telemetry.get("toolErrors", 0) + 1
        logger.warning("tool %s failed: %s", name, exc)
        return {"error": str(exc)}
    finally:
        if telemetry is not None:
            telemetry.setdefault("toolLatencyMs", []).append(round((time.monotonic() - started) * 1000))


def _post_chat_completion(
    client: httpx.Client,
    settings: OpenRouterSettings,
    headers: dict,
    payload: dict,
    deadline: float,
    telemetry: dict[str, Any],
) -> dict:
    """POST a /chat/completions con reintentos ante 429/5xx (frecuentes en modelos ':free')."""
    response = None
    last_detail = ""
    telemetry.setdefault("providerStatusCodes", [])
    telemetry.setdefault("attemptLatenciesMs", [])
    for attempt in range(MAX_RETRIES + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AssistantError("Se agotó el presupuesto de tiempo para esta consulta.")
        telemetry["attempts"] += 1
        attempt_started = time.monotonic()
        try:
            response = client.post(
                f"{settings.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=min(REQUEST_TIMEOUT, remaining),
            )
        except httpx.HTTPError as exc:
            telemetry["attemptLatenciesMs"].append(round((time.monotonic() - attempt_started) * 1000))
            telemetry["providerStatusCodes"].append(None)
            last_detail = str(exc)
            if attempt < MAX_RETRIES:
                delay = min(RETRY_BACKOFF * (attempt + 1) + random.uniform(0, 0.4), max(0, deadline - time.monotonic()))
                time.sleep(delay)
                continue
            raise AssistantError(f"No se pudo contactar con OpenRouter: {exc}") from exc

        telemetry["attemptLatenciesMs"].append(round((time.monotonic() - attempt_started) * 1000))
        telemetry["providerStatusCodes"].append(response.status_code)
        telemetry["retryCount"] = max(0, telemetry["attempts"] - 1)

        if response.status_code == 429 or response.status_code >= 500:
            last_detail = response.text[:300]
            if attempt < MAX_RETRIES:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else RETRY_BACKOFF * (attempt + 1)
                except ValueError:
                    delay = RETRY_BACKOFF * (attempt + 1)
                delay = min(delay + random.uniform(0, 0.4), max(0, deadline - time.monotonic()))
                time.sleep(delay)
                continue
        break

    if response is None:
        raise AssistantError(f"No se pudo contactar con OpenRouter: {last_detail}")
    if response.status_code == 429:
        raise AssistantError(
            "El modelo está saturado (rate-limit). Reintenta en unos segundos o cambia a un "
            "modelo de pago en OPENROUTER_MODEL para evitar los límites de los modelos ':free'."
        )
    if response.status_code == 401:
        raise AssistantError(
            "OpenRouter rechazó la credencial. Revisa OPENROUTER_API_KEY en el entorno."
        )
    if response.status_code == 404:
        if "No endpoints found" in response.text:
            raise AssistantError(
                "OpenRouter no encontró un endpoint compatible con la solicitud. "
                "La selección exigió soporte para todos los parámetros, "
                f"data_collection={settings.data_collection} y zdr={settings.zdr}. "
                "Prueba otro modelo o endpoint; si tu organización permite retención, "
                "puedes usar OPENROUTER_DATA_COLLECTION=allow y OPENROUTER_ZDR=false."
            )
        raise AssistantError(
            f"El modelo configurado ({settings.model}) no está disponible en OpenRouter. "
            "Revisa OPENROUTER_MODEL y usa un slug activo para tu cuenta."
        )
    if response.status_code >= 400:
        detail = response.text[:300]
        raise AssistantError(f"OpenRouter devolvió HTTP {response.status_code}: {detail}")
    return response.json()


def ask_openrouter(
    settings: OpenRouterSettings,
    message: str,
    context: dict[str, Any],
    history: list[dict[str, str]] | None = None,
    *,
    db: Database | None = None,
    target_id: int | None = None,
    air_data: dict | None = None,
    telemetry: dict[str, Any] | None = None,
    mode: str = "quick",
    budget_seconds: float | None = None,
) -> str:
    """Llama a OpenRouter (API compatible con OpenAI) y devuelve el texto de respuesta final.

    Si se pasa `db`, el modelo puede invocar las TOOLS (buscar_hotel, historial_precio_hotel,
    buscar_vuelos, listar_competidores) para consultar datos que no caben en el resumen fijo de
    `context`. El bucle ejecuta como máximo MAX_TOOL_ROUNDS idas y vueltas antes de forzar una
    respuesta final sin más herramientas.
    """
    if not settings.enabled:
        raise AssistantError(
            "OpenRouter no está configurado. Añade OPENROUTER_API_KEY en .env para usar /ask."
        )

    mode = mode if mode in MODE_POLICIES else "auto"
    policy = MODE_POLICIES[mode]
    started = time.monotonic()
    turn_budget = budget_seconds if budget_seconds is not None else TURN_BUDGET_SECONDS
    deadline = started + turn_budget
    telemetry = telemetry if telemetry is not None else {}
    telemetry.setdefault("requestId", uuid.uuid4().hex)
    telemetry.setdefault("attempts", 0)
    telemetry.setdefault("toolRounds", 0)
    telemetry.setdefault("toolCalls", 0)
    telemetry.setdefault("toolErrors", 0)
    telemetry.setdefault("toolNames", [])
    telemetry["model"] = settings.model
    telemetry["mode"] = mode
    context_json = json.dumps(context, ensure_ascii=False, default=str)
    telemetry["contextChars"] = len(context_json)
    telemetry["historyTurns"] = min(len(history or []), MAX_HISTORY_TURNS)
    mode_prompt = f"\n\nMODO ACTIVO: {policy['label']}. {policy['instruction']}"
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT + mode_prompt}]
    for turn in (history or [])[-MAX_HISTORY_TURNS:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append(
        {"role": "user", "content": f"CONTEXTO (datos reales de la app):\n{context_json}\n\nPREGUNTA:\n{message}"}
    )
    telemetry["messageCount"] = len(messages)

    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
        # OpenRouter recomienda estas cabeceras de atribución (opcionales).
        "HTTP-Referer": "http://127.0.0.1:5001",
        "X-Title": "Atlas Revenue Intelligence",
        "X-OpenRouter-Metadata": "enabled",
    }

    tools_enabled = db is not None
    needs_web_search = bool(re.search(r"\b(hoy|actual|actualidad|evento|eventos|feria|concierto|clima|tiempo|noticia|noticias|fuente externa)\b", message.lower()))
    telemetry["webSearchRequested"] = needs_web_search
    tool_rounds_used = 0
    tool_calls_used = 0
    empty_retry_used = False
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        while True:
            allow_tools = tools_enabled and tool_rounds_used < MAX_TOOL_ROUNDS and tool_calls_used < MAX_TOOL_CALLS
            payload: dict[str, Any] = {
                "model": settings.model,
                "messages": messages,
                # Do not send ``temperature`` here.  OpenRouter's
                # ``require_parameters`` routing only selects endpoints that
                # support every parameter in the payload; the current Luna
                # endpoints (and several of the economic candidates) do not
                # advertise temperature.  Omitting it lets the provider use
                # its documented default while preserving strict routing.
                # Models still receive the per-mode max token budget below.
                # Reasoning models may spend part of that budget on internal
                # thinking before returning their visible answer.
                "max_tokens": policy["max_tokens"],
                # I1-06: pedir coste al proveedor (mismo patrón que reseñas en
                # flask_app.py). Sin `usage.include`, modelos sin `cost`
                # imputan 0 en `assistant_runs.cost_usd`.
                "usage": {"include": True},
                "provider": {
                    "require_parameters": True,
                    "data_collection": settings.data_collection,
                    "zdr": settings.zdr,
                },
            }
            if allow_tools:
                payload["tools"] = [*TOOLS, {
                    "type": "openrouter:web_search",
                    "parameters": {"engine": "auto", "max_results": 5, "max_total_results": 10,
                                    "search_context_size": "low"},
                }] if needs_web_search else TOOLS
                payload["tool_choice"] = "auto"

            try:
                data = _post_chat_completion(client, settings, headers, payload, deadline, telemetry)
            except AssistantError:
                # A 400 normally means an incompatible contract or malformed
                # request. Retrying without tools would silently remove the
                # evidence required to answer the question, so only the
                # bounded retry policy in _post_chat_completion applies.
                raise

            usage = data.get("usage")
            if isinstance(usage, dict):
                # I1-07: el coste imputado suma TODAS las rondas. Reutiliza
                # `_sum_usage` de `copilot_moa.py` (suma contadores sin asumir
                # forma del proveedor). Importación diferida para evitar ciclo
                # assistant <-> copilot_moa en tiempo de carga.
                try:
                    from .copilot_moa import _sum_usage as _sum_moa_usage  # type: ignore[import-not-found]
                except Exception:  # noqa: BLE001 - fallback local si el panel no está disponible
                    _sum_moa_usage = None  # type: ignore[assignment]
                if _sum_moa_usage is not None:
                    previous = telemetry.get("usage")
                    parts: list[dict[str, Any]] = []
                    if isinstance(previous, dict):
                        parts.append({"usage": previous})
                    parts.append({"usage": usage})
                    summed = _sum_moa_usage(parts)
                    telemetry["usage"] = summed if isinstance(summed, dict) else usage
                else:
                    previous = telemetry.get("usage")
                    if isinstance(previous, dict):
                        merged: dict[str, Any] = dict(previous)
                        for key, value in usage.items():
                            if isinstance(value, (int, float)) and not isinstance(value, bool):
                                prev_val = merged.get(key)
                                if isinstance(prev_val, (int, float)) and not isinstance(prev_val, bool):
                                    merged[key] = prev_val + value
                                else:
                                    merged[key] = value
                            elif key not in merged:
                                merged[key] = value
                        telemetry["usage"] = merged
                    else:
                        telemetry["usage"] = usage

            choices = data.get("choices") or []
            if not choices:
                raise AssistantError("OpenRouter no devolvió ninguna respuesta utilizable.")
            msg = choices[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []

            if tool_calls and allow_tools:
                tool_rounds_used += 1
                telemetry["toolRounds"] = tool_rounds_used
                available_calls = MAX_TOOL_CALLS - tool_calls_used
                bounded_tool_calls = tool_calls[:available_calls]
                messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": bounded_tool_calls})
                for call in bounded_tool_calls:
                    tool_calls_used += 1
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""
                    try:
                        arguments = json.loads(fn.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        arguments = {}
                    result = _run_tool(db, target_id, air_data, name, arguments, telemetry)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id"),
                            "content": json.dumps(result, ensure_ascii=False, default=str),
                        }
                    )
                continue  # nueva ronda con los resultados de las herramientas ya en `messages`

            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                telemetry["latencyMs"] = round((time.monotonic() - started) * 1000)
                telemetry["outcome"] = "success"
                return content.strip()

            # El modelo se quedó sin contenido (típico de modelos de razonamiento que agotan el
            # presupuesto de tokens "pensando"): un único reintento pidiendo la respuesta directa
            # suele bastar antes de rendirse con un error.
            if not empty_retry_used:
                empty_retry_used = True
                tools_enabled = False
                messages.append(
                    {
                        "role": "user",
                        "content": "Responde ya, en texto, con la mejor respuesta posible según lo que sabes. No uses más herramientas.",
                    }
                )
                continue

            raise AssistantError("La respuesta de OpenRouter llegó vacía.")
