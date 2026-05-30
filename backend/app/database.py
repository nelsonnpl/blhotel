from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from statistics import median
from threading import RLock

from .models import MarketHotelRow, MarketSnapshot, RevenueInsight, SearchTarget


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.lock = RLock()
        self.init()

    def init(self) -> None:
        with self.lock:
            self.conn.execute("PRAGMA journal_mode = WAL;")
            self.conn.execute("PRAGMA busy_timeout = 30000;")
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS search_targets (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              url TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS market_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              target_id INTEGER NOT NULL,
              source_url TEXT NOT NULL,
              requested_limit INTEGER NOT NULL,
              available_results INTEGER NOT NULL,
              captured_rows INTEGER NOT NULL,
              scraped_at TEXT NOT NULL,
              raw_hash TEXT NOT NULL,
              FOREIGN KEY(target_id) REFERENCES search_targets(id)
            );

            CREATE INDEX IF NOT EXISTS idx_market_snapshots_target_scraped
              ON market_snapshots(target_id, scraped_at DESC);

            CREATE TABLE IF NOT EXISTS hotel_locations (
              hotel_key TEXT PRIMARY KEY,
              detail_url TEXT NOT NULL,
              latitude REAL,
              longitude REAL,
              address TEXT,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_snapshot_hotels (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              snapshot_id INTEGER NOT NULL,
              hotel_key TEXT NOT NULL,
              hotel_name TEXT NOT NULL,
              detail_url TEXT NOT NULL,
              room_type TEXT,
              rating REAL,
              price REAL,
              price_text TEXT,
              currency TEXT,
              pax INTEGER,
              check_in TEXT,
              check_out TEXT,
              nights INTEGER,
              price_per_night REAL,
              price_per_person_night REAL,
              position INTEGER NOT NULL,
              location_status TEXT NOT NULL DEFAULT 'location_pending',
              FOREIGN KEY(snapshot_id) REFERENCES market_snapshots(id),
              FOREIGN KEY(hotel_key) REFERENCES hotel_locations(hotel_key)
            );

            CREATE INDEX IF NOT EXISTS idx_market_snapshot_hotels_snapshot
              ON market_snapshot_hotels(snapshot_id, position ASC);
            """
            )
            self.conn.commit()
        self._ensure_column("market_snapshot_hotels", "price_per_night", "REAL")
        self._ensure_column("market_snapshot_hotels", "price_per_person_night", "REAL")

    def _ensure_column(self, table: str, column: str, column_type: str) -> None:
        with self.lock:
            columns = [row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})")]
            if column not in columns:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                self.conn.commit()

    def list_targets(self) -> list[SearchTarget]:
        rows = self.conn.execute(
            """
            SELECT id, name, url, created_at AS createdAt, updated_at AS updatedAt
            FROM search_targets
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [SearchTarget(**dict(row)) for row in rows]

    def upsert_target(self, name: str, url: str) -> SearchTarget:
        now = _now()
        with self.lock:
            self.conn.execute(
            """
            INSERT INTO search_targets (name, url, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET name = excluded.name, updated_at = excluded.updated_at
            """,
            (name, url, now),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT id, name, url, created_at AS createdAt, updated_at AS updatedAt FROM search_targets WHERE url = ?",
                (url,),
            ).fetchone()
        return SearchTarget(**dict(row))

    def update_target(self, target_id: int, name: str, url: str) -> SearchTarget:
        now = _now()
        with self.lock:
            self.conn.execute(
                """
                UPDATE search_targets
                SET name = ?, url = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, url, now, target_id),
            )
            self.conn.commit()
        updated = self.get_target(target_id)
        if updated is None:
            raise ValueError(f"No existe target con id {target_id}")
        return updated

    def get_target(self, target_id: int) -> SearchTarget | None:
        row = self.conn.execute(
            "SELECT id, name, url, created_at AS createdAt, updated_at AS updatedAt FROM search_targets WHERE id = ?",
            (target_id,),
        ).fetchone()
        return SearchTarget(**dict(row)) if row else None

    def create_snapshot(self, target_id: int, source_url: str, requested_limit: int, available_results: int, captured_rows: int, raw_hash: str) -> MarketSnapshot:
        scraped_at = _now()
        with self.lock:
            cursor = self.conn.execute(
            """
            INSERT INTO market_snapshots (target_id, source_url, requested_limit, available_results, captured_rows, scraped_at, raw_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (target_id, source_url, requested_limit, available_results, captured_rows, scraped_at, raw_hash),
            )
            self.conn.commit()
        return MarketSnapshot(
            id=int(cursor.lastrowid),
            targetId=target_id,
            sourceUrl=source_url,
            requestedLimit=requested_limit,
            availableResults=available_results,
            capturedRows=captured_rows,
            scrapedAt=scraped_at,
        )

    def get_location(self, hotel_key: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM hotel_locations WHERE hotel_key = ?", (hotel_key,)).fetchone()

    def upsert_location(self, hotel_key: str, detail_url: str, latitude: float | None, longitude: float | None, address: str | None) -> None:
        with self.lock:
            self.conn.execute(
            """
            INSERT INTO hotel_locations (hotel_key, detail_url, latitude, longitude, address, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hotel_key) DO UPDATE SET
              detail_url = excluded.detail_url,
              latitude = excluded.latitude,
              longitude = excluded.longitude,
              address = excluded.address,
              updated_at = excluded.updated_at
            """,
            (hotel_key, detail_url, latitude, longitude, address, _now()),
            )
            self.conn.commit()

    def insert_market_hotel(self, snapshot_id: int, row: MarketHotelRow, location_status: str) -> None:
        with self.lock:
            self.conn.execute(
            """
            INSERT INTO market_snapshot_hotels (
              snapshot_id, hotel_key, hotel_name, detail_url, room_type, rating, price, price_text, currency, pax,
              check_in, check_out, nights, price_per_night, price_per_person_night, position, location_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                row.hotelKey,
                row.hotelName,
                row.detailUrl,
                row.roomType,
                row.rating,
                row.price,
                row.priceText,
                row.currency,
                row.pax,
                row.checkIn,
                row.checkOut,
                row.nights,
                row.pricePerNight,
                row.pricePerPersonPerNight,
                row.position,
                location_status,
            ),
            )
            self.conn.commit()

    def latest_snapshot(self, target_id: int) -> MarketSnapshot | None:
        row = self.conn.execute(
            """
            SELECT id, target_id AS targetId, source_url AS sourceUrl, requested_limit AS requestedLimit,
                   available_results AS availableResults, captured_rows AS capturedRows, scraped_at AS scrapedAt
            FROM market_snapshots
            WHERE target_id = ?
            ORDER BY scraped_at DESC, id DESC
            LIMIT 1
            """,
            (target_id,),
        ).fetchone()
        return MarketSnapshot(**dict(row)) if row else None

    def snapshot_history(self, target_id: int, limit: int = 20) -> list[MarketSnapshot]:
        rows = self.conn.execute(
            """
            SELECT id, target_id AS targetId, source_url AS sourceUrl, requested_limit AS requestedLimit,
                   available_results AS availableResults, captured_rows AS capturedRows, scraped_at AS scrapedAt
            FROM market_snapshots
            WHERE target_id = ?
            ORDER BY scraped_at DESC, id DESC
            LIMIT ?
            """,
            (target_id, limit),
        ).fetchall()
        return [MarketSnapshot(**dict(row)) for row in rows]

    def snapshot_rows(self, snapshot_id: int) -> list[MarketHotelRow]:
        rows = self.conn.execute(
            """
            SELECT
              msh.id AS id,
              msh.snapshot_id AS snapshotId,
              msh.hotel_key AS hotelKey,
              msh.hotel_name AS hotelName,
              msh.detail_url AS detailUrl,
              msh.room_type AS roomType,
              msh.rating AS rating,
              msh.price AS price,
              msh.price_text AS priceText,
              msh.currency AS currency,
              msh.pax AS pax,
              msh.check_in AS checkIn,
              msh.check_out AS checkOut,
              msh.nights AS nights,
              msh.price_per_night AS pricePerNight,
              msh.price_per_person_night AS pricePerPersonPerNight,
              msh.position AS position,
              msh.location_status AS locationStatus,
              hl.latitude AS latitude,
              hl.longitude AS longitude,
              hl.address AS address
            FROM market_snapshot_hotels msh
            LEFT JOIN hotel_locations hl ON hl.hotel_key = msh.hotel_key
            WHERE msh.snapshot_id = ?
            ORDER BY msh.position ASC
            """,
            (snapshot_id,),
        ).fetchall()
        return [MarketHotelRow(**dict(row)) for row in rows]

    def photo_history(self, target_id: int, limit: int = 24) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT
              ms.id AS id,
              ms.target_id AS targetId,
              ms.scraped_at AS scrapedAt,
              ms.captured_rows AS capturedRows,
              ms.available_results AS availableResults,
              AVG(COALESCE(msh.price_per_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END)) AS avgPricePerNight,
              AVG(COALESCE(msh.price_per_person_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 AND msh.pax > 0 THEN msh.price * 1.0 / msh.nights / msh.pax END)) AS avgPricePerPersonNight,
              AVG(msh.price) AS avgPriceTotal,
              MIN(COALESCE(msh.price_per_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END)) AS minPricePerNight,
              MAX(COALESCE(msh.price_per_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END)) AS maxPricePerNight,
              SUM(CASE WHEN msh.price IS NOT NULL THEN 1 ELSE 0 END) AS pricedRows,
              SUM(CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN 1 ELSE 0 END) AS comparableRows
            FROM market_snapshots ms
            LEFT JOIN market_snapshot_hotels msh ON msh.snapshot_id = ms.id
            WHERE ms.target_id = ?
            GROUP BY ms.id
            ORDER BY ms.scraped_at DESC, ms.id DESC
            LIMIT ?
            """,
            (target_id, limit),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "targetId": row["targetId"],
                "scrapedAt": row["scrapedAt"],
                "capturedRows": row["capturedRows"],
                "availableResults": row["availableResults"],
                "avgPricePerNight": _round(row["avgPricePerNight"] or 0),
                "avgPricePerPersonNight": _round(row["avgPricePerPersonNight"] or 0),
                "avgPriceTotal": _round(row["avgPriceTotal"] or 0),
                "minPricePerNight": _round(row["minPricePerNight"] or 0),
                "maxPricePerNight": _round(row["maxPricePerNight"] or 0),
                "pricedRows": int(row["pricedRows"] or 0),
                "comparableRows": int(row["comparableRows"] or 0),
            }
            for row in rows
        ]

    def photo_detail(self, snapshot_id: int) -> dict | None:
        snapshot = self.conn.execute(
            """
            SELECT id, target_id AS targetId, source_url AS sourceUrl, requested_limit AS requestedLimit,
                   available_results AS availableResults, captured_rows AS capturedRows, scraped_at AS scrapedAt
            FROM market_snapshots
            WHERE id = ?
            """,
            (snapshot_id,),
        ).fetchone()
        if snapshot is None:
            return None
        rows = self.snapshot_rows(snapshot_id)
        comparable = [row for row in rows if row.price is not None and row.nights and row.nights > 0]
        ppn_values = [float(row.pricePerNight or (row.price / row.nights)) for row in comparable if row.price is not None and row.nights]
        pppn_values = [float(row.pricePerPersonPerNight) for row in comparable if row.pricePerPersonPerNight is not None]
        return {
            "snapshot": MarketSnapshot(**dict(snapshot)).model_dump(),
            "summary": {
                "rows": len(rows),
                "comparableRows": len(comparable),
                "avgPricePerNight": _round(sum(ppn_values) / len(ppn_values)) if ppn_values else 0,
                "avgPricePerPersonNight": _round(sum(pppn_values) / len(pppn_values)) if pppn_values else 0,
                "minPricePerNight": _round(min(ppn_values)) if ppn_values else 0,
                "maxPricePerNight": _round(max(ppn_values)) if ppn_values else 0,
            },
            "rows": rows,
        }

    def market_heatmap(self, target_id: int, photos: int = 6) -> dict:
        photo_limit = max(1, min(photos, 24))
        rows = self.conn.execute(
            """
            WITH latest AS (
              SELECT id, scraped_at
              FROM market_snapshots
              WHERE target_id = ?
              ORDER BY scraped_at DESC, id DESC
              LIMIT ?
            )
            SELECT
              msh.hotel_key AS hotelKey,
              msh.hotel_name AS hotelName,
              AVG(COALESCE(msh.price_per_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END)) AS avgPricePerNight,
              MIN(COALESCE(msh.price_per_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END)) AS minPricePerNight,
              MAX(COALESCE(msh.price_per_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END)) AS maxPricePerNight,
              COUNT(*) AS samples,
              MAX(latest.scraped_at) AS lastSeenAt,
              hl.latitude AS latitude,
              hl.longitude AS longitude
            FROM latest
            JOIN market_snapshot_hotels msh ON msh.snapshot_id = latest.id
            LEFT JOIN hotel_locations hl ON hl.hotel_key = msh.hotel_key
            WHERE hl.latitude IS NOT NULL AND hl.longitude IS NOT NULL
            GROUP BY msh.hotel_key
            HAVING AVG(COALESCE(msh.price_per_night, CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END)) IS NOT NULL
            ORDER BY avgPricePerNight DESC
            """
            ,
            (target_id, photo_limit),
        ).fetchall()
        points = [
            {
                "hotelKey": row["hotelKey"],
                "hotelName": row["hotelName"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "avgPricePerNight": _round(row["avgPricePerNight"] or 0),
                "minPricePerNight": _round(row["minPricePerNight"] or 0),
                "maxPricePerNight": _round(row["maxPricePerNight"] or 0),
                "samples": int(row["samples"] or 0),
                "lastSeenAt": row["lastSeenAt"],
            }
            for row in rows
        ]
        scale_values = [point["avgPricePerNight"] for point in points if point["avgPricePerNight"] > 0]
        min_val = min(scale_values) if scale_values else 0
        max_val = max(scale_values) if scale_values else 0
        for point in points:
            if max_val <= min_val:
                point["intensity"] = 0.5 if point["avgPricePerNight"] > 0 else 0
            else:
                point["intensity"] = _round((point["avgPricePerNight"] - min_val) / (max_val - min_val))
        return {
            "photosUsed": photo_limit,
            "points": points,
            "scale": {"minPricePerNight": _round(min_val), "maxPricePerNight": _round(max_val)},
        }

    def dashboard_metrics(self, target_id: int) -> dict:
        latest = self.latest_snapshot(target_id)
        if latest is None:
            return _empty_dashboard()

        rows = self.snapshot_rows(latest.id)
        priced = [r for r in rows if r.price is not None]
        comparable = [r for r in rows if r.price is not None and r.nights and r.nights > 0]
        prices = [float(r.price) for r in priced]
        per_night = [float(r.pricePerNight or (r.price / r.nights)) for r in comparable if r.price is not None and r.nights]
        avg = sum(prices) / len(prices) if prices else 0
        avg_ppn = sum(per_night) / len(per_night) if per_night else 0
        per_person_night = [float(r.pricePerPersonPerNight) for r in comparable if r.pricePerPersonPerNight is not None]
        avg_pppn = sum(per_person_night) / len(per_person_night) if per_person_night else 0
        located = len([r for r in rows if r.latitude is not None and r.longitude is not None])
        currencies = sorted({r.currency for r in rows if r.currency})

        history = self.snapshot_history(target_id, 2)
        previous = next((item for item in history if item.id != latest.id), None)
        previous_rows = self.snapshot_rows(previous.id) if previous else []
        previous_priced = [r for r in previous_rows if r.price is not None]
        previous_avg = sum(float(r.price) for r in previous_priced) / len(previous_priced) if previous_priced else 0
        previous_comp = [r for r in previous_rows if r.price is not None and r.nights and r.nights > 0]
        previous_ppn_values = [float(r.pricePerNight or (r.price / r.nights)) for r in previous_comp if r.price is not None and r.nights]
        previous_avg_ppn = sum(previous_ppn_values) / len(previous_ppn_values) if previous_ppn_values else 0
        previous_pppn_values = [float(r.pricePerPersonPerNight) for r in previous_comp if r.pricePerPersonPerNight is not None]
        previous_avg_pppn = sum(previous_pppn_values) / len(previous_pppn_values) if previous_pppn_values else 0

        previous_by_key = {r.hotelKey: r for r in previous_rows}
        changed = increases = drops = 0
        for row in comparable:
            prev = previous_by_key.get(row.hotelKey)
            if not prev or not prev.price or not prev.nights:
                continue
            current_ppn = row.pricePerNight or (row.price / row.nights)  # type: ignore[operator]
            prev_ppn = prev.pricePerNight or (prev.price / prev.nights)
            change = _pct_change(current_ppn, prev_ppn)
            if change is not None and abs(change) >= 3:
                changed += 1
                increases += 1 if change > 0 else 0
                drops += 1 if change < 0 else 0

        competitive = []
        for row in comparable:
            current_ppn = row.pricePerNight or (row.price / row.nights)  # type: ignore[operator]
            competitive.append(
                {
                    "hotelKey": row.hotelKey,
                    "hotelName": row.hotelName,
                    "price": row.price,
                    "pricePerNight": _round(current_ppn),
                    "pricePerPersonPerNight": row.pricePerPersonPerNight,
                    "currency": row.currency,
                    "rating": row.rating,
                    "position": row.position,
                    "gapVsMarketPct": _round(((current_ppn - avg_ppn) / avg_ppn) * 100) if avg_ppn else None,
                    "comparable": bool(row.price is not None and row.nights and row.currency),
                }
            )
        competitive.sort(key=lambda item: item["pricePerNight"] or 0, reverse=True)

        notes: list[str] = []
        if len(priced) < len(rows):
            notes.append("Hay hoteles sin precio: no deben entrar en comparativas de ADR.")
        if len(currencies) > 1:
            notes.append("Hay varias monedas en la captura: normaliza divisas antes de decidir.")
        if len(comparable) < len(rows):
            notes.append("Hay filas sin noches/precio: el precio por noche no es comparable.")
        if any(r.roomType is None for r in rows):
            notes.append("Faltan tipologias de habitacion en algunas filas; revisa comparabilidad del producto.")

        rating_buckets = Counter(_rating_bucket(r.rating) for r in rows if r.rating is not None)
        trend = self._trend(target_id)
        insights = _build_insights(avg_ppn, _pct_change(avg, previous_avg), _pct_change(avg_ppn, previous_avg_ppn), competitive, notes, rows, comparable, changed, increases, drops)

        return {
            "latestSnapshot": latest.model_dump(),
            "cards": [
                {"label": "Precio medio", "value": _round(avg)},
                {"label": "ADR mercado", "value": _round(avg_ppn)},
                {"label": "Precio minimo noche", "value": _round(min(per_night) if per_night else 0)},
                {"label": "Precio maximo noche", "value": _round(max(per_night) if per_night else 0)},
            ],
            "ratingDistribution": [{"bucket": key, "count": value} for key, value in sorted(rating_buckets.items())],
            "topPrices": [{"hotelName": r.hotelName, "price": r.price} for r in sorted(priced, key=lambda x: x.price or 0, reverse=True)[:5]],
            "bottomPrices": [{"hotelName": r.hotelName, "price": r.price} for r in sorted(priced, key=lambda x: x.price or 0)[:5]],
            "trend": trend,
            "locationCoverage": {"total": len(rows), "located": located, "pct": _round((located / len(rows)) * 100) if rows else 0},
            "market": {
                "avgPrice": _round(avg),
                "avgPricePerNight": _round(avg_ppn),
                "avgPricePerPersonNight": _round(avg_pppn),
                "minPricePerNight": _round(min(per_night) if per_night else 0),
                "maxPricePerNight": _round(max(per_night) if per_night else 0),
                "medianPricePerNight": _round(median(per_night) if per_night else 0),
            },
            "movement": {
                "previousSnapshotId": previous.id if previous else None,
                "avgPriceChangePct": _pct_change(avg, previous_avg),
                "avgPricePerNightChangePct": _pct_change(avg_ppn, previous_avg_ppn),
                "avgPricePerPersonNightChangePct": _pct_change(avg_pppn, previous_avg_pppn),
                "changedHotels": changed,
                "priceIncreases": increases,
                "priceDrops": drops,
            },
            "dataQuality": {
                "totalRows": len(rows),
                "pricedRows": len(priced),
                "missingPriceRows": len(rows) - len(priced),
                "comparableRows": len(comparable),
                "comparablePct": _round((len(comparable) / len(rows)) * 100) if rows else 0,
                "currencyWarnings": currencies if len(currencies) > 1 else [],
                "notes": notes,
            },
            "competitiveSet": competitive,
            "insights": insights,
        }

    def _trend(self, target_id: int) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT ms.scraped_at AS scrapedAt, AVG(msh.price) AS avgPrice, COUNT(msh.id) AS hotels
            FROM market_snapshots ms
            JOIN market_snapshot_hotels msh ON msh.snapshot_id = ms.id
            WHERE ms.target_id = ? AND msh.price IS NOT NULL
            GROUP BY ms.id
            ORDER BY ms.scraped_at DESC
            LIMIT 12
            """,
            (target_id,),
        ).fetchall()
        return [{"scrapedAt": row["scrapedAt"], "avgPrice": _round(row["avgPrice"] or 0), "hotels": row["hotels"]} for row in reversed(rows)]


def _empty_dashboard() -> dict:
    return {
        "latestSnapshot": None,
        "cards": [],
        "ratingDistribution": [],
        "topPrices": [],
        "bottomPrices": [],
        "trend": [],
        "locationCoverage": {"total": 0, "located": 0, "pct": 0},
        "market": {"avgPrice": 0, "avgPricePerNight": 0, "avgPricePerPersonNight": 0, "minPricePerNight": 0, "maxPricePerNight": 0, "medianPricePerNight": 0},
        "movement": {"previousSnapshotId": None, "avgPriceChangePct": None, "avgPricePerNightChangePct": None, "avgPricePerPersonNightChangePct": None, "changedHotels": 0, "priceIncreases": 0, "priceDrops": 0},
        "dataQuality": {"totalRows": 0, "pricedRows": 0, "missingPriceRows": 0, "comparableRows": 0, "comparablePct": 0, "currencyWarnings": [], "notes": ["No hay capturas todavia para este mercado."]},
        "competitiveSet": [],
        "insights": [],
    }


def _build_insights(avg_ppn: float, market_change: float | None, ppn_change: float | None, competitive: list[dict], notes: list[str], rows: list[MarketHotelRow], comparable: list[MarketHotelRow], changed: int, increases: int, drops: int) -> list[dict]:
    insights: list[RevenueInsight] = []
    if ppn_change is not None and abs(ppn_change) >= 5:
        insights.append(RevenueInsight(id="market-movement", type="market_movement", severity="critical" if abs(ppn_change) >= 12 else "warning", title="Mercado en subida" if ppn_change > 0 else "Mercado en bajada", message=f"El ADR competitivo cambio un {ppn_change}% frente a la lectura anterior.", changePct=ppn_change))
    if competitive:
        leader = competitive[0]
        if leader.get("gapVsMarketPct") is not None and leader["gapVsMarketPct"] >= 15:
            insights.append(RevenueInsight(id="price-leader", type="price_leader", severity="info", title="Lider de precio identificado", message=f"{leader['hotelName']} esta un {leader['gapVsMarketPct']}% por encima de la media del set.", hotelName=leader["hotelName"], value=leader["pricePerNight"], benchmark=_round(avg_ppn), changePct=leader["gapVsMarketPct"]))
        aggressive = next((h for h in competitive if h.get("gapVsMarketPct") is not None and h["gapVsMarketPct"] <= -15), None)
        if aggressive:
            insights.append(RevenueInsight(id="aggressive-pricing", type="aggressive_pricing", severity="warning", title="Precio agresivo en el mercado", message=f"{aggressive['hotelName']} esta {abs(aggressive['gapVsMarketPct'])}% por debajo de la media del set.", hotelName=aggressive["hotelName"], value=aggressive["pricePerNight"], benchmark=_round(avg_ppn), changePct=aggressive["gapVsMarketPct"]))
    if changed >= 3:
        insights.append(RevenueInsight(id="competitor-movement", type="market_movement", severity="warning", title="Movimiento competitivo relevante", message=f"{changed} hoteles cambiaron precio de forma significativa: {increases} subidas y {drops} bajadas.", changePct=market_change))
    comparable_pct = (len(comparable) / len(rows) * 100) if rows else 0
    if comparable_pct < 85:
        insights.append(RevenueInsight(id="comparability-risk", type="data_quality", severity="warning", title="Comparabilidad limitada", message=f"Solo el {_round(comparable_pct)}% de filas tiene precio y noches validas.", value=_round(comparable_pct)))
    for index, note in enumerate(notes[:2], start=1):
        insights.append(RevenueInsight(id=f"quality-{index}", type="data_quality", severity="info", title="Aviso de calidad de dato", message=note))
    return [item.model_dump() for item in insights[:6]]


def _rating_bucket(rating: float | None) -> str:
    if rating is None:
        return "Sin rating"
    if rating >= 9:
        return "9+"
    if rating >= 8:
        return "8-8.9"
    if rating >= 7:
        return "7-7.9"
    return "<7"


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return _round(((current - previous) / previous) * 100)


def _round(value: float) -> float:
    return round(float(value), 2)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
