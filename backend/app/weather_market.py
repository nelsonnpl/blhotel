"""Agrupación geográfica conservadora para consultas meteorológicas."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def coordinate_cell(latitude: float, longitude: float, precision: int = 2) -> str:
    """Devuelve una celda estable de aproximadamente 1 km sin falsear precisión."""
    return f"cell:{latitude:.{precision}f}:{longitude:.{precision}f}"


def cluster_market_rows(rows: Iterable, precision: int = 2) -> dict[str, dict]:
    """Agrupa hoteles por celda y conserva asignaciones hotel → celda."""
    groups: dict[str, dict] = {}
    for row in rows:
        if row.latitude is None or row.longitude is None:
            continue
        key = coordinate_cell(float(row.latitude), float(row.longitude), precision)
        group = groups.setdefault(key, {"locationKey": key, "latitude": [], "longitude": [], "hotelKeys": []})
        group["latitude"].append(float(row.latitude))
        group["longitude"].append(float(row.longitude))
        group["hotelKeys"].append(row.hotelKey)
    for group in groups.values():
        group["latitude"] = round(sum(group["latitude"]) / len(group["latitude"]), 6)
        group["longitude"] = round(sum(group["longitude"]) / len(group["longitude"]), 6)
    return groups
