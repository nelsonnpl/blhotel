from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
from statistics import median, stdev
from threading import RLock

from .models import (
    CompetitiveStabilityEntry,
    DemandCurvePoint,
    MarketHotelRow,
    MarketSnapshot,
    PickupEntry,
    RevenueInsight,
    RevenueOpportunity,
    SearchTarget,
)


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
              board TEXT,
              review_count INTEGER,
              free_cancellation INTEGER,
              FOREIGN KEY(snapshot_id) REFERENCES market_snapshots(id),
              FOREIGN KEY(hotel_key) REFERENCES hotel_locations(hotel_key)
            );

            CREATE INDEX IF NOT EXISTS idx_market_snapshot_hotels_snapshot
              ON market_snapshot_hotels(snapshot_id, position ASC);

            CREATE TABLE IF NOT EXISTS air_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              captured_at TEXT NOT NULL,
              source TEXT NOT NULL DEFAULT 'mock',
              routes_requested INTEGER NOT NULL DEFAULT 0,
              routes_captured INTEGER NOT NULL DEFAULT 0,
              flights_captured INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS air_flights (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              search_id TEXT,
              itinerary_id TEXT,
              search_datetime TEXT,
              origin TEXT NOT NULL,
              destination TEXT NOT NULL,
              market TEXT,
              outbound_date TEXT,
              return_date TEXT,
              leg_direction TEXT,
              trip_type TEXT,
              search_type TEXT,
              days_ahead INTEGER,
              price REAL,
              lowest_price REAL,
              price_level TEXT,
              typical_price_min REAL,
              typical_price_max REAL,
              typical_price_avg REAL,
              result_group TEXT,
              option_index INTEGER,
              total_duration_min INTEGER,
              stops INTEGER,
              num_layovers INTEGER,
              num_legs INTEGER,
              main_airline TEXT,
              airlines TEXT,
              flight_numbers TEXT,
              aircraft_models TEXT,
              travel_classes TEXT,
              departure_airport_id TEXT,
              departure_airport_name TEXT,
              departure_time TEXT,
              arrival_airport_id TEXT,
              arrival_airport_name TEXT,
              arrival_time TEXT,
              layover_airports TEXT,
              google_price_level TEXT,
              price_history TEXT,
              FOREIGN KEY(run_id) REFERENCES air_runs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_air_flights_run
              ON air_flights(run_id, origin, destination);

            CREATE INDEX IF NOT EXISTS idx_air_flights_origin_dest
              ON air_flights(origin, destination);
            """
            )
            self.conn.commit()
        self._ensure_column("market_snapshot_hotels", "price_per_night", "REAL")
        self._ensure_column("market_snapshot_hotels", "price_per_person_night", "REAL")
        # Comparability fields parsed from the Booking search card (added later — migrate existing DBs).
        self._ensure_column("market_snapshot_hotels", "board", "TEXT")
        self._ensure_column("market_snapshot_hotels", "review_count", "INTEGER")
        self._ensure_column("market_snapshot_hotels", "free_cancellation", "INTEGER")
        # Route-level Google Flights demand signals (added later — migrate existing DBs).
        self._ensure_column("air_flights", "google_price_level", "TEXT")
        self._ensure_column("air_flights", "price_history", "TEXT")

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
              check_in, check_out, nights, price_per_night, price_per_person_night, position, location_status,
              board, review_count, free_cancellation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                row.board,
                row.reviewCount,
                int(row.freeCancellation) if row.freeCancellation is not None else None,
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
              msh.board AS board,
              msh.review_count AS reviewCount,
              msh.free_cancellation AS freeCancellation,
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
        for rank_index, row in enumerate(sorted(comparable, key=lambda r: float(r.pricePerNight or (r.price / r.nights)) if r.price and r.nights else 0, reverse=True), start=1):
            current_ppn = row.pricePerNight or (row.price / row.nights)  # type: ignore[operator]
            rate_position_index = _round((current_ppn / avg_ppn) * 100) if avg_ppn else None
            prev_row = previous_by_key.get(row.hotelKey)
            prev_ppn = None
            price_change_ppn = None
            if prev_row and prev_row.price and prev_row.nights and prev_row.nights > 0:
                prev_ppn = prev_row.pricePerNight or (prev_row.price / prev_row.nights)
                price_change_ppn = _pct_change(current_ppn, prev_ppn)
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
                    "marketRank": rank_index,
                    "ratePositionIndex": rate_position_index,
                    "gapVsMarketPct": _round(((current_ppn - avg_ppn) / avg_ppn) * 100) if avg_ppn else None,
                    "priceChangePct": price_change_ppn,
                    "comparable": bool(row.price is not None and row.nights and row.currency),
                }
            )
        competitive.sort(key=lambda item: item["pricePerNight"] or 0, reverse=True)

        # New / disappeared hotels detection
        current_keys = {r.hotelKey for r in rows}
        previous_keys = {r.hotelKey for r in previous_rows}
        new_entrants = [{"hotelKey": r.hotelKey, "hotelName": r.hotelName} for r in rows if r.hotelKey not in previous_keys] if previous_rows else []
        disappeared = [{"hotelKey": r.hotelKey, "hotelName": r.hotelName} for r in previous_rows if r.hotelKey not in current_keys] if previous_rows else []

        # Demand indicators
        ppn_change = _pct_change(avg_ppn, previous_avg_ppn)
        fill_ratio = _round(latest.capturedRows / latest.availableResults * 100) if latest.availableResults > 0 else None
        booking_pressure = "alta" if increases > drops and ppn_change and ppn_change > 3 else ("baja" if drops > increases and ppn_change and ppn_change < -3 else "neutral")

        # Price tier distribution
        tier_dist = _price_tier_distribution(comparable, avg_ppn)

        # Rating-price correlation
        rating_price = _rating_price_correlation(comparable)

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
        insights = _build_insights(
            avg_ppn, _pct_change(avg, previous_avg), _pct_change(avg_ppn, previous_avg_ppn),
            competitive, notes, rows, comparable, changed, increases, drops,
            fill_ratio, booking_pressure, new_entrants, disappeared, rating_price,
        )

        return {
            "latestSnapshot": latest.model_dump(),
            "cards": [
                {"label": "Precio medio", "value": _round(avg)},
                {"label": "ADR mercado", "value": _round(avg_ppn)},
                {"label": "Precio minimo noche", "value": _round(min(per_night) if per_night else 0)},
                {"label": "Precio maximo noche", "value": _round(max(per_night) if per_night else 0)},
            ],
            "rateShoppingIndex": {
                "marketAvgAdr": _round(avg_ppn),
                "medianAdr": _round(median(per_night) if per_night else 0),
                "totalCompetitors": len(comparable),
                "topQuartileThreshold": _round(_percentile(per_night, 75)) if per_night else 0,
                "bottomQuartileThreshold": _round(_percentile(per_night, 25)) if per_night else 0,
            },
            "demandIndicators": {
                "bookingPressure": booking_pressure,
                "fillRatio": fill_ratio,
                "capturedRows": latest.capturedRows,
                "availableResults": latest.availableResults,
                "priceDirection": "subiendo" if ppn_change and ppn_change > 2 else ("bajando" if ppn_change and ppn_change < -2 else "estable"),
                "competitorIncreases": increases,
                "competitorDrops": drops,
            },
            "ratingDistribution": [{"bucket": key, "count": value} for key, value in sorted(rating_buckets.items())],
            "priceTierDistribution": tier_dist,
            "ratingPriceCorrelation": rating_price,
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
            "newEntrants": new_entrants,
            "disappearedHotels": disappeared,
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

    # ------------------------------------------------------------------
    # Pickup / Pace Analysis
    # ------------------------------------------------------------------

    def pickup_analysis(self, target_id: int, hotel_key: str | None = None, check_in: str | None = None, limit: int = 50) -> list[dict]:
        """Compare the same hotel+check-in across consecutive snapshots."""
        snapshots = self.snapshot_history(target_id, limit=30)
        if len(snapshots) < 2:
            return []

        snapshot_ids = [s.id for s in snapshots]
        placeholders = ",".join("?" for _ in snapshot_ids)
        params: list = list(snapshot_ids)

        where_extra = ""
        if hotel_key:
            where_extra += " AND msh.hotel_key = ?"
            params.append(hotel_key)
        if check_in:
            where_extra += " AND msh.check_in = ?"
            params.append(check_in)

        rows = self.conn.execute(
            f"""
            SELECT
              msh.hotel_key AS hotelKey,
              msh.hotel_name AS hotelName,
              msh.check_in AS checkIn,
              ms.scraped_at AS observedAt,
              msh.price AS price,
              msh.nights AS nights,
              COALESCE(msh.price_per_night,
                CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END
              ) AS pricePerNight
            FROM market_snapshot_hotels msh
            JOIN market_snapshots ms ON ms.id = msh.snapshot_id
            WHERE msh.snapshot_id IN ({placeholders})
              AND msh.price IS NOT NULL
              AND msh.nights > 0
              {where_extra}
            ORDER BY msh.hotel_key, msh.check_in, ms.scraped_at DESC
            """,
            params,
        ).fetchall()

        grouped: dict[tuple[str, str | None], list[dict]] = defaultdict(list)
        for row in rows:
            grouped[(row["hotelKey"], row["checkIn"])].append(dict(row))

        entries: list[dict] = []
        for (h_key, ci), observations in grouped.items():
            for i in range(len(observations) - 1):
                current = observations[i]
                prev = observations[i + 1]
                pickup_abs = _round(current["pricePerNight"] - prev["pricePerNight"]) if current["pricePerNight"] and prev["pricePerNight"] else None
                pickup_pct = _pct_change(current["pricePerNight"], prev["pricePerNight"])
                entries.append(
                    PickupEntry(
                        hotelKey=h_key,
                        hotelName=current["hotelName"],
                        checkIn=ci,
                        observedAt=current["observedAt"],
                        previousObservedAt=prev["observedAt"],
                        currentPrice=current["price"],
                        previousPrice=prev["price"],
                        pricePerNight=_round(current["pricePerNight"]) if current["pricePerNight"] else None,
                        previousPricePerNight=_round(prev["pricePerNight"]) if prev["pricePerNight"] else None,
                        pickupAbsolute=pickup_abs,
                        pickupPct=pickup_pct,
                    ).model_dump()
                )
        entries.sort(key=lambda e: abs(e.get("pickupPct") or 0), reverse=True)
        return entries[:limit]

    # ------------------------------------------------------------------
    # Demand Curve (days-to-arrival pricing)
    # ------------------------------------------------------------------

    def demand_curve(self, target_id: int, limit_snapshots: int = 30) -> list[dict]:
        """Group observations by days-until-check-in to show pricing curve."""
        rows = self.conn.execute(
            """
            SELECT
              CAST(julianday(msh.check_in) - julianday(ms.scraped_at) AS INTEGER) AS daysUntilCheckIn,
              COALESCE(msh.price_per_night,
                CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END
              ) AS ppn
            FROM market_snapshot_hotels msh
            JOIN market_snapshots ms ON ms.id = msh.snapshot_id
            WHERE ms.target_id = ?
              AND msh.price IS NOT NULL
              AND msh.nights > 0
              AND msh.check_in IS NOT NULL
              AND CAST(julianday(msh.check_in) - julianday(ms.scraped_at) AS INTEGER) >= 0
            ORDER BY daysUntilCheckIn
            """,
            (target_id,),
        ).fetchall()

        if not rows:
            return []

        grouped: dict[int, list[float]] = defaultdict(list)
        for row in rows:
            days = int(row["daysUntilCheckIn"])
            ppn = float(row["ppn"])
            grouped[days].append(ppn)

        points: list[dict] = []
        for days in sorted(grouped.keys()):
            values = grouped[days]
            points.append(
                DemandCurvePoint(
                    daysUntilCheckIn=days,
                    avgAdr=_round(sum(values) / len(values)),
                    medianAdr=_round(median(values)),
                    minAdr=_round(min(values)),
                    maxAdr=_round(max(values)),
                    observations=len(values),
                ).model_dump()
            )
        return points

    # ------------------------------------------------------------------
    # Competitive Stability
    # ------------------------------------------------------------------

    def competitive_stability(self, target_id: int, snapshots_count: int = 10) -> list[dict]:
        """Measure price consistency for each hotel across multiple snapshots."""
        rows = self.conn.execute(
            """
            WITH recent_snaps AS (
              SELECT id FROM market_snapshots
              WHERE target_id = ?
              ORDER BY scraped_at DESC, id DESC
              LIMIT ?
            )
            SELECT
              msh.hotel_key AS hotelKey,
              msh.hotel_name AS hotelName,
              COALESCE(msh.price_per_night,
                CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END
              ) AS ppn
            FROM market_snapshot_hotels msh
            WHERE msh.snapshot_id IN (SELECT id FROM recent_snaps)
              AND msh.price IS NOT NULL
              AND msh.nights > 0
            ORDER BY msh.hotel_key
            """,
            (target_id, snapshots_count),
        ).fetchall()

        if not rows:
            return []

        grouped: dict[str, dict] = defaultdict(lambda: {"prices": [], "name": ""})
        for row in rows:
            grouped[row["hotelKey"]]["prices"].append(float(row["ppn"]))
            grouped[row["hotelKey"]]["name"] = row["hotelName"]

        all_ppn = [float(row["ppn"]) for row in rows]
        market_avg = sum(all_ppn) / len(all_ppn) if all_ppn else 0

        entries: list[dict] = []
        for hotel_key, data in grouped.items():
            prices = data["prices"]
            if len(prices) < 2:
                continue
            avg_p = sum(prices) / len(prices)
            sd = stdev(prices) if len(prices) >= 2 else 0.0
            consistency = _round(max(0, 100 - (sd / avg_p * 100))) if avg_p > 0 else 0
            gap_vs_market = _round(((avg_p - market_avg) / market_avg) * 100) if market_avg else 0
            if gap_vs_market > 10:
                positioning = "Premium constante"
            elif gap_vs_market < -10:
                positioning = "Descuento constante"
            else:
                positioning = "Alineado al mercado"
            entries.append(
                CompetitiveStabilityEntry(
                    hotelKey=hotel_key,
                    hotelName=data["name"],
                    avgPricePerNight=_round(avg_p),
                    stddevPricePerNight=_round(sd),
                    consistencyScore=consistency,
                    positioningLabel=positioning,
                    avgGapVsMarketPct=gap_vs_market,
                    observations=len(prices),
                ).model_dump()
            )
        entries.sort(key=lambda e: e["consistencyScore"])
        return entries

    # ------------------------------------------------------------------
    # Revenue Opportunities
    # ------------------------------------------------------------------

    def revenue_opportunities(self, target_id: int, air_data: dict | None = None) -> list[dict]:
        """Score date windows by demand signals, competitive gaps, and flight data."""
        latest = self.latest_snapshot(target_id)
        if latest is None:
            return []
        rows = self.snapshot_rows(latest.id)
        comparable = [r for r in rows if r.price is not None and r.nights and r.nights > 0]
        if not comparable:
            return []

        per_night = [float(r.pricePerNight or (r.price / r.nights)) for r in comparable if r.price is not None and r.nights]
        avg_ppn = sum(per_night) / len(per_night) if per_night else 0

        # Previous snapshot for movement
        history = self.snapshot_history(target_id, 2)
        previous = next((s for s in history if s.id != latest.id), None)
        previous_rows = self.snapshot_rows(previous.id) if previous else []
        previous_by_key = {r.hotelKey: r for r in previous_rows}
        previous_comp = [r for r in previous_rows if r.price is not None and r.nights and r.nights > 0]
        prev_per_night = [float(r.pricePerNight or (r.price / r.nights)) for r in previous_comp if r.price is not None and r.nights]
        prev_avg_ppn = sum(prev_per_night) / len(prev_per_night) if prev_per_night else 0

        opportunities: list[dict] = []
        opp_id = 0

        # 1. Hotels below rising market trend
        ppn_change = _pct_change(avg_ppn, prev_avg_ppn) if prev_avg_ppn else None
        if ppn_change and ppn_change > 3:
            for r in comparable:
                current_ppn = float(r.pricePerNight or (r.price / r.nights)) if r.price and r.nights else 0
                prev_r = previous_by_key.get(r.hotelKey)
                if prev_r and prev_r.price and prev_r.nights:
                    prev_ppn = float(prev_r.pricePerNight or (prev_r.price / prev_r.nights))
                    hotel_change = _pct_change(current_ppn, prev_ppn)
                    if hotel_change is not None and hotel_change < ppn_change - 3 and current_ppn < avg_ppn:
                        opp_id += 1
                        score = min(100, abs(ppn_change - (hotel_change or 0)) * 5)
                        opportunities.append(
                            RevenueOpportunity(
                                id=f"raise-{opp_id}",
                                type="raise_rate",
                                severity="warning",
                                title="Sube tu tarifa",
                                message=f"{r.hotelName} esta {_round(abs(current_ppn - avg_ppn))} EUR/noche por debajo de un mercado en alza ({ppn_change}%).",
                                score=_round(score),
                                checkIn=r.checkIn,
                                hotelKey=r.hotelKey,
                                hotelName=r.hotelName,
                                currentAdr=_round(current_ppn),
                                marketAdr=_round(avg_ppn),
                            ).model_dump()
                        )

        # 2. Competitor price drops (protect your rate)
        for r in comparable:
            prev_r = previous_by_key.get(r.hotelKey)
            if not prev_r or not prev_r.price or not prev_r.nights:
                continue
            current_ppn = float(r.pricePerNight or (r.price / r.nights)) if r.price and r.nights else 0
            prev_ppn = float(prev_r.pricePerNight or (prev_r.price / prev_r.nights))
            change = _pct_change(current_ppn, prev_ppn)
            if change is not None and change < -10:
                opp_id += 1
                opportunities.append(
                    RevenueOpportunity(
                        id=f"protect-{opp_id}",
                        type="protect_rate",
                        severity="warning",
                        title="Protege tu tarifa",
                        message=f"{r.hotelName} ha bajado un {abs(change)}%. Vigila tu posicionamiento.",
                        score=_round(min(100, abs(change) * 3)),
                        hotelKey=r.hotelKey,
                        hotelName=r.hotelName,
                        currentAdr=_round(current_ppn),
                        marketAdr=_round(avg_ppn),
                    ).model_dump()
                )

        # 3. Premium opportunity (highest rating, not pricing accordingly)
        rated = [r for r in comparable if r.rating is not None]
        if rated:
            best_rated = max(rated, key=lambda r: r.rating or 0)
            best_ppn = float(best_rated.pricePerNight or (best_rated.price / best_rated.nights)) if best_rated.price and best_rated.nights else 0
            if best_rated.rating and best_rated.rating >= 8.5 and best_ppn < avg_ppn * 1.1:
                opp_id += 1
                opportunities.append(
                    RevenueOpportunity(
                        id=f"premium-{opp_id}",
                        type="premium_opportunity",
                        severity="info",
                        title="Oportunidad premium",
                        message=f"{best_rated.hotelName} tiene rating {best_rated.rating} pero precio por debajo del premium. Potencial de subida.",
                        score=_round(min(100, (best_rated.rating - 8) * 30)),
                        hotelKey=best_rated.hotelKey,
                        hotelName=best_rated.hotelName,
                        currentAdr=_round(best_ppn),
                        marketAdr=_round(avg_ppn),
                    ).model_dump()
                )

        # 4. Air data opportunities (if air data provided)
        if air_data and air_data.get("routes"):
            for route in air_data["routes"]:
                flight_price = route.get("lowest_price") or route.get("avg_price")
                # Aggregated routes expose `price_quality_label` ("Barato"/"Caro"/"Normal");
                # keep `price_level` as a fallback for any legacy/raw payloads.
                price_level = route.get("price_quality_label") or route.get("price_level") or ""
                if flight_price and str(price_level).lower() in ("low", "barato"):
                    opp_id += 1
                    opportunities.append(
                        RevenueOpportunity(
                            id=f"air-low-{opp_id}",
                            type="air_opportunity",
                            severity="info",
                            title="Vuelos baratos detectados",
                            message=f"Vuelos desde {route.get('market', route.get('origin'))} a {flight_price} EUR (barato). Posible pico de demanda inminente.",
                            score=_round(75),
                            flightAvgPrice=_round(flight_price),
                            marketAdr=_round(avg_ppn),
                        ).model_dump()
                    )
                elif flight_price and str(price_level).lower() in ("high", "caro"):
                    opp_id += 1
                    opportunities.append(
                        RevenueOpportunity(
                            id=f"air-high-{opp_id}",
                            type="committed_traveler",
                            severity="info",
                            title="Viajero comprometido",
                            message=f"Vuelos desde {route.get('market', route.get('origin'))} caros ({flight_price} EUR). El huesped ya invirtio en el viaje: mantener tarifa premium.",
                            score=_round(60),
                            flightAvgPrice=_round(flight_price),
                            marketAdr=_round(avg_ppn),
                        ).model_dump()
                    )

        # 5. Fill ratio signal
        if latest.availableResults > 0:
            fill = latest.capturedRows / latest.availableResults
            if fill < 0.6:
                opp_id += 1
                opportunities.append(
                    RevenueOpportunity(
                        id=f"demand-surge-{opp_id}",
                        type="demand_surge",
                        severity="critical",
                        title="Posible pico de demanda",
                        message=f"Solo se capturaron {latest.capturedRows} de {latest.availableResults} resultados ({_round(fill * 100)}%). El mercado puede estar lleno.",
                        score=_round(min(100, (1 - fill) * 120)),
                    ).model_dump()
                )

        opportunities.sort(key=lambda o: o.get("score", 0), reverse=True)
        return opportunities[:20]

    # ------------------------------------------------------------------
    # Air Data
    # ------------------------------------------------------------------

    def create_air_run(self, source: str, routes_requested: int) -> int:
        with self.lock:
            cursor = self.conn.execute(
                "INSERT INTO air_runs (captured_at, source, routes_requested) VALUES (?, ?, ?)",
                (_now(), source, routes_requested),
            )
            self.conn.commit()
        return int(cursor.lastrowid)

    def finish_air_run(self, run_id: int, routes_captured: int, flights_captured: int) -> None:
        with self.lock:
            self.conn.execute(
                "UPDATE air_runs SET routes_captured=?, flights_captured=? WHERE id=?",
                (routes_captured, flights_captured, run_id),
            )
            self.conn.commit()

    def insert_air_flight(self, run_id: int, row: dict) -> None:
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO air_flights (
                  run_id, search_id, itinerary_id, search_datetime, origin, destination, market,
                  outbound_date, return_date, leg_direction, trip_type, search_type, days_ahead,
                  price, lowest_price, price_level, typical_price_min, typical_price_max, typical_price_avg,
                  result_group, option_index, total_duration_min, stops, num_layovers, num_legs,
                  main_airline, airlines, flight_numbers, aircraft_models, travel_classes,
                  departure_airport_id, departure_airport_name, departure_time,
                  arrival_airport_id, arrival_airport_name, arrival_time, layover_airports,
                  google_price_level, price_history
                ) VALUES (
                  ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
                """,
                (
                    run_id,
                    row.get("search_id"), row.get("itinerary_id"), row.get("search_datetime"),
                    row.get("origin", ""), row.get("destination", ""), row.get("market"),
                    row.get("outbound_date"), row.get("return_date"), row.get("leg_direction"),
                    row.get("trip_type"), row.get("search_type"), row.get("days_ahead"),
                    row.get("price"), row.get("lowest_price"), row.get("price_level"),
                    row.get("typical_price_min"), row.get("typical_price_max"), row.get("typical_price_avg"),
                    row.get("result_group"), row.get("option_index"), row.get("total_duration_min"),
                    row.get("stops"), row.get("num_layovers"), row.get("num_legs"),
                    row.get("main_airline"),
                    json.dumps(row.get("airlines") or []),
                    json.dumps(row.get("flight_numbers") or []),
                    json.dumps(row.get("aircraft_models") or []),
                    json.dumps(row.get("travel_classes") or []),
                    row.get("departure_airport_id"), row.get("departure_airport_name"), row.get("departure_time"),
                    row.get("arrival_airport_id"), row.get("arrival_airport_name"), row.get("arrival_time"),
                    json.dumps(row.get("layover_airports") or []),
                    row.get("google_price_level"),
                    json.dumps(row.get("price_history") or []),
                ),
            )
            self.conn.commit()

    def list_air_flights(self, run_id: int | None = None) -> list[dict]:
        if run_id is not None:
            rows = self.conn.execute(
                "SELECT * FROM air_flights WHERE run_id=? ORDER BY origin, destination, price ASC",
                (run_id,),
            ).fetchall()
        else:
            latest_run = self.conn.execute(
                "SELECT id FROM air_runs ORDER BY captured_at DESC LIMIT 1"
            ).fetchone()
            if latest_run is None:
                return []
            rows = self.conn.execute(
                "SELECT * FROM air_flights WHERE run_id=? ORDER BY origin, destination, price ASC",
                (latest_run["id"],),
            ).fetchall()
        return [_deserialize_air_row(dict(row)) for row in rows]

    def air_route_history(self, route_key: str, limit: int = 20) -> list[dict]:
        parts = route_key.split("_", 1)
        if len(parts) != 2:
            return []
        origin, destination = parts
        rows = self.conn.execute(
            """
            SELECT af.*, ar.captured_at AS run_captured_at
            FROM air_flights af
            JOIN air_runs ar ON ar.id = af.run_id
            WHERE af.origin = ? AND af.destination = ?
            ORDER BY ar.captured_at DESC, af.price ASC
            LIMIT ?
            """,
            (origin, destination, limit),
        ).fetchall()
        return [_deserialize_air_row(dict(row)) for row in rows]


def _deserialize_air_row(row: dict) -> dict:
    for field in ("airlines", "flight_numbers", "aircraft_models", "travel_classes", "layover_airports", "price_history"):
        val = row.get(field)
        row[field] = json.loads(val) if isinstance(val, str) and val else []
    return row


def _empty_dashboard() -> dict:
    return {
        "latestSnapshot": None,
        "cards": [],
        "rateShoppingIndex": {"marketAvgAdr": 0, "medianAdr": 0, "totalCompetitors": 0, "topQuartileThreshold": 0, "bottomQuartileThreshold": 0},
        "demandIndicators": {"bookingPressure": "neutral", "fillRatio": None, "capturedRows": 0, "availableResults": 0, "priceDirection": "estable", "competitorIncreases": 0, "competitorDrops": 0},
        "ratingDistribution": [],
        "priceTierDistribution": [],
        "ratingPriceCorrelation": [],
        "topPrices": [],
        "bottomPrices": [],
        "trend": [],
        "locationCoverage": {"total": 0, "located": 0, "pct": 0},
        "market": {"avgPrice": 0, "avgPricePerNight": 0, "avgPricePerPersonNight": 0, "minPricePerNight": 0, "maxPricePerNight": 0, "medianPricePerNight": 0},
        "movement": {"previousSnapshotId": None, "avgPriceChangePct": None, "avgPricePerNightChangePct": None, "avgPricePerPersonNightChangePct": None, "changedHotels": 0, "priceIncreases": 0, "priceDrops": 0},
        "dataQuality": {"totalRows": 0, "pricedRows": 0, "missingPriceRows": 0, "comparableRows": 0, "comparablePct": 0, "currencyWarnings": [], "notes": ["No hay capturas todavia para este mercado."]},
        "competitiveSet": [],
        "newEntrants": [],
        "disappearedHotels": [],
        "insights": [],
    }


def _build_insights(
    avg_ppn: float,
    market_change: float | None,
    ppn_change: float | None,
    competitive: list[dict],
    notes: list[str],
    rows: list[MarketHotelRow],
    comparable: list[MarketHotelRow],
    changed: int,
    increases: int,
    drops: int,
    fill_ratio: float | None = None,
    booking_pressure: str = "neutral",
    new_entrants: list[dict] | None = None,
    disappeared: list[dict] | None = None,
    rating_price: list[dict] | None = None,
) -> list[dict]:
    insights: list[RevenueInsight] = []

    # --- Raise your rates ---
    if ppn_change is not None and ppn_change >= 5:
        insights.append(RevenueInsight(
            id="raise-rates", type="raise_rate", severity="critical" if ppn_change >= 12 else "warning",
            title="Sube tus tarifas",
            message=f"El ADR del mercado ha subido un {ppn_change}%. Revisa si tu hotel sigue la tendencia.",
            changePct=ppn_change,
        ))

    # --- Market cooling ---
    if drops >= 3 and ppn_change is not None and ppn_change < -3:
        insights.append(RevenueInsight(
            id="market-cooling", type="market_cooling", severity="warning",
            title="Mercado en enfriamiento",
            message=f"{drops} competidores bajaron precio simultaneamente. ADR del set cayo un {abs(ppn_change)}%.",
            changePct=ppn_change,
        ))
    elif ppn_change is not None and abs(ppn_change) >= 5:
        insights.append(RevenueInsight(
            id="market-movement", type="market_movement",
            severity="critical" if abs(ppn_change) >= 12 else "warning",
            title="Mercado en subida" if ppn_change > 0 else "Mercado en bajada",
            message=f"El ADR competitivo cambio un {ppn_change}% frente a la lectura anterior.",
            changePct=ppn_change,
        ))

    # --- Demand surge (fill ratio) ---
    if fill_ratio is not None and fill_ratio < 65:
        insights.append(RevenueInsight(
            id="demand-surge", type="demand_surge", severity="critical",
            title="Pico de demanda",
            message=f"Ratio de captura bajo ({fill_ratio}%). El mercado puede estar llenandose.",
            value=fill_ratio,
        ))

    # --- Price leader ---
    if competitive:
        leader = competitive[0]
        if leader.get("gapVsMarketPct") is not None and leader["gapVsMarketPct"] >= 15:
            insights.append(RevenueInsight(
                id="price-leader", type="price_leader", severity="info",
                title="Lider de precio identificado",
                message=f"{leader['hotelName']} esta un {leader['gapVsMarketPct']}% por encima de la media del set.",
                hotelName=leader["hotelName"], value=leader["pricePerNight"],
                benchmark=_round(avg_ppn), changePct=leader["gapVsMarketPct"],
            ))
        # --- Protect your rate ---
        big_drops = [h for h in competitive if h.get("priceChangePct") is not None and h["priceChangePct"] < -10]
        if big_drops:
            worst = min(big_drops, key=lambda h: h["priceChangePct"])
            insights.append(RevenueInsight(
                id="protect-rate", type="protect_rate", severity="warning",
                title="Protege tu tarifa",
                message=f"{worst['hotelName']} ha bajado un {abs(worst['priceChangePct'])}%. Vigila tu posicionamiento.",
                hotelName=worst["hotelName"], value=worst["pricePerNight"],
                benchmark=_round(avg_ppn), changePct=worst["priceChangePct"],
            ))
        # --- Aggressive pricing ---
        aggressive = next((h for h in competitive if h.get("gapVsMarketPct") is not None and h["gapVsMarketPct"] <= -15), None)
        if aggressive:
            insights.append(RevenueInsight(
                id="aggressive-pricing", type="aggressive_pricing", severity="warning",
                title="Precio agresivo en el mercado",
                message=f"{aggressive['hotelName']} esta {abs(aggressive['gapVsMarketPct'])}% por debajo de la media del set.",
                hotelName=aggressive["hotelName"], value=aggressive["pricePerNight"],
                benchmark=_round(avg_ppn), changePct=aggressive["gapVsMarketPct"],
            ))

    # --- Premium opportunity ---
    rated = [r for r in comparable if r.rating is not None]
    if rated:
        best = max(rated, key=lambda r: r.rating or 0)
        if best.rating and best.rating >= 8.5 and best.price and best.nights:
            best_ppn = float(best.pricePerNight or (best.price / best.nights))
            if best_ppn < avg_ppn * 1.1:
                insights.append(RevenueInsight(
                    id="premium-opportunity", type="premium_opportunity", severity="info",
                    title="Oportunidad premium",
                    message=f"{best.hotelName} tiene rating {best.rating} pero no cobra prima. Potencial de subida.",
                    hotelName=best.hotelName, value=_round(best_ppn),
                    benchmark=_round(avg_ppn),
                ))

    # --- New entrants ---
    if new_entrants and len(new_entrants) >= 2:
        names = ", ".join(e["hotelName"] for e in new_entrants[:3])
        insights.append(RevenueInsight(
            id="new-entrants", type="competitive_change", severity="info",
            title="Nuevos competidores",
            message=f"{len(new_entrants)} hoteles nuevos en el set competitivo: {names}.",
            value=float(len(new_entrants)),
        ))

    # --- Disappeared hotels ---
    if disappeared and len(disappeared) >= 2:
        names = ", ".join(e["hotelName"] for e in disappeared[:3])
        insights.append(RevenueInsight(
            id="disappeared-hotels", type="competitive_change", severity="info",
            title="Hoteles desaparecidos",
            message=f"{len(disappeared)} hoteles ya no aparecen: {names}. Posible sold-out.",
            value=float(len(disappeared)),
        ))

    # --- Competitor movement ---
    if changed >= 3:
        insights.append(RevenueInsight(
            id="competitor-movement", type="market_movement", severity="warning",
            title="Movimiento competitivo relevante",
            message=f"{changed} hoteles cambiaron precio de forma significativa: {increases} subidas y {drops} bajadas.",
            changePct=market_change,
        ))

    # --- Data quality ---
    comparable_pct = (len(comparable) / len(rows) * 100) if rows else 0
    if comparable_pct < 85:
        insights.append(RevenueInsight(
            id="comparability-risk", type="data_quality", severity="warning",
            title="Comparabilidad limitada",
            message=f"Solo el {_round(comparable_pct)}% de filas tiene precio y noches validas.",
            value=_round(comparable_pct),
        ))
    for index, note in enumerate(notes[:2], start=1):
        insights.append(RevenueInsight(
            id=f"quality-{index}", type="data_quality", severity="info",
            title="Aviso de calidad de dato", message=note,
        ))
    return [item.model_dump() for item in insights[:12]]


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


def _percentile(values: list[float], pct: float) -> float:
    """Simple percentile calculation (linear interpolation)."""
    if not values:
        return 0.0
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * pct / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_v[int(k)]
    return sorted_v[f] * (c - k) + sorted_v[c] * (k - f)


def _price_tier_distribution(comparable: list[MarketHotelRow], avg_ppn: float) -> list[dict]:
    """Segment hotels into budget/mid/premium/luxury tiers."""
    per_night = [float(r.pricePerNight or (r.price / r.nights)) for r in comparable if r.price is not None and r.nights]
    if not per_night:
        return []
    q25 = _percentile(per_night, 25)
    q50 = _percentile(per_night, 50)
    q75 = _percentile(per_night, 75)
    tiers = [
        ("budget", "Economico", 0, q25),
        ("mid", "Gama Media", q25, q50),
        ("premium", "Premium", q50, q75),
        ("luxury", "Lujo", q75, float("inf")),
    ]
    result = []
    for tier_id, label, low, high in tiers:
        count = sum(1 for v in per_night if (low <= v < high) or (tier_id == "luxury" and v >= low))
        if count > 0:
            tier_vals = [v for v in per_night if (low <= v < high) or (tier_id == "luxury" and v >= low)]
            result.append({
                "tier": tier_id,
                "label": label,
                "count": count,
                "avgAdr": _round(sum(tier_vals) / len(tier_vals)),
                "pct": _round(count / len(per_night) * 100),
            })
    return result


def _rating_price_correlation(comparable: list[MarketHotelRow]) -> list[dict]:
    """Show how rating bands correlate with ADR."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for r in comparable:
        if r.rating is None or r.price is None or not r.nights:
            continue
        bucket = _rating_bucket(r.rating)
        ppn = float(r.pricePerNight or (r.price / r.nights))
        buckets[bucket].append(ppn)
    result = []
    for bucket in ["<7", "7-7.9", "8-8.9", "9+"]:
        vals = buckets.get(bucket, [])
        if not vals:
            continue
        result.append({
            "ratingBucket": bucket,
            "hotelCount": len(vals),
            "avgAdr": _round(sum(vals) / len(vals)),
            "minAdr": _round(min(vals)),
            "maxAdr": _round(max(vals)),
        })
    return result
