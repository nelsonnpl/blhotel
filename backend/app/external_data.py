"""Descarga y normalización de indicadores públicos para la caché de Atlas.

Este módulo no persiste respuestas originales. Cada adaptador devuelve filas
pequeñas y normalizadas que :class:`Database` puede hacer upsert. Las funciones
aceptan un cliente HTTP opcional para que los tests no necesiten red.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import re
import unicodedata
from typing import Any, Iterable

import httpx

from .database import Database


DATAESTUR_API_BASE = "https://www.dataestur.es/API-SEGITTUR-v2"
ISTAC_DATASET_URL = (
    "https://datos.canarias.es/api/estadisticas/statistical-resources/v1.0/"
    "datasets/ISTAC/{dataset_id}/{version}.csv"
)
DATAESTUR_RETENTION_MONTHS = 24
ISTAC_RETENTION_MONTHS = 36
ISTAC_P0_TERRITORY_CODES = ("ES70", "ES705")


class ExternalDataError(RuntimeError):
    """Error controlado de transporte o formato de una fuente externa."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _period_cutoff(months: int) -> str:
    """Devuelve el primer día del mes usado para la retención de la caché."""
    now = datetime.now(timezone.utc)
    index = now.year * 12 + (now.month - 1) - max(1, int(months))
    year, month_index = divmod(index, 12)
    return f"{year:04d}-{month_index + 1:02d}-01"


def _expiry_at(fetched_at: str, days: int) -> str:
    try:
        base = datetime.fromisoformat(fetched_at)
    except (TypeError, ValueError):
        base = datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    return (base + timedelta(days=days)).isoformat()


def _decode_csv(payload: bytes) -> str:
    """Dataestur sirve CSV en Windows-1252; ISTAC suele servir UTF-8."""
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ExternalDataError("No se pudo decodificar el CSV recibido")


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("\u00a0", "")
    if not text or text in {"-", "—", "..", "NA", "N/A"}:
        return None
    text = text.replace("%", "").replace(" ", "")
    # Los CSV estadísticos españoles usan coma decimal y punto de millar.
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value == value and abs(value) != float("inf") else None


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _header_map(headers: Iterable[str]) -> dict[str, str]:
    """Indexa encabezados y sus variantes localizadas de los CSV SDMX.

    ISTAC publica con frecuencia una etiqueta como ``TERRITORIO#es`` junto a
    su código. Conservamos el encabezado original para leer el valor, pero
    aceptamos también la clave semántica ``territorio``. Así el adaptador no
    depende del idioma concreto de la exportación.
    """
    result: dict[str, str] = {}
    for header in headers:
        if not header:
            continue
        normalized = _key(header)
        result[normalized] = header
        localized = re.sub(r"_(?:es|en|fr|de|pt)$", "", normalized)
        if localized != normalized:
            result.setdefault(localized, header)
    return result


def _first(row: dict[str, Any], headers: dict[str, str], candidates: Iterable[str]) -> Any:
    for candidate in candidates:
        header = headers.get(_key(candidate))
        if header is not None:
            value = row.get(header)
            if value not in (None, ""):
                return value
    return None


def _month_end(year: int, month: int) -> str:
    next_month = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1)
    return (next_month - timedelta(days=1)).date().isoformat()


def _period(row: dict[str, Any], headers: dict[str, str]) -> tuple[str, str, str]:
    """Lee periodo mensual o anual y conserva su alcance temporal completo."""
    raw = _first(row, headers, ("time_period", "periodo", "period", "fecha", "date"))
    raw_code = _first(row, headers, ("time_period_code", "periodo_code", "period_code"))
    for candidate in (raw_code, raw):
        if not candidate:
            continue
        text = str(candidate).strip()
        monthly = re.fullmatch(r"(\d{4})-M(\d{2})", text, flags=re.IGNORECASE)
        monthly = monthly or re.fullmatch(r"(\d{4})[-/](\d{2})", text)
        monthly = monthly or re.fullmatch(r"(\d{2})/(\d{4})", text)
        if monthly:
            first, second = (int(monthly.group(1)), int(monthly.group(2)))
            year, month = (second, first) if len(monthly.group(1)) == 2 else (first, second)
            if 1900 <= year <= 2200 and 1 <= month <= 12:
                return f"{year:04d}-{month:02d}-01", _month_end(year, month), str(raw or text)
        annual = re.fullmatch(r"(\d{4})", text)
        if annual:
            year = int(annual.group(1))
            if 1900 <= year <= 2200:
                return f"{year:04d}-01-01", f"{year:04d}-12-31", str(raw or text)
    year = _first(row, headers, ("ano", "año", "anio", "year"))
    month = _first(row, headers, ("mes", "month"))
    try:
        year_int = int(str(year).strip())
        month_int = int(str(month or 1).strip())
        if 1900 <= year_int <= 2200 and 1 <= month_int <= 12:
            return (
                f"{year_int:04d}-{month_int:02d}-01",
                _month_end(year_int, month_int),
                str(year_int),
            )
    except (TypeError, ValueError):
        pass
    return "", "", ""


def parse_dataestur_hotel_prices(payload: bytes, *, fetched_at: str | None = None) -> list[dict]:
    """Convierte PRECIOS_ALOJAMIENTOS_HOTELEROS_DL en filas de caché.

    Se generan dos métricas por registro (entre semana y fin de semana). Los
    campos de categoría y antelación forman el segmento, no se mezclan con el
    valor numérico.
    """
    text = _decode_csv(payload)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    headers = _header_map(reader.fieldnames or [])
    required = {
        "ano": headers.get("ano") or headers.get("año"),
        "mes": headers.get("mes"),
        "categoria": headers.get("categoria_alojamiento"),
        "ccaa": headers.get("ccaa"),
        "provincia": headers.get("provincia"),
        "lead": headers.get("periodo_antelacion"),
        "weekday": headers.get("precio_check_in_entre_semana"),
        # El encabezado ha aparecido con y sin "DE" en distintas revisiones.
        "weekend": headers.get("precio_check_in_fin_de_semana") or headers.get("precio_check_in_fin_semana"),
    }
    missing = [name for name, header in required.items() if header is None]
    if missing:
        raise ExternalDataError(f"CSV Dataestur sin columnas: {', '.join(missing)}")
    fetched = fetched_at or _now()
    rows: list[dict] = []
    for source in reader:
        year = str(source.get(required["ano"] or "") or "").strip()
        month = str(source.get(required["mes"] or "") or "").strip()
        try:
            period_start = f"{int(year):04d}-{int(month):02d}-01"
        except (TypeError, ValueError):
            continue
        category = str(source.get(required["categoria"] or "") or "").strip()
        ccaa = str(source.get(required["ccaa"] or "") or "").strip()
        province = str(source.get(required["provincia"] or "") or "").strip()
        lead = str(source.get(required["lead"] or "") or "").strip()
        if not category or not ccaa or not province or not lead:
            continue
        for day_type, field in (("weekday", required["weekday"]), ("weekend", required["weekend"])):
            value = _number(source.get(field or ""))
            if value is None:
                continue
            rows.append(
                {
                    "sourceId": "dataestur-segittur",
                    "datasetId": "PRECIOS_ALOJAMIENTOS_HOTELEROS_DL",
                    "metric": "hotel_price_by_lead_time",
                    "unit": "EUR/room_night",
                    "geographyType": "province",
                    "geographyCode": province,
                    "segment": f"category={category};lead_time={lead};day_type={day_type}",
                    "periodStart": period_start,
                    "value": value,
                    "fetchedAt": fetched,
                    "expiresAt": _expiry_at(fetched, 45),
                    "qualityStatus": "ok",
                    "payloadHash": _sha256(payload),
                    "metadata": {
                        "ccaa": ccaa,
                        "province": province,
                        "category": category,
                        "leadTime": lead,
                        "dayType": day_type,
                    },
                }
            )
    return rows


def fetch_dataestur_hotel_prices(
    database: Database,
    *,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    ccaa: str = "Canarias",
    province: str = "Todos",
    client: httpx.Client | None = None,
) -> dict:
    """Descarga el endpoint P0 de precios y actualiza la caché normalizada."""
    url = f"{DATAESTUR_API_BASE}/PRECIOS_ALOJAMIENTOS_HOTELEROS_DL"
    params = {
        "desde (año)": start_year,
        "desde (mes)": start_month,
        "hasta (año)": end_year,
        "hasta (mes)": end_month,
        "CCAA": ccaa,
        "Provincia": province,
    }
    scope = {
        "startYear": start_year,
        "startMonth": start_month,
        "endYear": end_year,
        "endMonth": end_month,
        "ccaa": ccaa,
        "province": province,
    }
    run_id = database.start_external_ingestion(
        "dataestur-segittur", "PRECIOS_ALOJAMIENTOS_HOTELEROS_DL", scope
    )
    own_client = client is None
    http = client or httpx.Client(timeout=30, follow_redirects=True)
    try:
        response = http.get(url, params=params, headers={"Accept": "text/csv, application/octet-stream"})
        response.raise_for_status()
        observations = parse_dataestur_hotel_prices(response.content)
    except (httpx.HTTPError, ExternalDataError) as exc:
        database.finish_external_ingestion(run_id, status="error", error=str(exc))
        raise ExternalDataError(f"No se pudo descargar Dataestur: {exc}") from exc
    finally:
        if own_client:
            http.close()
    count = database.upsert_external_observations(observations)
    purged = database.purge_external_observations(
        _period_cutoff(DATAESTUR_RETENTION_MONTHS),
        source_id="dataestur-segittur",
        dataset_id="PRECIOS_ALOJAMIENTOS_HOTELEROS_DL",
    )
    payload_hash = _sha256(response.content)
    database.finish_external_ingestion(
        run_id, status="success", row_count=count, payload_hash=payload_hash
    )
    return {
        "sourceId": "dataestur-segittur",
        "datasetId": "PRECIOS_ALOJAMIENTOS_HOTELEROS_DL",
        "runId": run_id,
        "downloadedRows": len(observations),
        "upsertedRows": count,
        "purgedRows": purged,
        "payloadHash": payload_hash,
    }


def parse_istac_csv(payload: bytes, *, dataset_id: str, fetched_at: str | None = None) -> list[dict]:
    """Normaliza CSV largo o ancho de ISTAC sin conservar el fichero original.

    El adaptador tolera tanto filas con ``OBS_VALUE`` + indicador como cubos
    anchos con columnas ADR/RevPAR/ocupación. Conserva únicamente las métricas
    de benchmark definidas para Atlas (tarifa, ingreso, ocupación, capacidad y
    volumen). Si la estructura cambia, omite la fila ambigua o fuera de alcance
    para evitar insertar métricas mal etiquetadas.
    """
    text = _decode_csv(payload)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = None
    reader = (
        csv.DictReader(io.StringIO(text), dialect=dialect)
        if dialect is not None
        else csv.DictReader(io.StringIO(text), delimiter=";")
    )
    headers = _header_map(reader.fieldnames or [])
    fetched = fetched_at or _now()
    digest = _sha256(payload)
    rows: list[dict] = []
    geo_candidates = (
        ("microdestination", "microdestino"),
        ("microdestination", "microdestino turistico"),
        ("territory", "territorio"),
        ("municipality", "municipio"),
        ("island", "isla"),
        ("zone", "zona"),
    )
    value_candidates = ("obs_value", "value", "valor", "dato", "observacion", "observación")
    indicator_candidates = ("indicador", "medida", "medidas", "metric", "concepto", "variable")
    for source in reader:
        period_start, period_end, raw_period = _period(source, headers)
        geography_type = None
        geography = None
        for candidate_type, candidate_name in geo_candidates:
            candidate_value = _first(source, headers, (candidate_name,))
            if candidate_value:
                geography_type, geography = candidate_type, candidate_value
                break
        if not period_start or not geography or not geography_type:
            continue
        indicator = _first(source, headers, indicator_candidates)
        value_header = next((headers.get(_key(candidate)) for candidate in value_candidates if headers.get(_key(candidate))), None)
        candidates: list[tuple[str, Any]] = []
        if value_header and indicator:
            candidates.append((str(indicator), source.get(value_header)))
        else:
            for key, header in headers.items():
                if any(token in key for token in ("adr", "revpar", "ocupacion", "plazas", "viajeros", "pernoct")):
                    candidates.append((header, source.get(header)))
        for metric_raw, raw_value in candidates:
            value = _number(raw_value)
            if value is None:
                continue
            metric_key = _key(metric_raw)
            if "empleo" in metric_key:
                continue
            if "revpar" in metric_key or ("ingreso" in metric_key and "habitacion" in metric_key):
                metric, unit = "revpar", "EUR/room_night"
            elif "adr" in metric_key or "tarifa" in metric_key:
                metric, unit = "adr", "EUR/room_night"
            elif "ocupacion" in metric_key:
                metric, unit = "occupancy_rate", "percent"
            elif ("plaza" in metric_key or "habitacion" in metric_key) and "ingreso" not in metric_key:
                metric, unit = "accommodation_capacity", "units"
            elif "viajero" in metric_key or "pernoct" in metric_key:
                metric, unit = "travellers_or_nights", "persons_or_nights"
            else:
                continue
            segment_parts = [str(indicator or "").strip()]
            accommodation_type = _first(
                source,
                headers,
                ("alojamiento_turistico_tipo", "tipo_alojamiento", "accommodation_type"),
            )
            accommodation_category = _first(
                source,
                headers,
                ("alojamiento_turistico_categoria", "categoria_alojamiento", "accommodation_category"),
            )
            if accommodation_type:
                segment_parts.append(f"accommodation_type={str(accommodation_type).strip()}")
            if accommodation_category:
                segment_parts.append(f"accommodation_category={str(accommodation_category).strip()}")
            rows.append(
                {
                    "sourceId": "istac-accommodation",
                    "datasetId": dataset_id,
                    "metric": metric,
                    "unit": unit,
                    "geographyType": geography_type,
                    "geographyCode": str(geography).strip(),
                    "segment": ";".join(part for part in segment_parts if part),
                    "periodStart": period_start,
                    "periodEnd": period_end,
                    "value": value,
                    "fetchedAt": fetched,
                    "expiresAt": _expiry_at(fetched, 120),
                    "qualityStatus": "ok",
                    "payloadHash": digest,
                    "metadata": {
                        "rawPeriod": raw_period,
                        "periodGranularity": "annual" if period_end.endswith("-12-31") else "monthly",
                        "officialGeographyCode": str(
                            _first(source, headers, (f"{geography_type}_code", "territorio_code")) or ""
                        ).strip() or None,
                        "accommodationType": str(accommodation_type).strip() if accommodation_type else None,
                        "accommodationCategory": str(accommodation_category).strip() if accommodation_category else None,
                        "label": str(metric_raw).strip(),
                    },
                }
            )
    return rows


def filter_istac_territories(observations: list[dict], territory_codes: Iterable[str]) -> list[dict]:
    """Restringe la caché a territorios oficiales solicitados explícitamente.

    La descarga de ISTAC es un cubo completo. Su respuesta se procesa en
    memoria, pero solo se persiste el ámbito de trabajo; las respuestas crudas
    y los territorios ajenos no llegan a SQLite.
    """
    allowed = {str(code).strip().upper() for code in territory_codes if str(code).strip()}
    if not allowed:
        return observations
    return [
        item for item in observations
        if str((item.get("metadata") or {}).get("officialGeographyCode") or "").upper() in allowed
    ]


def fetch_istac_csv(
    database: Database,
    *,
    dataset_id: str,
    version: str,
    territory_codes: Iterable[str] = (),
    client: httpx.Client | None = None,
) -> dict:
    """Descarga un cubo ISTAC CSV y almacena solo sus filas interpretables."""
    url = ISTAC_DATASET_URL.format(dataset_id=dataset_id, version=version)
    territory_codes = tuple(str(code).strip().upper() for code in territory_codes if str(code).strip())
    run_id = database.start_external_ingestion(
        "istac-accommodation", dataset_id, {"version": version, "territoryCodes": list(territory_codes)}
    )
    own_client = client is None
    http = client or httpx.Client(timeout=45, follow_redirects=True)
    try:
        response = http.get(url, headers={"Accept": "text/csv, text/tab-separated-values"})
        response.raise_for_status()
        observations = parse_istac_csv(response.content, dataset_id=dataset_id)
        observations = filter_istac_territories(observations, territory_codes)
        if not observations:
            raise ExternalDataError(
                "CSV ISTAC sin filas normalizables para el ámbito solicitado; no se actualizó la caché"
            )
    except (httpx.HTTPError, ExternalDataError) as exc:
        database.finish_external_ingestion(run_id, status="error", error=str(exc))
        raise ExternalDataError(f"No se pudo descargar ISTAC: {exc}") from exc
    finally:
        if own_client:
            http.close()
    count = database.upsert_external_observations(observations)
    purged = database.purge_external_observations(
        _period_cutoff(ISTAC_RETENTION_MONTHS), source_id="istac-accommodation", dataset_id=dataset_id
    )
    payload_hash = _sha256(response.content)
    database.finish_external_ingestion(
        run_id, status="success", row_count=count, payload_hash=payload_hash
    )
    return {
        "sourceId": "istac-accommodation",
        "datasetId": dataset_id,
        "runId": run_id,
        "territoryCodes": list(territory_codes),
        "downloadedRows": len(observations),
        "upsertedRows": count,
        "purgedRows": purged,
        "payloadHash": payload_hash,
    }
