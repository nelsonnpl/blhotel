"""Calendario de tarifas por hotel y fecha de entrada (panel de análisis · rate shopper).

Agrega las fotos de un mercado por ``check_in``: para cada fecha de entrada del horizonte se
usa la foto más reciente que la observó. Nunca se rellena una fecha sin captura.

Estados de cada celda (hotel × fecha):

* ``None``      la fecha no se ha capturado; no hay precio.
* ``"ok"``      tarifa observada que cumple los filtros.
* ``"low"``     tarifa observada con cupo bajo (``unitsLeft ≤ 2``).
* ``"closed"``  fecha capturada sin tarifa para el hotel: aparece agotado/cerrado, o no
                aparece en una captura **completa** (se recibieron todos los resultados).
* ``"unknown"`` el hotel no aparece en una captura **parcial**: su ausencia no prueba nada.
* ``"nomatch"`` hay tarifa, pero ninguna cumple el régimen o el tipo de habitación pedidos.

Precio efectivo: la tarifa por noche más baja que cumple régimen y tipo de habitación.
Si la foto tiene detalle de tarifas vinculado (``hotel_rate_details.snapshot_id``) se usan
todas sus habitaciones; si no, solo la tarifa que publica la búsqueda (habitación y régimen
de la fila). Un hotel sin ninguna tarifa que cumpla los filtros sale del análisis.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta

from .hotel_traits import detect_chain, is_adults_only

LOW_STOCK_UNITS = 2
MAX_DAYS = 120
EXTRACTIONS_LIMIT = 12

ROOM_FAMILIES = ("Doble", "Suite", "Familiar", "Bungalow / villa", "Apartamento", "Otra")


def _normalise(text: str | None) -> str:
    value = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in value if unicodedata.category(c) != "Mn").lower().strip()


def room_family(room_type: str | None) -> str:
    """Familia de habitación deducida del nombre; «Otra» si el nombre no lo indica."""
    name = _normalise(room_type)
    if re.search(r"\bsuite", name):
        return "Suite"
    if re.search(r"familiar|family", name):
        return "Familiar"
    if re.search(r"bungalow|villa", name):
        return "Bungalow / villa"
    if re.search(r"apartamento|apartment|estudio|studio", name):
        return "Apartamento"
    if re.search(r"doble|double|twin|matrimonio", name):
        return "Doble"
    return "Otra"


def board_category(board: str | None) -> str | None:
    """Régimen agrupado: los rótulos de Booking varían («Desayuno incluido (Bueno)»…)."""
    value = _normalise(board)
    if not value:
        return None
    if "todo incluido" in value or "all inclusive" in value:
        return "Todo incluido premium" if "premium" in value else "Todo incluido"
    if "almuerzo" in value and "cena" in value:
        return "Pensión completa"
    if "desayuno" in value and "cena" in value:
        return "Media pensión"
    if "desayuno" in value:
        return "Desayuno"
    if "solo alojamiento" in value or "solo habitacion" in value or "room only" in value:
        return "Solo alojamiento"
    return (board or "").strip() or None


def quantile(values: list[float], q: float) -> float | None:
    """Cuantil con interpolación lineal (el mismo método que usa el cliente)."""
    if not values:
        return None
    data = sorted(values)
    pos = (len(data) - 1) * q
    lo, hi = int(pos // 1), int(-(-pos // 1))
    return data[lo] + (data[hi] - data[lo]) * (pos - lo)


def _nights(check_in: str | None, check_out: str | None) -> int | None:
    try:
        n = (date.fromisoformat(str(check_out)[:10]) - date.fromisoformat(str(check_in)[:10])).days
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _zone_labels(rows: list[dict]) -> dict[str, str]:
    """Variantes de zona sin acento o con otras mayúsculas se unen en la más frecuente."""
    variants: dict[str, dict[str, int]] = {}
    for row in rows:
        label = (row.get("city") or row.get("popularDistrict") or row.get("displayLocation") or "").strip()
        if label:
            bucket = variants.setdefault(_normalise(label), {})
            bucket[label] = bucket.get(label, 0) + 1
    labels = {}
    for key, counts in variants.items():
        labels[key] = sorted(counts.items(), key=lambda item: (-item[1], not re.search(r"[^\x00-\x7f]", item[0]), item[0]))[0][0]
    return labels


def _snapshot_complete(snapshot) -> bool:
    status = (snapshot["capture_status"] or "unknown").lower()
    if status == "complete":
        return True
    if status in ("partial", "empty", "blocked", "error"):
        return False
    available, captured = snapshot["available_results"], snapshot["captured_rows"]
    return available is not None and captured is not None and captured >= available > 0


def _latest_snapshot_per_date(conn, target_id: int, start: date, end: date) -> dict[str, dict]:
    rows = conn.execute(
        """
        SELECT s.id, s.scraped_at, s.capture_status, s.available_results, s.captured_rows, h.check_in
        FROM market_snapshots s
        JOIN market_snapshot_hotels h ON h.snapshot_id = s.id
        WHERE s.target_id = ? AND h.check_in >= ? AND h.check_in < ?
        GROUP BY s.id, h.check_in
        """,
        (target_id, start.isoformat(), end.isoformat()),
    ).fetchall()
    chosen: dict[str, dict] = {}
    for row in rows:
        day = str(row["check_in"])[:10]
        current = chosen.get(day)
        if current is None or (row["scraped_at"], row["id"]) > (current["scraped_at"], current["id"]):
            chosen[day] = dict(row)
    return chosen


def _linked_rate_details(conn, snapshot_ids: list[int]) -> dict[tuple[int, str], list[dict]]:
    """Detalle de tarifas vinculado a cada foto (solo la captura de detalle más reciente)."""
    if not snapshot_ids:
        return {}
    marks = ",".join("?" for _ in snapshot_ids)
    rows = conn.execute(
        f"""
        SELECT snapshot_id, hotel_key, room_type, board, price_final, units_left, sold_out,
               check_in, check_out, captured_at
        FROM hotel_rate_details
        WHERE snapshot_id IN ({marks})
        ORDER BY captured_at DESC, id DESC
        """,
        snapshot_ids,
    ).fetchall()
    grouped: dict[tuple[int, str], list[dict]] = {}
    latest: dict[tuple[int, str], str] = {}
    for row in rows:
        key = (int(row["snapshot_id"]), row["hotel_key"])
        latest.setdefault(key, row["captured_at"])
        if row["captured_at"] == latest[key]:
            grouped.setdefault(key, []).append(dict(row))
    return grouped


def _candidates(row, details: list[dict] | None) -> list[dict]:
    """Tarifas por noche disponibles para un hotel en una foto."""
    if details:
        result = []
        for rate in details:
            nights = _nights(rate["check_in"], rate["check_out"])
            if rate["sold_out"] or rate["price_final"] is None or not nights:
                continue
            result.append({"price": float(rate["price_final"]) / nights, "board": rate["board"], "room": rate["room_type"], "units": rate["units_left"]})
        if result:
            return result
    if row.pricePerNight is None or row.pricePerNight <= 0:
        return []
    return [{"price": float(row.pricePerNight), "board": row.board, "room": row.roomType, "units": row.unitsLeft}]


def _matches(rate: dict, board: str, family: str) -> bool:
    if board != "all" and board_category(rate["board"]) != board:
        return False
    if family != "all" and room_family(rate["room"]) != family:
        return False
    return True


def _cell(row, details, board: str, family: str) -> tuple[float | None, str, int | None]:
    if row.soldOut or row.closed or row.observationStatus in ("closed", "unavailable_for_query"):
        return None, "closed", None
    rates = _candidates(row, details)
    if not rates:
        return None, "closed", None
    matching = [rate for rate in rates if _matches(rate, board, family)]
    if not matching:
        return None, "nomatch", None
    best = min(matching, key=lambda rate: rate["price"])
    units = best["units"]
    status = "low" if units is not None and 0 < int(units) <= LOW_STOCK_UNITS else "ok"
    return round(best["price"], 2), status, units


def build_rate_calendar(db, target_id: int, start: date, days: int, board: str = "all", family: str = "all") -> dict:
    days = max(1, min(MAX_DAYS, int(days)))
    end = start + timedelta(days=days)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    chosen = _latest_snapshot_per_date(db.conn, target_id, start, end)
    details = _linked_rate_details(db.conn, sorted({int(v["id"]) for v in chosen.values()}))
    snapshot_rows: dict[int, list] = {}
    for snapshot in chosen.values():
        sid = int(snapshot["id"])
        if sid not in snapshot_rows:
            snapshot_rows[sid] = [row for row in db.snapshot_rows(sid) if str(row.checkIn or "")[:10] in chosen]

    # universo del set: todos los hoteles observados en alguna fecha capturada del horizonte
    hotels: dict[str, dict] = {}
    raw_rows: list[dict] = []
    for day in sorted(chosen, key=lambda d: chosen[d]["scraped_at"]):
        for row in snapshot_rows[int(chosen[day]["id"])]:
            if str(row.checkIn)[:10] != day:
                continue
            raw = row.model_dump()
            raw_rows.append(raw)
            hotels[row.hotelKey] = raw  # gana la observación más reciente para los atributos
    zones = _zone_labels(raw_rows)

    board_facet: set[str] = set()
    family_facet: set[str] = set()
    index = {day: i for i, day in enumerate(dates)}
    prices = {key: [None] * days for key in hotels}
    status = {key: [None] * days for key in hotels}
    units = {key: [None] * days for key in hotels}
    coverage_dates: list[dict | None] = [None] * days
    for day, snapshot in chosen.items():
        i = index[day]
        sid = int(snapshot["id"])
        complete = _snapshot_complete(snapshot)
        present = {row.hotelKey: row for row in snapshot_rows[sid] if str(row.checkIn)[:10] == day}
        linked = any((sid, key) in details for key in present)
        coverage_dates[i] = {
            "date": day, "snapshotId": sid, "scrapedAt": snapshot["scraped_at"], "complete": complete,
            "observed": len(present), "available": snapshot["available_results"], "detail": linked,
        }
        for key in hotels:
            row = present.get(key)
            if row is None:
                status[key][i] = "closed" if complete else "unknown"
                continue
            for rate in _candidates(row, details.get((sid, key))):
                if rate["board"]:
                    board_facet.add(board_category(rate["board"]) or "")
                family_facet.add(room_family(rate["room"]))
            price, cell_status, cell_units = _cell(row, details.get((sid, key)), board, family)
            prices[key][i], status[key][i], units[key][i] = price, cell_status, cell_units

    in_scope = [key for key in hotels if any(p is not None for p in prices[key])]
    medians, p25, p75 = [], [], []
    for i in range(days):
        values = [prices[key][i] for key in in_scope if prices[key][i] is not None]
        medians.append(_round(quantile(values, 0.5)))
        p25.append(_round(quantile(values, 0.25)))
        p75.append(_round(quantile(values, 0.75)))

    hotel_list = []
    for key in in_scope:
        raw = hotels[key]
        label = (raw.get("city") or raw.get("popularDistrict") or raw.get("displayLocation") or "").strip()
        hotel_list.append({
            "key": key, "name": raw.get("hotelName"), "zone": zones.get(_normalise(label)) if label else None,
            "chain": detect_chain(raw.get("hotelName")), "adultsOnly": is_adults_only(raw.get("hotelName")),
            "rating": raw.get("rating"), "reviews": raw.get("reviewCount"),
            "lat": raw.get("latitude"), "lng": raw.get("longitude"),
            "prices": prices[key], "status": status[key], "units": units[key],
        })
    hotel_list.sort(key=lambda h: (h["name"] or "").lower())

    latest = db.latest_snapshot(target_id)
    latest_check_in = None
    if latest is not None:
        latest_rows = db.snapshot_rows(latest.id)
        latest_check_in = next((str(r.checkIn)[:10] for r in latest_rows if r.checkIn), None)

    return {
        "targetId": target_id, "from": start.isoformat(), "days": days, "board": board, "roomFamily": family,
        "dates": dates, "hotels": hotel_list, "medians": medians, "p25": p25, "p75": p75,
        "coverage": {
            "capturedDates": len(chosen), "hotels": len(hotels), "inScope": len(in_scope),
            "dates": coverage_dates, "lowStockUnits": LOW_STOCK_UNITS,
        },
        "facets": {
            "boards": sorted(b for b in board_facet if b),
            "roomFamilies": [f for f in ROOM_FAMILIES if f in family_facet],
        },
        "latestCheckIn": latest_check_in,
        "extractions": _extractions(db, target_id, board, family),
    }


def _extractions(db, target_id: int, board: str, family: str) -> list[dict]:
    """Mediana y banda P25–P75 de las últimas fotos, con el precio de cada hotel en cada una."""
    snapshots = list(reversed(db.snapshot_history(target_id, limit=EXTRACTIONS_LIMIT)))
    result = []
    for snapshot in snapshots:
        per_hotel = {}
        check_in = None
        for row in db.snapshot_rows(snapshot.id):
            check_in = check_in or (str(row.checkIn)[:10] if row.checkIn else None)
            if row.soldOut or row.closed:
                continue
            rates = [rate for rate in _candidates(row, None) if _matches(rate, board, family)]
            if rates:
                per_hotel[row.hotelKey] = round(min(rate["price"] for rate in rates), 2)
        values = list(per_hotel.values())
        result.append({
            "snapshotId": snapshot.id, "scrapedAt": snapshot.scrapedAt, "checkIn": check_in,
            "median": _round(quantile(values, 0.5)), "p25": _round(quantile(values, 0.25)), "p75": _round(quantile(values, 0.75)),
            "prices": per_hotel,
        })
    return result


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def parse_start(value: str | None, today: date | None = None) -> date:
    if not value:
        return today or datetime.now().date()
    return date.fromisoformat(value[:10])
