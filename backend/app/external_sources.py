"""Catálogo declarativo de fuentes públicas aptas para integrar en Market Desk.

El catálogo no descarga datos ni concede derechos de reutilización. Sirve para
que la aplicación exponga qué señal puede incorporarse, con qué granularidad y
qué credencial o revisión legal falta antes de activar un conector.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ExternalSourceDefinition:
    id: str
    provider: str
    dataset: str
    url: str
    granularity: str
    access: str
    requires_api_key: bool
    decision_uses: tuple[str, ...]
    license_note: str
    recommended_datasets: tuple[dict[str, str], ...] = ()


PUBLIC_SOURCE_CATALOG: tuple[ExternalSourceDefinition, ...] = (
    ExternalSourceDefinition(
        id="istac-accommodation",
        provider="ISTAC",
        dataset="Encuesta de alojamientos turísticos",
        url="https://www3.gobiernodecanarias.org/istac/statistical-visualizer/visualizer/collection.html?agencyId=ISTAC&resourceId=C00065A_000001&resourceType=collection",
        granularity="mensual / anual",
        access="open_catalog",
        requires_api_key=False,
        decision_uses=("benchmark de destino", "estacionalidad", "capacidad"),
        license_note="Conservar fecha de publicación y revisión de la serie.",
        recommended_datasets=(
            {
                "id": "C00065A_000001",
                "name": "Encuesta de alojamientos turísticos",
                "cadence": "mensual / anual",
                "priority": "P1",
                "use": "benchmark de ocupación, tarifas e ingresos",
            },
            {
                "id": "C00065A_000038",
                "name": "Alojamiento por microdestino: plazas, ocupación, ADR y RevPAR",
                "cadence": "anual",
                "priority": "P0",
                "use": "benchmark territorial fino de ADR y RevPAR",
            },
            {
                "id": "C00065A_000060",
                "name": "Pernoctaciones, viajeros y estancia por residencia",
                "cadence": "mensual / anual",
                "priority": "P1",
                "use": "mix de mercados y demanda territorial",
            },
            {
                "id": "C00065A_000059",
                "name": "Pernoctaciones, viajeros y estancia por nacionalidad",
                "cadence": "mensual / anual",
                "priority": "P1",
                "use": "mix de mercados emisores",
            },
        ),
    ),
    ExternalSourceDefinition(
        id="dataestur-segittur",
        provider="Dataestur / SEGITTUR",
        dataset="Indicadores turísticos y conectividad",
        url="https://www.dataestur.es/apidata/",
        granularity="mensual / variable",
        access="open_api",
        requires_api_key=False,
        decision_uses=("benchmark nacional", "mercados emisores", "conectividad"),
        license_note="Validar condiciones de cada endpoint antes de redistribuir valores.",
        recommended_datasets=(
            {
                "id": "PRECIOS_ALOJAMIENTOS_HOTELEROS_DL",
                "name": "Precio medio por antelación y check-in",
                "cadence": "mensual",
                "priority": "P0",
                "use": "calibración de curva de lead time",
            },
            {
                "id": "IND_RENTABILIDAD_PUNT_TUR_DL",
                "name": "Rentabilidad hotelera por punto turístico",
                "cadence": "mensual",
                "priority": "P1",
                "use": "benchmark de ADR/RevPAR y rentabilidad",
            },
            {
                "id": "CONECTIVIDAD_AEREA_BUSQUEDAS_INICIO_VIAJE_DL",
                "name": "Búsquedas aéreas por inicio del viaje",
                "cadence": "mensual",
                "priority": "P1",
                "use": "señal temprana de intención, no ocupación",
            },
            {
                "id": "CONECTIVIDAD_AEREA_RESERVAS_INICIO_VIAJE_DL",
                "name": "Reservas aéreas por inicio del viaje",
                "cadence": "mensual",
                "priority": "P1",
                "use": "señal de conversión de conectividad",
            },
            {
                "id": "CONECTIVIDAD_AEREA_CAPACIDAD_DL",
                "name": "Capacidad aérea programada",
                "cadence": "mensual",
                "priority": "P2",
                "use": "explicar shocks de oferta de transporte",
            },
            {
                "id": "GASTO_TPV_DESTINO_PROV_MES_ACTUAL_DL",
                "name": "Gasto y transacciones TPV en destino",
                "cadence": "mensual",
                "priority": "P2",
                "use": "contexto de poder de gasto del destino",
            },
        ),
    ),
    ExternalSourceDefinition(
        id="aemet-opendata",
        provider="AEMET",
        dataset="Observación, predicción y avisos meteorológicos",
        url="https://opendata.aemet.es/dist/index.html",
        granularity="horaria / diaria",
        access="open_api",
        requires_api_key=True,
        decision_uses=("contexto de destino", "avisos operativos", "explicación de shocks"),
        license_note="Requiere API key y respetar límites de consulta.",
    ),
    ExternalSourceDefinition(
        id="aena-traffic",
        provider="Aena",
        dataset="Estadísticas de tráfico aeroportuario",
        url="https://www.aena.es/es/estadisticas/inicio.html",
        granularity="mensual",
        access="open_web",
        requires_api_key=False,
        decision_uses=("accesibilidad aérea", "capacidad por aeropuerto"),
        license_note="Pasajeros y operaciones no equivalen a reservas hoteleras.",
    ),
    ExternalSourceDefinition(
        id="eurostat-tourism",
        provider="Eurostat",
        dataset="Tourism statistics",
        url="https://ec.europa.eu/eurostat/web/tourism/information-data",
        granularity="mensual / trimestral / anual",
        access="open_data",
        requires_api_key=False,
        decision_uses=("benchmark europeo", "control de coherencia"),
        license_note="Conservar versión y posibles revisiones estadísticas.",
    ),
)


def public_source_catalog() -> list[dict]:
    """Devuelve una copia JSON segura del catálogo, sin secretos ni payloads."""
    return [
        {
            **asdict(source),
            "decision_uses": list(source.decision_uses),
            "recommended_datasets": [dict(dataset) for dataset in source.recommended_datasets],
        }
        for source in PUBLIC_SOURCE_CATALOG
    ]
