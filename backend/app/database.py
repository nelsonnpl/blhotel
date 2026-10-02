from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from statistics import median, stdev
from threading import RLock, local
from urllib.parse import quote_plus
import uuid

from .revenue_semantics import product_signature, unique_products, freshness

from .capture_profile import profile_from_url
from .models import (
    DemandCurvePoint,
    HotelRateDetailRow,
    MarketHotelRow,
    MarketSnapshot,
    PickupEntry,
    RevenueInsight,
    RevenueOpportunity,
    SearchTarget,
)


def _safe_float(value) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = local()
        self.lock = RLock()
        self.init()

    @property
    def conn(self) -> sqlite3.Connection:
        """Conexión por hilo: sqlite3.Connection no soporta uso concurrente desde varios
        hilos (Flask atiende cada request en un hilo distinto y el frontend lanza varias a
        la vez), lo que producía `InterfaceError: bad parameter or other API misuse`
        intermitentes. Con WAL, varias conexiones pueden leer en paralelo sin bloquearse."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.path, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            conn.execute("PRAGMA foreign_keys = ON;")
            self._local.conn = conn
        return conn

    def init(self) -> None:
        with self.lock:
            self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS search_targets (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              url TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS app_identities (
              owner_key TEXT PRIMARY KEY,
              display_name TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'analyst',
              active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_access (
              owner_key TEXT NOT NULL,
              target_id INTEGER NOT NULL,
              permission TEXT NOT NULL DEFAULT 'viewer',
              created_at TEXT NOT NULL,
              PRIMARY KEY(owner_key, target_id),
              FOREIGN KEY(owner_key) REFERENCES app_identities(owner_key) ON DELETE CASCADE,
              FOREIGN KEY(target_id) REFERENCES search_targets(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_market_access_target
              ON market_access(target_id, owner_key);

            CREATE TABLE IF NOT EXISTS market_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              target_id INTEGER NOT NULL,
              source_url TEXT NOT NULL,
              requested_limit INTEGER NOT NULL,
              available_results INTEGER NOT NULL,
              captured_rows INTEGER NOT NULL,
              scraped_at TEXT NOT NULL,
              raw_hash TEXT NOT NULL,
              capture_group_id TEXT,
              capture_status TEXT NOT NULL DEFAULT 'unknown',
              capture_profile_hash TEXT,
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

            CREATE TABLE IF NOT EXISTS hotel_inventory (
              hotel_key TEXT PRIMARY KEY,
              hotel_id TEXT,
              hotel_name TEXT NOT NULL,
              detail_url TEXT NOT NULL,
              description TEXT,
              stars REAL,
              accommodation_type TEXT,
              city TEXT,
              country_code TEXT,
              display_location TEXT,
              address TEXT,
              latitude REAL,
              longitude REAL,
              beach_distance TEXT,
              main_distance TEXT,
              nearby_beach_names TEXT NOT NULL DEFAULT '[]',
              top_location INTEGER,
              popular_district TEXT,
              photo_url TEXT,
              review_score REAL,
              review_count INTEGER,
              review_score_text TEXT,
              no_prepayment INTEGER,
              ufi TEXT,
              source TEXT NOT NULL DEFAULT 'booking_graphql',
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              completeness REAL NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_hotel_inventory_hotel_id_lookup
              ON hotel_inventory(hotel_id) WHERE hotel_id IS NOT NULL;

            CREATE INDEX IF NOT EXISTS idx_hotel_inventory_name
              ON hotel_inventory(hotel_name);

            CREATE TABLE IF NOT EXISTS hotel_name_aliases (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hotel_key TEXT NOT NULL,
              alias TEXT NOT NULL,
              source TEXT NOT NULL DEFAULT 'manual',
              created_at TEXT NOT NULL,
              UNIQUE(hotel_key, alias, source),
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS hotel_source_links (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hotel_key TEXT NOT NULL,
              source TEXT NOT NULL,
              external_id TEXT,
              url TEXT NOT NULL,
              external_name TEXT,
              verified INTEGER NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL,
              UNIQUE(hotel_key, source),
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hotel_source_links_source
              ON hotel_source_links(source, external_id);

            CREATE TABLE IF NOT EXISTS hotel_attribute_observations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hotel_key TEXT NOT NULL,
              attribute TEXT NOT NULL,
              value_json TEXT NOT NULL,
              source TEXT NOT NULL,
              observed_at TEXT NOT NULL,
              selected INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hotel_attribute_observations
              ON hotel_attribute_observations(hotel_key, attribute, observed_at DESC);

            CREATE TABLE IF NOT EXISTS hotel_reviews (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hotel_key TEXT NOT NULL,
              source TEXT NOT NULL,
              source_review_id TEXT,
              review_fingerprint TEXT NOT NULL,
              author TEXT,
              title TEXT,
              rating REAL,
              rating_scale REAL NOT NULL DEFAULT 5,
              positive_text TEXT,
              negative_text TEXT,
              review_original TEXT,
              review_es TEXT,
              language_original TEXT,
              language_confidence REAL,
              translation_method TEXT,
              published_at TEXT,
              date_precision TEXT NOT NULL DEFAULT 'unknown',
              relative_published_at TEXT,
              source_url TEXT NOT NULL,
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              run_id TEXT,
              discovery_contexts_json TEXT NOT NULL DEFAULT '[]',
              quality_flags_json TEXT NOT NULL DEFAULT '[]',
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE,
              FOREIGN KEY(run_id) REFERENCES hotel_review_runs(id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_hotel_reviews_dedupe
              ON hotel_reviews(hotel_key, source, review_fingerprint);
            CREATE INDEX IF NOT EXISTS idx_hotel_reviews_page
              ON hotel_reviews(hotel_key, source, rating, published_at DESC, id DESC);

            CREATE TABLE IF NOT EXISTS hotel_review_versions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              review_id INTEGER NOT NULL,
              run_id TEXT,
              captured_at TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              snapshot_json TEXT NOT NULL,
              UNIQUE(review_id, content_hash),
              FOREIGN KEY(review_id) REFERENCES hotel_reviews(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hotel_review_versions_history
              ON hotel_review_versions(review_id, captured_at DESC);

            CREATE TABLE IF NOT EXISTS hotel_review_runs (
              id TEXT PRIMARY KEY,
              hotel_key TEXT NOT NULL,
              source TEXT NOT NULL,
              status TEXT NOT NULL,
              source_url TEXT,
              max_reviews INTEGER NOT NULL DEFAULT 1000,
              budget_usd REAL,
              estimated_spend_usd REAL NOT NULL DEFAULT 0,
              actual_spend_usd REAL,
              rows_seen INTEGER NOT NULL DEFAULT 0,
              rows_inserted INTEGER NOT NULL DEFAULT 0,
              rows_updated INTEGER NOT NULL DEFAULT 0,
              cursor_json TEXT,
              coverage_json TEXT NOT NULL DEFAULT '{}',
              error TEXT,
              started_at TEXT NOT NULL,
              completed_at TEXT,
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hotel_review_runs_latest
              ON hotel_review_runs(hotel_key, source, started_at DESC);

            CREATE TABLE IF NOT EXISTS hotel_review_notes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hotel_key TEXT NOT NULL,
              review_id INTEGER,
              owner_key TEXT NOT NULL,
              body TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE,
              FOREIGN KEY(review_id) REFERENCES hotel_reviews(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hotel_review_notes
              ON hotel_review_notes(hotel_key, updated_at DESC);

            CREATE TABLE IF NOT EXISTS hotel_review_analyses (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hotel_key TEXT NOT NULL,
              sources_json TEXT NOT NULL,
              model TEXT NOT NULL,
              prompt_version TEXT NOT NULL,
              analysis_json TEXT NOT NULL,
              evidence_json TEXT NOT NULL DEFAULT '[]',
              input_hash TEXT NOT NULL,
              cost_usd REAL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hotel_review_analyses_latest
              ON hotel_review_analyses(hotel_key, created_at DESC);

            CREATE TABLE IF NOT EXISTS hotel_review_legacy_imports (
              source_file TEXT PRIMARY KEY,
              sha256 TEXT NOT NULL,
              rows_imported INTEGER NOT NULL,
              imported_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS hotel_review_topics (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hotel_key TEXT NOT NULL,
              review_id INTEGER NOT NULL,
              topic TEXT NOT NULL,
              sentiment TEXT NOT NULL DEFAULT 'neutral',
              model TEXT NOT NULL,
              created_at TEXT NOT NULL,
              UNIQUE(review_id, topic, sentiment),
              FOREIGN KEY(hotel_key) REFERENCES hotel_inventory(hotel_key) ON DELETE CASCADE,
              FOREIGN KEY(review_id) REFERENCES hotel_reviews(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hotel_review_topics_lookup
              ON hotel_review_topics(hotel_key,topic,review_id);

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
              hotel_id TEXT,
              price_original REAL,
              discount_pct REAL,
              sold_out INTEGER,
              observation_status TEXT,
              closed INTEGER,
              units_left INTEGER,
              accommodation_type TEXT,
              beach_distance TEXT,
              top_location INTEGER,
              popular_district TEXT,
              children_free INTEGER,
              third_party INTEGER,
              occupancy_rate INTEGER,
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

            CREATE TABLE IF NOT EXISTS air_route_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              route_key TEXT NOT NULL,
              area_id TEXT,
              area_name TEXT,
              country TEXT,
              origin TEXT NOT NULL,
              destination TEXT NOT NULL,
              outbound_date TEXT,
              return_date TEXT,
              lowest_price REAL,
              avg_price REAL,
              num_options INTEGER NOT NULL DEFAULT 0,
              num_direct_options INTEGER NOT NULL DEFAULT 0,
              num_airlines INTEGER NOT NULL DEFAULT 0,
              airlines_detected TEXT NOT NULL DEFAULT '[]',
              direct INTEGER NOT NULL,
              currency TEXT NOT NULL DEFAULT 'EUR',
              FOREIGN KEY(run_id) REFERENCES air_runs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_air_route_snapshots_lookup
              ON air_route_snapshots(route_key, direct, run_id DESC);

            CREATE TABLE IF NOT EXISTS flight_price_observations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              route_snapshot_id INTEGER NOT NULL,
              itinerary_id TEXT,
              price REAL,
              observed_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES air_runs(id),
              FOREIGN KEY(route_snapshot_id) REFERENCES air_route_snapshots(id)
            );

            CREATE TABLE IF NOT EXISTS hotel_capture_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              captured_at TEXT NOT NULL,
              group_id TEXT,
              target_id INTEGER,
              profile_json TEXT,
              status TEXT NOT NULL DEFAULT 'running',
              expected_slices INTEGER NOT NULL DEFAULT 1,
              completed_slices INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY(target_id) REFERENCES search_targets(id)
            );

            CREATE TABLE IF NOT EXISTS hotel_price_observations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              capture_run_id INTEGER NOT NULL,
              snapshot_id INTEGER NOT NULL,
              hotel_key TEXT NOT NULL,
              target_id INTEGER NOT NULL,
              price_per_night REAL,
              data_quality_flags TEXT NOT NULL DEFAULT '[]',
              FOREIGN KEY(capture_run_id) REFERENCES hotel_capture_runs(id),
              FOREIGN KEY(snapshot_id) REFERENCES market_snapshots(id)
            );

            CREATE INDEX IF NOT EXISTS idx_hotel_price_observations_latest
              ON hotel_price_observations(hotel_key, id DESC);

            CREATE TABLE IF NOT EXISTS background_jobs (
              id TEXT PRIMARY KEY,
              kind TEXT NOT NULL,
              status TEXT NOT NULL,
              payload TEXT NOT NULL,
              result TEXT,
              error TEXT,
              progress INTEGER NOT NULL DEFAULT 0,
              message TEXT,
              attempts INTEGER NOT NULL DEFAULT 0,
              max_attempts INTEGER NOT NULL DEFAULT 3,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              started_at TEXT,
              completed_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_background_jobs_pending
              ON background_jobs(status, created_at);

            CREATE TABLE IF NOT EXISTS hotel_detail_capture_tasks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              batch_id TEXT NOT NULL,
              target_id INTEGER NOT NULL,
              snapshot_id INTEGER,
              hotel_key TEXT NOT NULL,
              hotel_name TEXT,
              detail_url TEXT NOT NULL,
              check_in TEXT NOT NULL,
              check_out TEXT NOT NULL,
              adults INTEGER NOT NULL,
              children INTEGER NOT NULL DEFAULT 0,
              rooms INTEGER NOT NULL DEFAULT 1,
              status TEXT NOT NULL DEFAULT 'queued',
              attempts INTEGER NOT NULL DEFAULT 0,
              rows_captured INTEGER NOT NULL DEFAULT 0,
              error TEXT,
              started_at TEXT,
              completed_at TEXT,
              UNIQUE(batch_id, hotel_key),
              FOREIGN KEY(target_id) REFERENCES search_targets(id),
              FOREIGN KEY(snapshot_id) REFERENCES market_snapshots(id)
            );

            CREATE INDEX IF NOT EXISTS idx_hotel_detail_tasks_batch_status
              ON hotel_detail_capture_tasks(batch_id, status, id);

            CREATE TABLE IF NOT EXISTS hotel_rate_details (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              target_id INTEGER NOT NULL,
              hotel_key TEXT NOT NULL,
              hotel_name TEXT,
              hotel_pagename TEXT,
              room_type TEXT,
              max_occupancy INTEGER,
              price_original REAL,
              price_final REAL,
              currency TEXT,
              board TEXT,
              prepayment_text TEXT,
              program TEXT,
              cancellation_text TEXT,
              free_cancellation INTEGER,
              units_left INTEGER,
              block_uid TEXT,
              sold_out INTEGER,
              genius INTEGER,
              breakfast_score REAL,
              breakfast_type_id INTEGER,
              bed_comfort_score REAL,
              bed_comfort_reviews INTEGER,
              stars REAL,
              check_in TEXT,
              check_out TEXT,
              adults INTEGER,
              children INTEGER,
              rooms INTEGER,
              captured_at TEXT NOT NULL,
              FOREIGN KEY(target_id) REFERENCES search_targets(id)
            );

            CREATE INDEX IF NOT EXISTS idx_hotel_rate_details_target
              ON hotel_rate_details(target_id, captured_at DESC);

            CREATE INDEX IF NOT EXISTS idx_hotel_rate_details_hotel
              ON hotel_rate_details(hotel_key, captured_at DESC);

            CREATE TABLE IF NOT EXISTS analysis_workspaces (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              owner_key TEXT NOT NULL DEFAULT 'local-revenue',
              target_ids TEXT NOT NULL DEFAULT '[]',
              global_filters TEXT NOT NULL DEFAULT '{}',
              layers TEXT NOT NULL DEFAULT '[]',
              version INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_analysis_workspaces_owner_updated
              ON analysis_workspaces(owner_key, updated_at DESC);

            CREATE TABLE IF NOT EXISTS analysis_workspace_revisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              workspace_id INTEGER NOT NULL,
              owner_key TEXT NOT NULL,
              workspace_version INTEGER NOT NULL,
              name TEXT NOT NULL,
              target_ids TEXT NOT NULL,
              global_filters TEXT NOT NULL,
              layers TEXT NOT NULL,
              created_at TEXT NOT NULL,
              UNIQUE(workspace_id, workspace_version),
              FOREIGN KEY(workspace_id) REFERENCES analysis_workspaces(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_workspace_revisions_owner_workspace
              ON analysis_workspace_revisions(owner_key, workspace_id, workspace_version DESC);

            CREATE TABLE IF NOT EXISTS assistant_sessions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              owner_key TEXT NOT NULL DEFAULT 'local-revenue',
              target_id INTEGER,
              mode TEXT NOT NULL DEFAULT 'quick',
              status TEXT NOT NULL DEFAULT 'active',
              pinned INTEGER NOT NULL DEFAULT 0,
              summary TEXT NOT NULL DEFAULT '',
              version INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              last_message_at TEXT,
              FOREIGN KEY(target_id) REFERENCES search_targets(id)
            );

            CREATE INDEX IF NOT EXISTS idx_assistant_sessions_owner_updated
              ON assistant_sessions(owner_key, status, pinned DESC, updated_at DESC);

            CREATE TABLE IF NOT EXISTS assistant_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              sequence INTEGER NOT NULL,
              role TEXT NOT NULL,
              content TEXT NOT NULL,
              visualization TEXT,
              data_meta TEXT,
              request_id TEXT,
              created_at TEXT NOT NULL,
              UNIQUE(session_id, sequence),
              FOREIGN KEY(session_id) REFERENCES assistant_sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_assistant_messages_session_sequence
              ON assistant_messages(session_id, sequence ASC);

            CREATE TABLE IF NOT EXISTS assistant_attachments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              owner_key TEXT NOT NULL,
              filename TEXT NOT NULL,
              media_type TEXT NOT NULL,
              size_bytes INTEGER NOT NULL,
              sha256 TEXT NOT NULL,
              storage_path TEXT NOT NULL,
              extracted_text TEXT NOT NULL DEFAULT '',
              extraction_status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL,
              FOREIGN KEY(session_id) REFERENCES assistant_sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_assistant_attachments_owner_session
              ON assistant_attachments(owner_key, session_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS assistant_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id INTEGER NOT NULL,
              assistant_message_id INTEGER,
              request_id TEXT,
              model TEXT,
              mode TEXT,
              outcome TEXT NOT NULL,
              latency_ms INTEGER,
              endpoint_latency_ms INTEGER,
              tool_rounds INTEGER NOT NULL DEFAULT 0,
              tool_calls INTEGER NOT NULL DEFAULT 0,
              context_chars INTEGER,
              usage TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(session_id) REFERENCES assistant_sessions(id) ON DELETE CASCADE,
              FOREIGN KEY(assistant_message_id) REFERENCES assistant_messages(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_assistant_runs_session_created
              ON assistant_runs(session_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS assistant_budget_reservations (
              request_id TEXT PRIMARY KEY,
              owner_key TEXT NOT NULL,
              month_prefix TEXT NOT NULL,
              reserved_usd REAL NOT NULL,
              actual_cost_usd REAL,
              status TEXT NOT NULL DEFAULT 'reserved',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_assistant_budget_owner_month
              ON assistant_budget_reservations(owner_key, month_prefix, status);

            CREATE TABLE IF NOT EXISTS copilot_evaluation_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source TEXT NOT NULL,
              profile TEXT NOT NULL,
              provider_live INTEGER NOT NULL DEFAULT 0,
              passed INTEGER NOT NULL,
              case_count INTEGER NOT NULL,
              passed_count INTEGER NOT NULL,
              warning_count INTEGER NOT NULL DEFAULT 0,
              error_count INTEGER NOT NULL DEFAULT 0,
              details TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_copilot_evaluation_runs_created
              ON copilot_evaluation_runs(created_at DESC);

            -- Estadística externa normalizada. No se almacenan respuestas JSON/XLSX:
            -- cada fila es una observación agregada con procedencia y caducidad.
            CREATE TABLE IF NOT EXISTS external_observations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source_id TEXT NOT NULL,
              dataset_id TEXT NOT NULL,
              metric TEXT NOT NULL,
              unit TEXT NOT NULL,
              geography_type TEXT NOT NULL,
              geography_code TEXT NOT NULL,
              segment TEXT NOT NULL DEFAULT '',
              period_start TEXT NOT NULL,
              period_end TEXT NOT NULL DEFAULT '',
              value REAL NOT NULL,
              revision TEXT NOT NULL DEFAULT '',
              observed_at TEXT,
              published_at TEXT,
              fetched_at TEXT NOT NULL,
              expires_at TEXT,
              quality_status TEXT NOT NULL DEFAULT 'ok',
              payload_hash TEXT,
              metadata_json TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              UNIQUE (
                source_id, dataset_id, metric, unit, geography_type,
                geography_code, segment, period_start, period_end, revision
              )
            );

            CREATE INDEX IF NOT EXISTS idx_external_observations_lookup
              ON external_observations(
                source_id, dataset_id, geography_code, metric, period_start DESC
              );

            CREATE INDEX IF NOT EXISTS idx_external_observations_expiry
              ON external_observations(expires_at);

            CREATE TABLE IF NOT EXISTS external_ingestion_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source_id TEXT NOT NULL,
              dataset_id TEXT NOT NULL,
              requested_scope TEXT NOT NULL DEFAULT '{}',
              started_at TEXT NOT NULL,
              completed_at TEXT,
              status TEXT NOT NULL DEFAULT 'running',
              row_count INTEGER NOT NULL DEFAULT 0,
              payload_hash TEXT,
              error TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_external_ingestion_runs_lookup
              ON external_ingestion_runs(source_id, dataset_id, started_at DESC);

            -- Caché meteorológica normalizada. No conserva respuestas completas
            -- del proveedor; cada fila guarda solo variables y procedencia.
            CREATE TABLE IF NOT EXISTS weather_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              location_key TEXT NOT NULL,
              latitude REAL,
              longitude REAL,
              provider TEXT NOT NULL,
              dataset TEXT NOT NULL,
              model TEXT,
              kind TEXT NOT NULL,
              market_snapshot_id INTEGER,
              timezone TEXT NOT NULL,
              start_date TEXT NOT NULL,
              end_date TEXT NOT NULL,
              retrieved_at TEXT NOT NULL,
              capture_at TEXT NOT NULL,
              payload_hash TEXT,
              source_url TEXT,
              created_at TEXT NOT NULL,
              UNIQUE(location_key, provider, dataset, kind, retrieved_at, capture_at, start_date, end_date)
            );

            CREATE INDEX IF NOT EXISTS idx_weather_snapshots_location
              ON weather_snapshots(location_key, retrieved_at DESC);

            CREATE TABLE IF NOT EXISTS weather_daily (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              snapshot_id INTEGER NOT NULL,
              local_date TEXT NOT NULL,
              valid_at TEXT NOT NULL,
              values_json TEXT NOT NULL,
              units_json TEXT NOT NULL,
              known_at_capture INTEGER NOT NULL,
              retrospective INTEGER NOT NULL,
              FOREIGN KEY(snapshot_id) REFERENCES weather_snapshots(id) ON DELETE CASCADE,
              UNIQUE(snapshot_id, local_date)
            );

            CREATE INDEX IF NOT EXISTS idx_weather_daily_lookup
              ON weather_daily(snapshot_id, local_date);
            """
            )
            self.conn.commit()
            # Additive migration for cost accounting (safe for existing SQLite files).
            columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(assistant_runs)").fetchall()}
            if "cost_usd" not in columns:
                self.conn.execute("ALTER TABLE assistant_runs ADD COLUMN cost_usd REAL NOT NULL DEFAULT 0")
                self.conn.commit()
            # Additive queue migration. Existing installations keep all jobs
            # while gaining a cooperative cancellation flag.
            job_columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(background_jobs)").fetchall()}
            if "cancel_requested" not in job_columns:
                self.conn.execute("ALTER TABLE background_jobs ADD COLUMN cancel_requested INTEGER NOT NULL DEFAULT 0")
                self.conn.commit()
            if "idempotency_key" not in job_columns:
                self.conn.execute("ALTER TABLE background_jobs ADD COLUMN idempotency_key TEXT")
                self.conn.commit()
            self.conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_background_jobs_idempotency "
                "ON background_jobs(kind, idempotency_key) WHERE idempotency_key IS NOT NULL"
            )
            self.conn.commit()
            now = _now()
            self.conn.execute(
                """
                INSERT OR IGNORE INTO app_identities
                  (owner_key, display_name, role, active, created_at, updated_at)
                VALUES ('local-revenue', 'Revenue local', 'admin', 1, ?, ?)
                """,
                (now, now),
            )
            self.conn.execute(
                """
                INSERT OR IGNORE INTO market_access (owner_key, target_id, permission, created_at)
                SELECT 'local-revenue', id, 'admin', ? FROM search_targets
                """,
                (now,),
            )
            # Los tableros creados antes del historial conservan una línea base
            # de su versión actual. No reconstruimos versiones anteriores que
            # nunca fueron almacenadas.
            self.conn.execute(
                """
                INSERT OR IGNORE INTO analysis_workspace_revisions
                  (workspace_id, owner_key, workspace_version, name, target_ids, global_filters, layers, created_at)
                SELECT id, owner_key, version, name, target_ids, global_filters, layers, updated_at
                FROM analysis_workspaces
                """
            )
            self.conn.commit()
        self._ensure_column("market_snapshot_hotels", "price_per_night", "REAL")
        self._ensure_column("market_snapshot_hotels", "price_per_person_night", "REAL")
        # Comparability fields parsed from the Booking search card (added later — migrate existing DBs).
        self._ensure_column("market_snapshot_hotels", "board", "TEXT")
        self._ensure_column("market_snapshot_hotels", "review_count", "INTEGER")
        self._ensure_column("market_snapshot_hotels", "free_cancellation", "INTEGER")
        # Señales de revenue del backend GraphQL (added later — migrate existing DBs).
        self._ensure_column("market_snapshot_hotels", "hotel_id", "TEXT")
        self._ensure_column("market_snapshot_hotels", "price_original", "REAL")
        self._ensure_column("market_snapshot_hotels", "discount_pct", "REAL")
        self._ensure_column("market_snapshot_hotels", "sold_out", "INTEGER")
        self._ensure_column("market_snapshot_hotels", "observation_status", "TEXT")
        self._ensure_column("weather_snapshots", "market_snapshot_id", "INTEGER")
        with self.lock:
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_weather_snapshots_market_snapshot ON weather_snapshots(market_snapshot_id, location_key)"
            )
            self.conn.commit()
        self._ensure_column("market_snapshot_hotels", "closed", "INTEGER")
        self._ensure_column("market_snapshot_hotels", "units_left", "INTEGER")
        self._ensure_column("market_snapshot_hotels", "accommodation_type", "TEXT")
        self._ensure_column("market_snapshot_hotels", "beach_distance", "TEXT")
        self._ensure_column("market_snapshot_hotels", "top_location", "INTEGER")
        self._ensure_column("market_snapshot_hotels", "popular_district", "TEXT")
        self._ensure_column("market_snapshot_hotels", "children_free", "INTEGER")
        self._ensure_column("hotel_rate_details", "program", "TEXT")
        self._ensure_column("hotel_rate_details", "prepayment_text", "TEXT")
        self._ensure_column("market_snapshot_hotels", "third_party", "INTEGER")
        self._ensure_column("market_snapshot_hotels", "occupancy_rate", "INTEGER")
        self._ensure_column("hotel_inventory", "no_prepayment", "INTEGER")
        self._ensure_column("hotel_reviews", "last_run_id", "TEXT")
        # hotel_id identifica el alojamiento en Booking, pero puede repetirse
        # entre mercados/variantes; la clave canónica de la app sigue siendo
        # hotel_key (slug de la ficha), no imponemos unicidad global aquí.
        self.conn.execute("DROP INDEX IF EXISTS idx_hotel_inventory_hotel_id")
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_hotel_inventory_hotel_id_lookup ON hotel_inventory(hotel_id) WHERE hotel_id IS NOT NULL"
        )
        self.conn.commit()
        # Route-level Google Flights demand signals (added later — migrate existing DBs).
        self._ensure_column("air_flights", "google_price_level", "TEXT")
        self._ensure_column("air_flights", "price_history", "TEXT")
        self._ensure_column("air_runs", "provider", "TEXT NOT NULL DEFAULT 'serpapi'")
        self._ensure_column("air_runs", "profile_json", "TEXT")
        self._ensure_column("air_runs", "coverage_json", "TEXT")
        self._ensure_column("air_runs", "status", "TEXT NOT NULL DEFAULT 'completed'")
        self._ensure_column("air_runs", "queries_requested", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column("air_runs", "queries_completed", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column("air_runs", "queries_failed", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column("air_runs", "cache_hits", "INTEGER NOT NULL DEFAULT 0")
        for column, definition in {
            "provider": "TEXT NOT NULL DEFAULT 'serpapi'",
            "observed_at": "TEXT",
            "currency": "TEXT",
            "departure_at": "TEXT",
            "arrival_at": "TEXT",
            "departure_token": "TEXT",
            "booking_token": "TEXT",
            "segment_signature": "TEXT",
            "baggage_json": "TEXT",
            "extensions_json": "TEXT",
            "emissions_json": "TEXT",
        }.items():
            self._ensure_column("air_flights", column, definition)
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_air_flights_comparison ON air_flights(origin, destination, outbound_date, segment_signature, run_id)"
        )
        self._ensure_column("market_snapshots", "capture_run_id", "INTEGER")
        self._ensure_column("market_snapshots", "capture_profile_json", "TEXT")
        self._ensure_column("market_snapshots", "capture_group_id", "TEXT")
        self._ensure_column("market_snapshots", "capture_status", "TEXT NOT NULL DEFAULT 'unknown'")
        self._ensure_column("market_snapshots", "capture_profile_hash", "TEXT")
        self._ensure_column("hotel_capture_runs", "group_id", "TEXT")
        self._ensure_column("hotel_capture_runs", "target_id", "INTEGER")
        self._ensure_column("hotel_capture_runs", "profile_json", "TEXT")
        self._ensure_column("hotel_capture_runs", "status", "TEXT NOT NULL DEFAULT 'running'")
        self._ensure_column("hotel_capture_runs", "expected_slices", "INTEGER NOT NULL DEFAULT 1")
        self._ensure_column("hotel_capture_runs", "completed_slices", "INTEGER NOT NULL DEFAULT 0")
        self.conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_hotel_capture_runs_group ON hotel_capture_runs(group_id) WHERE group_id IS NOT NULL"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_market_snapshots_capture_group ON market_snapshots(capture_group_id, scraped_at DESC)"
        )
        self.conn.execute(
            "UPDATE market_snapshots SET capture_status = 'unknown' WHERE capture_profile_json IS NULL AND capture_status = 'complete'"
        )
        self._ensure_column("hotel_rate_details", "snapshot_id", "INTEGER REFERENCES market_snapshots(id)")
        self.conn.execute(
            """
            CREATE VIEW IF NOT EXISTS latest_hotel_price_observations AS
            SELECT observation.*
            FROM hotel_price_observations observation
            JOIN (
              SELECT hotel_key, MAX(id) AS latest_id
              FROM hotel_price_observations
              GROUP BY hotel_key
            ) latest ON latest.latest_id = observation.id
            """
        )
        self.conn.commit()

    @staticmethod
    def _external_observation_from_row(row: sqlite3.Row) -> dict:
        """Serializa una observación externa sin exponer JSON bruto."""
        item = dict(row)
        metadata = item.get("metadata_json")
        try:
            metadata_value = json.loads(metadata) if metadata else None
        except (TypeError, ValueError):
            metadata_value = None
        quality_status = item["quality_status"]
        expires_at = item["expires_at"]
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry < datetime.now(timezone.utc):
                    quality_status = "stale"
            except (TypeError, ValueError):
                pass
        return {
            "id": item["id"],
            "sourceId": item["source_id"],
            "datasetId": item["dataset_id"],
            "metric": item["metric"],
            "unit": item["unit"],
            "geographyType": item["geography_type"],
            "geographyCode": item["geography_code"],
            "segment": item["segment"] or None,
            "periodStart": item["period_start"],
            "periodEnd": item["period_end"] or None,
            "value": item["value"],
            "revision": item["revision"] or None,
            "observedAt": item["observed_at"],
            "publishedAt": item["published_at"],
            "fetchedAt": item["fetched_at"],
            "expiresAt": expires_at,
            "qualityStatus": quality_status,
            "payloadHash": item["payload_hash"],
            "metadata": metadata_value,
            "createdAt": item["created_at"],
            "updatedAt": item["updated_at"],
        }

    def upsert_external_observations(self, observations: list[dict]) -> int:
        """Inserta observaciones agregadas y actualiza revisiones sin duplicarlas.

        Los conectores deben pasar valores ya normalizados. Se acepta camelCase o
        snake_case para facilitar la integración con las respuestas de las APIs.
        Las filas con dimensiones obligatorias incompletas o valores no numéricos
        se omiten de forma explícita.
        """
        if not observations:
            return 0
        now = _now()
        values: list[tuple] = []
        for raw in observations:
            item = raw or {}
            def pick(name: str, fallback: str | None = None):
                return item.get(name) if name in item else item.get(fallback or name)

            source_id = str(pick("sourceId", "source_id") or "").strip()
            dataset_id = str(pick("datasetId", "dataset_id") or "").strip()
            metric = str(pick("metric") or "").strip()
            unit = str(pick("unit") or "").strip()
            geography_type = str(pick("geographyType", "geography_type") or "").strip()
            geography_code = str(pick("geographyCode", "geography_code") or "").strip()
            period_start = str(pick("periodStart", "period_start") or "").strip()
            if not all((source_id, dataset_id, metric, unit, geography_type, geography_code, period_start)):
                continue
            try:
                value = float(pick("value"))
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value):
                continue
            metadata = pick("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                metadata = {"value": str(metadata)[:500]}
            values.append(
                (
                    source_id,
                    dataset_id,
                    metric,
                    unit,
                    geography_type,
                    geography_code,
                    str(pick("segment") or "").strip(),
                    period_start,
                    str(pick("periodEnd", "period_end") or "").strip(),
                    value,
                    str(pick("revision") or "").strip(),
                    pick("observedAt", "observed_at"),
                    pick("publishedAt", "published_at"),
                    str(pick("fetchedAt", "fetched_at") or now),
                    pick("expiresAt", "expires_at"),
                    str(pick("qualityStatus", "quality_status") or "ok").strip()[:40],
                    pick("payloadHash", "payload_hash"),
                    json.dumps(metadata, ensure_ascii=False, separators=(",", ":")) if metadata else None,
                    now,
                    now,
                )
            )
        if not values:
            return 0
        with self.lock:
            self.conn.executemany(
                """
                INSERT INTO external_observations (
                  source_id, dataset_id, metric, unit, geography_type,
                  geography_code, segment, period_start, period_end, value,
                  revision, observed_at, published_at, fetched_at, expires_at,
                  quality_status, payload_hash, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                  source_id, dataset_id, metric, unit, geography_type,
                  geography_code, segment, period_start, period_end, revision
                ) DO UPDATE SET
                  value = excluded.value,
                  observed_at = excluded.observed_at,
                  published_at = excluded.published_at,
                  fetched_at = excluded.fetched_at,
                  expires_at = excluded.expires_at,
                  quality_status = excluded.quality_status,
                  payload_hash = excluded.payload_hash,
                  metadata_json = excluded.metadata_json,
                  updated_at = excluded.updated_at
                """,
                values,
            )
            self.conn.commit()
        return len(values)

    def list_external_observations(
        self,
        *,
        source_id: str | None = None,
        dataset_id: str | None = None,
        metric: str | None = None,
        geography_type: str | None = None,
        geography_code: str | None = None,
        period_from: str | None = None,
        period_to: str | None = None,
        limit: int = 250,
    ) -> list[dict]:
        """Consulta acotada para UI y Copilot, con límite defensivo."""
        clauses: list[str] = []
        params: list = []
        filters = (
            ("source_id", source_id),
            ("dataset_id", dataset_id),
            ("metric", metric),
            ("geography_type", geography_type),
            ("geography_code", geography_code),
        )
        for column, value in filters:
            clean = str(value or "").strip()
            if clean:
                clauses.append(f"{column} = ?")
                params.append(clean[:160])
        if period_from:
            clauses.append("period_start >= ?")
            params.append(str(period_from)[:40])
        if period_to:
            clauses.append("period_start <= ?")
            params.append(str(period_to)[:40])
        safe_limit = max(1, min(int(limit), 1000))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(safe_limit)
        rows = self.conn.execute(
            f"SELECT * FROM external_observations {where} "
            "ORDER BY period_start DESC, fetched_at DESC, id DESC LIMIT ?",
            params,
        ).fetchall()
        return [self._external_observation_from_row(row) for row in rows]

    def external_cache_status(self) -> list[dict]:
        """Resumen compacto de cobertura; nunca incluye payloads."""
        rows = self.conn.execute(
            """
            SELECT source_id, dataset_id, COUNT(*) AS row_count,
                   MIN(period_start) AS period_start,
                   MAX(period_start) AS latest_period,
                   MAX(fetched_at) AS fetched_at,
                   SUM(CASE WHEN expires_at IS NOT NULL AND expires_at < ? THEN 1 ELSE 0 END) AS expired_count
            FROM external_observations
            GROUP BY source_id, dataset_id
            ORDER BY source_id, dataset_id
            """,
            (_now(),),
        ).fetchall()
        return [
            {
                "sourceId": row["source_id"],
                "datasetId": row["dataset_id"],
                "rowCount": row["row_count"],
                "periodStart": row["period_start"],
                "latestPeriod": row["latest_period"],
                "fetchedAt": row["fetched_at"],
                "expiredCount": row["expired_count"],
            }
            for row in rows
        ]

    def purge_external_observations(
        self,
        before_period: str,
        *,
        source_id: str | None = None,
        dataset_id: str | None = None,
    ) -> int:
        """Elimina observaciones anteriores a un periodo ISO.

        La fuente y el dataset son opcionales para permitir mantenimientos
        globales, pero los sincronizadores los especifican para no aplicar la
        retención de Dataestur a las series de ISTAC.
        """
        cutoff = str(before_period or "").strip()[:40]
        if not cutoff:
            return 0
        clauses = ["period_start < ?"]
        params: list = [cutoff]
        if source_id:
            clauses.append("source_id = ?")
            params.append(source_id)
        if dataset_id:
            clauses.append("dataset_id = ?")
            params.append(dataset_id)
        with self.lock:
            cursor = self.conn.execute(
                f"DELETE FROM external_observations WHERE {' AND '.join(clauses)}", params
            )
            self.conn.commit()
        return int(cursor.rowcount)

    def start_external_ingestion(self, source_id: str, dataset_id: str, scope: dict | None = None) -> int:
        """Registra una ejecución sin conservar su respuesta original."""
        now = _now()
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO external_ingestion_runs
                  (source_id, dataset_id, requested_scope, started_at, status)
                VALUES (?, ?, ?, ?, 'running')
                """,
                (
                    str(source_id)[:120],
                    str(dataset_id)[:180],
                    json.dumps(scope or {}, ensure_ascii=False, separators=(",", ":")),
                    now,
                ),
            )
            self.conn.commit()
        return int(cursor.lastrowid)

    def finish_external_ingestion(
        self,
        run_id: int,
        *,
        status: str,
        row_count: int = 0,
        payload_hash: str | None = None,
        error: str | None = None,
    ) -> None:
        safe_status = status if status in {"success", "partial", "error"} else "error"
        with self.lock:
            self.conn.execute(
                """
                UPDATE external_ingestion_runs
                SET completed_at = ?, status = ?, row_count = ?, payload_hash = ?, error = ?
                WHERE id = ?
                """,
                (_now(), safe_status, max(0, int(row_count)), payload_hash, (error or "")[:500] or None, run_id),
            )
            self.conn.commit()

    def latest_external_ingestion(self, source_id: str, dataset_id: str) -> dict | None:
        row = self.conn.execute(
            """
            SELECT id, source_id, dataset_id, requested_scope, started_at,
                   completed_at, status, row_count, payload_hash, error
            FROM external_ingestion_runs
            WHERE source_id = ? AND dataset_id = ?
            ORDER BY started_at DESC, id DESC
            LIMIT 1
            """,
            (source_id, dataset_id),
        ).fetchone()
        if row is None:
            return None
        try:
            scope = json.loads(row["requested_scope"] or "{}")
        except (TypeError, ValueError):
            scope = {}
        return {
            "id": row["id"],
            "sourceId": row["source_id"],
            "datasetId": row["dataset_id"],
            "scope": scope,
            "startedAt": row["started_at"],
            "completedAt": row["completed_at"],
            "status": row["status"],
            "rowCount": row["row_count"],
            "payloadHash": row["payload_hash"],
            "error": row["error"],
        }

    def persist_weather_records(
        self,
        records: list,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        timezone_name: str = "Atlantic/Canary",
        payload_hash: str | None = None,
        market_snapshot_id: int | None = None,
    ) -> dict:
        """Guarda una foto meteorológica normalizada, nunca el payload bruto."""
        if not records:
            raise ValueError("No hay registros meteorológicos que guardar")
        first = records[0]
        dates = [record.local_date or record.valid_at.date().isoformat() for record in records]
        now = _now()
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO weather_snapshots (
                  location_key, latitude, longitude, provider, dataset, model,
                  kind, market_snapshot_id, timezone, start_date, end_date, retrieved_at, capture_at,
                  payload_hash, source_url, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(location_key, provider, dataset, kind, retrieved_at, capture_at, start_date, end_date)
                DO UPDATE SET
                  latitude = excluded.latitude,
                  longitude = excluded.longitude,
                  model = excluded.model,
                  market_snapshot_id = excluded.market_snapshot_id,
                  payload_hash = excluded.payload_hash,
                  source_url = excluded.source_url
                RETURNING id
                """,
                (
                    first.location_key, latitude, longitude, first.provider,
                    first.dataset, first.model, first.kind, market_snapshot_id, timezone_name,
                    min(dates), max(dates), first.retrieved_at.isoformat(),
                    first.capture_at.isoformat(), payload_hash, first.source_url, now,
                ),
            )
            snapshot_id = int(cursor.fetchone()[0])
            self.conn.executemany(
                """
                INSERT INTO weather_daily (
                  snapshot_id, local_date, valid_at, values_json, units_json,
                  known_at_capture, retrospective
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id, local_date) DO UPDATE SET
                  valid_at = excluded.valid_at,
                  values_json = excluded.values_json,
                  units_json = excluded.units_json,
                  known_at_capture = excluded.known_at_capture,
                  retrospective = excluded.retrospective
                """,
                [
                    (
                        snapshot_id,
                        record.local_date or record.valid_at.date().isoformat(),
                        record.valid_at.isoformat(),
                        json.dumps(record.values, ensure_ascii=False, separators=(",", ":")),
                        json.dumps(record.units, ensure_ascii=False, separators=(",", ":")),
                        int(record.known_at_capture),
                        int(record.retrospective),
                    )
                    for record in records
                ],
            )
            self.conn.commit()
        return {
            "snapshotId": snapshot_id,
            "locationKey": first.location_key,
            "provider": first.provider,
            "dataset": first.dataset,
            "kind": first.kind,
            "marketSnapshotId": market_snapshot_id,
            "startDate": min(dates),
            "endDate": max(dates),
            "days": len(records),
            "knownAtCaptureDays": sum(1 for record in records if record.known_at_capture),
            "retrospectiveDays": sum(1 for record in records if record.retrospective),
            "retrievedAt": first.retrieved_at.isoformat(),
            "captureAt": first.capture_at.isoformat(),
        }

    def weather_snapshot(self, snapshot_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM weather_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
        if row is None:
            return None
        daily = self.conn.execute(
            "SELECT * FROM weather_daily WHERE snapshot_id = ? ORDER BY local_date ASC", (snapshot_id,)
        ).fetchall()
        days = []
        for item in daily:
            try:
                values = json.loads(item["values_json"])
                units = json.loads(item["units_json"])
            except (TypeError, ValueError):
                values, units = {}, {}
            days.append({
                "date": item["local_date"], "validAt": item["valid_at"],
                "values": values, "units": units,
                "knownAtCapture": bool(item["known_at_capture"]),
                "retrospective": bool(item["retrospective"]),
            })
        return {
            "id": row["id"], "locationKey": row["location_key"],
            "latitude": row["latitude"], "longitude": row["longitude"],
            "provider": row["provider"], "dataset": row["dataset"],
            "model": row["model"], "kind": row["kind"], "timezone": row["timezone"],
            "marketSnapshotId": row["market_snapshot_id"],
            "startDate": row["start_date"], "endDate": row["end_date"],
            "retrievedAt": row["retrieved_at"], "captureAt": row["capture_at"],
            "payloadHash": row["payload_hash"], "sourceUrl": row["source_url"], "days": days,
        }

    def latest_weather_snapshot(self, location_key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT id FROM weather_snapshots WHERE location_key = ? ORDER BY retrieved_at DESC, id DESC LIMIT 1",
            (location_key,),
        ).fetchone()
        return self.weather_snapshot(int(row["id"])) if row else None

    def cached_weather_snapshot(
        self,
        location_key: str,
        *,
        market_snapshot_id: int | None,
        start_date: str,
        end_date: str,
        max_age_hours: int = 6,
    ) -> dict | None:
        """Devuelve una consulta meteorológica equivalente mientras siga fresca.

        La caché se comparte por grupo geográfico y foto de mercado. Esto evita
        que abrir o recargar el workspace genere otra cabecera y las mismas filas
        diarias en SQLite.
        """
        row = self.conn.execute(
            """
            SELECT id, retrieved_at
            FROM weather_snapshots
            WHERE location_key = ? AND market_snapshot_id IS ?
              AND start_date = ? AND end_date = ?
            ORDER BY retrieved_at DESC, id DESC
            LIMIT 1
            """,
            (location_key, market_snapshot_id, start_date, end_date),
        ).fetchone()
        if row is None:
            return None
        try:
            retrieved_at = datetime.fromisoformat(str(row["retrieved_at"]).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if retrieved_at.tzinfo is None:
            return None
        if datetime.now(timezone.utc) - retrieved_at > timedelta(hours=max(1, max_age_hours)):
            return None
        return self.weather_snapshot(int(row["id"]))

    def purge_weather_snapshots(self, before_retrieved_at: str) -> int:
        with self.lock:
            cursor = self.conn.execute("DELETE FROM weather_snapshots WHERE retrieved_at < ?", (before_retrieved_at,))
            self.conn.commit()
        return int(cursor.rowcount)

    def weather_price_association(self, target_id: int, limit_snapshots: int = 12) -> dict:
        """Calcula una asociación descriptiva entre ADR observado y meteorología enlazada.

        Solo usa fotos que tienen snapshots meteorológicos vinculados. La salida
        es deliberadamente descriptiva: no estima demanda ni causalidad y no
        interpola el tiempo de fotos que carecen de enriquecimiento.
        """
        snapshots = list(reversed(self.snapshot_history(target_id, max(2, min(60, int(limit_snapshots))))))
        observations: list[dict] = []
        for snapshot in snapshots:
            rows = self.snapshot_rows(snapshot.id)
            # A weather enrichment is only eligible when it was available at
            # the instant represented by the photo.  A later refresh may be
            # useful as current context, but it must never rewrite history.
            captured_at = _parse_utc_optional(snapshot.scrapedAt)
            if captured_at is None:
                continue
            weather_rows = self.conn.execute(
                """
                SELECT id, location_key, start_date, end_date, retrieved_at
                FROM weather_snapshots
                WHERE market_snapshot_id = ? AND retrieved_at <= ? AND capture_at <= ?
                ORDER BY retrieved_at DESC, id DESC
                """,
                (snapshot.id, captured_at.isoformat(), captured_at.isoformat()),
            ).fetchall()
            # Una foto puede tener enriquecimientos para varias estancias. Solo
            # admitimos ventanas que correspondan a una estancia realmente
            # observada en esa foto; el resto no se puede relacionar con su ADR.
            def matches_stay(start: str, end: str) -> bool:
                for row in rows:
                    check_in = str(row.checkIn or "")
                    check_out = str(row.checkOut or "")
                    if not check_in or not check_out:
                        continue
                    if start == check_in and end <= check_out:
                        return True
                return False

            weather_rows = [
                item for item in weather_rows
                if matches_stay(str(item["start_date"]), str(item["end_date"]))
            ]
            # Elegimos una sola ventana dominante y la versión más reciente por
            # grupo, pero únicamente dentro del conjunto conocido *as of*.
            window_rows: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
            for item in weather_rows:
                window_rows[(item["start_date"], item["end_date"])].append(item)
            selected_window = max(
                window_rows,
                key=lambda window: (len(window_rows[window]), max(item["retrieved_at"] for item in window_rows[window])),
                default=None,
            )
            latest_by_location: dict[str, sqlite3.Row] = {}
            if selected_window is not None:
                for item in window_rows[selected_window]:
                    latest_by_location.setdefault(item["location_key"], item)
            weather_ids = [int(item["id"]) for item in latest_by_location.values()]
            if not weather_ids:
                continue
            prices = [
                float(row.pricePerNight)
                for row in rows
                if row.pricePerNight is not None
                and row.currency == "EUR"
                and str(row.checkIn or "") == str(selected_window[0])
                and str(row.checkOut or "") >= str(selected_window[1])
            ]
            if not prices:
                continue
            temperature_values: list[float] = []
            precipitation_values: list[float] = []
            covered_days = 0
            known_days = 0
            group_count = 0
            for weather_id in weather_ids:
                weather = self.weather_snapshot(weather_id)
                if not weather:
                    continue
                group_count += 1
                for day in weather.get("days") or []:
                    values = day.get("values") or {}
                    temperature = values.get("temperature_2m_max")
                    precipitation = values.get("precipitation_sum")
                    if isinstance(temperature, (int, float)):
                        temperature_values.append(float(temperature))
                    if isinstance(precipitation, (int, float)):
                        precipitation_values.append(float(precipitation))
                    covered_days += 1
                    if day.get("knownAtCapture"):
                        known_days += 1
            if not group_count or not covered_days:
                continue
            observations.append({
                "snapshotId": snapshot.id,
                "capturedAt": snapshot.scrapedAt,
                "adrMedian": _round(median(prices)),
                "adrObservations": len(prices),
                "temperatureMaxMeanC": _round(sum(temperature_values) / len(temperature_values)) if temperature_values else None,
                "precipitationMeanMm": _round(sum(precipitation_values) / len(precipitation_values)) if precipitation_values else None,
                "weatherGroups": group_count,
                "weatherDays": covered_days,
                "weatherStartDate": selected_window[0] if selected_window else None,
                "weatherEndDate": selected_window[1] if selected_window else None,
                "knownAtCaptureDays": known_days,
                "knownAtCapturePct": _round((known_days / covered_days) * 100),
                "eligibleAtCapture": known_days == covered_days,
            })

        pairs: list[dict] = []
        eligible_observations = [item for item in observations if item["eligibleAtCapture"]]
        for previous, current in zip(eligible_observations, eligible_observations[1:]):
            price_change = _pct_change(current["adrMedian"], previous["adrMedian"])
            temperature_change = None
            if current["temperatureMaxMeanC"] is not None and previous["temperatureMaxMeanC"] is not None:
                temperature_change = _round(current["temperatureMaxMeanC"] - previous["temperatureMaxMeanC"])
            precipitation_change = None
            if current["precipitationMeanMm"] is not None and previous["precipitationMeanMm"] is not None:
                precipitation_change = _round(current["precipitationMeanMm"] - previous["precipitationMeanMm"])
            pairs.append({
                "previousSnapshotId": previous["snapshotId"],
                "snapshotId": current["snapshotId"],
                "adrChangePct": _round(price_change) if price_change is not None else None,
                "temperatureChangeC": temperature_change,
                "precipitationChangeMm": precipitation_change,
            })

        valid_pairs = [
            pair for pair in pairs
            if isinstance(pair.get("adrChangePct"), (int, float))
            and isinstance(pair.get("temperatureChangeC"), (int, float))
        ]
        correlation = None
        if len(valid_pairs) >= 3:
            xs = [float(pair["temperatureChangeC"]) for pair in valid_pairs]
            ys = [float(pair["adrChangePct"]) for pair in valid_pairs]
            mean_x = sum(xs) / len(xs)
            mean_y = sum(ys) / len(ys)
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
            denominator_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
            denominator_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
            if denominator_x and denominator_y:
                correlation = _round(numerator / (denominator_x * denominator_y))
        return {
            "schemaVersion": "weather-price-association.v1",
            "targetId": target_id,
            "status": "ready" if len(valid_pairs) >= 3 and correlation is not None else "insufficient_sample",
            "observations": observations,
            "pairs": pairs,
            "samplePairs": len(valid_pairs),
            "temperatureAdrCorrelation": correlation,
            "method": "Cambios consecutivos de ADR mediano y temperatura máxima media por foto con meteorología enlazada.",
            "limitations": [
                "La tarifa es pública observada, no pickup, ocupación ni demanda real.",
                "La asociación no demuestra causalidad y no controla eventos, promociones o composición del producto.",
                "Solo entran en los pares las fotos cuya meteorología completa era conocida en el momento de la captura.",
                "Las fotos sin meteorología enlazada quedan fuera del cálculo.",
            ],
        }

    @staticmethod
    def _workspace_from_row(row: sqlite3.Row) -> dict:
        item = dict(row)
        return {
            "id": item["id"],
            "name": item["name"],
            "ownerKey": item["owner_key"],
            "targetIds": json.loads(item["target_ids"] or "[]"),
            "globalFilters": json.loads(item["global_filters"] or "{}"),
            "layers": json.loads(item["layers"] or "[]"),
            "version": item["version"],
            "createdAt": item["created_at"],
            "updatedAt": item["updated_at"],
        }

    def list_workspaces(self, owner_key: str = "local-revenue") -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM analysis_workspaces WHERE owner_key = ? ORDER BY updated_at DESC, id DESC",
            (owner_key,),
        ).fetchall()
        return [self._workspace_from_row(row) for row in rows]

    @staticmethod
    def _workspace_revision_from_row(row: sqlite3.Row) -> dict:
        item = dict(row)
        return {
            "id": item["id"],
            "workspaceId": item["workspace_id"],
            "ownerKey": item["owner_key"],
            "workspaceVersion": item["workspace_version"],
            "name": item["name"],
            "targetIds": json.loads(item["target_ids"] or "[]"),
            "globalFilters": json.loads(item["global_filters"] or "{}"),
            "layers": json.loads(item["layers"] or "[]"),
            "createdAt": item["created_at"],
        }

    def list_workspace_revisions(self, workspace_id: int, owner_key: str = "local-revenue") -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT * FROM analysis_workspace_revisions
            WHERE workspace_id = ? AND owner_key = ?
            ORDER BY workspace_version DESC, id DESC
            """,
            (workspace_id, owner_key),
        ).fetchall()
        return [self._workspace_revision_from_row(row) for row in rows]

    def _record_workspace_revision(self, workspace: dict) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO analysis_workspace_revisions
              (workspace_id, owner_key, workspace_version, name, target_ids, global_filters, layers, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workspace["id"], workspace["ownerKey"], workspace["version"], workspace["name"],
                json.dumps(workspace["targetIds"]), json.dumps(workspace["globalFilters"]),
                json.dumps(workspace["layers"]), workspace["updatedAt"],
            ),
        )

    def create_workspace(
        self,
        name: str,
        target_ids: list[int],
        global_filters: dict,
        layers: list[dict],
        owner_key: str = "local-revenue",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO analysis_workspaces
                  (name, owner_key, target_ids, global_filters, layers, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (name, owner_key, json.dumps(target_ids), json.dumps(global_filters), json.dumps(layers), now, now),
            )
            self.conn.commit()
        row = self.conn.execute("SELECT * FROM analysis_workspaces WHERE id = ?", (cursor.lastrowid,)).fetchone()
        workspace = self._workspace_from_row(row)
        with self.lock:
            self._record_workspace_revision(workspace)
            self.conn.commit()
        return workspace

    def update_workspace(
        self,
        workspace_id: int,
        name: str,
        target_ids: list[int],
        global_filters: dict,
        layers: list[dict],
        expected_version: int | None = None,
        owner_key: str = "local-revenue",
    ) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        query = """
          UPDATE analysis_workspaces
          SET name = ?, target_ids = ?, global_filters = ?, layers = ?,
              version = version + 1, updated_at = ?
          WHERE id = ? AND owner_key = ?
        """
        params: list = [name, json.dumps(target_ids), json.dumps(global_filters), json.dumps(layers), now, workspace_id, owner_key]
        if expected_version is not None:
            query += " AND version = ?"
            params.append(expected_version)
        with self.lock:
            cursor = self.conn.execute(query, params)
            self.conn.commit()
        if not cursor.rowcount:
            return None
        row = self.conn.execute("SELECT * FROM analysis_workspaces WHERE id = ?", (workspace_id,)).fetchone()
        workspace = self._workspace_from_row(row)
        with self.lock:
            self._record_workspace_revision(workspace)
            self.conn.commit()
        return workspace

    @staticmethod
    def _assistant_session_from_row(row: sqlite3.Row) -> dict:
        item = dict(row)
        return {
            "id": item["id"],
            "title": item["title"],
            "ownerKey": item["owner_key"],
            "targetId": item["target_id"],
            "mode": item["mode"],
            "status": item["status"],
            "pinned": bool(item["pinned"]),
            "summary": item["summary"] or "",
            "version": item["version"],
            "createdAt": item["created_at"],
            "updatedAt": item["updated_at"],
            "lastMessageAt": item["last_message_at"],
        }

    @staticmethod
    def _assistant_message_from_row(row: sqlite3.Row) -> dict:
        item = dict(row)
        return {
            "id": item["id"],
            "sessionId": item["session_id"],
            "sequence": item["sequence"],
            "role": item["role"],
            "content": item["content"],
            "visualization": json.loads(item["visualization"]) if item["visualization"] else None,
            "dataMeta": json.loads(item["data_meta"]) if item["data_meta"] else None,
            "requestId": item["request_id"],
            "createdAt": item["created_at"],
        }

    def list_assistant_sessions(
        self,
        owner_key: str = "local-revenue",
        query: str = "",
        include_archived: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        clauses = ["owner_key = ?"]
        params: list = [owner_key]
        if not include_archived:
            clauses.append("status = 'active'")
        clean_query = (query or "").strip()
        if clean_query:
            clauses.append("(title LIKE ? OR summary LIKE ? OR id IN (SELECT session_id FROM assistant_messages WHERE content LIKE ?))")
            term = f"%{clean_query[:120]}%"
            params.extend([term, term, term])
        params.append(limit)
        rows = self.conn.execute(
            f"SELECT * FROM assistant_sessions WHERE {' AND '.join(clauses)} "
            "ORDER BY pinned DESC, updated_at DESC, id DESC LIMIT ?",
            params,
        ).fetchall()
        return [self._assistant_session_from_row(row) for row in rows]

    def get_assistant_session(self, session_id: int, owner_key: str = "local-revenue") -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM assistant_sessions WHERE id = ? AND owner_key = ?",
            (session_id, owner_key),
        ).fetchone()
        return self._assistant_session_from_row(row) if row else None

    def create_assistant_session(
        self,
        title: str,
        target_id: int | None = None,
        mode: str = "quick",
        owner_key: str = "local-revenue",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        clean_mode = mode if mode in {"quick", "auto", "analysis", "decision"} else "auto"
        clean_title = (title or "Nueva consulta").strip()[:120] or "Nueva consulta"
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO assistant_sessions
                  (title, owner_key, target_id, mode, status, pinned, summary, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'active', 0, '', 1, ?, ?)
                """,
                (clean_title, owner_key, target_id, clean_mode, now, now),
            )
            self.conn.commit()
        row = self.conn.execute("SELECT * FROM assistant_sessions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._assistant_session_from_row(row)

    def update_assistant_session(
        self,
        session_id: int,
        *,
        title: str | None = None,
        mode: str | None = None,
        target_id: int | None = None,
        pinned: bool | None = None,
        status: str | None = None,
        expected_version: int | None = None,
        owner_key: str = "local-revenue",
    ) -> dict | None:
        current = self.get_assistant_session(session_id, owner_key)
        if current is None:
            return None
        fields: list[str] = []
        params: list = []
        if title is not None:
            fields.append("title = ?")
            params.append((title.strip() or current["title"])[:120])
        if mode in {"quick", "auto", "analysis", "decision"}:
            fields.append("mode = ?")
            params.append(mode)
        if target_id is not None:
            fields.append("target_id = ?")
            params.append(target_id)
        if pinned is not None:
            fields.append("pinned = ?")
            params.append(1 if pinned else 0)
        if status in {"active", "archived"}:
            fields.append("status = ?")
            params.append(status)
        if not fields:
            return current
        now = datetime.now(timezone.utc).isoformat()
        fields.extend(["version = version + 1", "updated_at = ?"])
        params.append(now)
        params.extend([session_id, owner_key])
        query = f"UPDATE assistant_sessions SET {', '.join(fields)} WHERE id = ? AND owner_key = ?"
        if expected_version is not None:
            query += " AND version = ?"
            params.append(expected_version)
        with self.lock:
            cursor = self.conn.execute(query, params)
            self.conn.commit()
        if not cursor.rowcount:
            return None
        return self.get_assistant_session(session_id, owner_key)

    def add_assistant_message(
        self,
        session_id: int,
        role: str,
        content: str,
        *,
        visualization: dict | None = None,
        data_meta: dict | None = None,
        request_id: str | None = None,
        owner_key: str = "local-revenue",
    ) -> dict:
        session = self.get_assistant_session(session_id, owner_key)
        if session is None:
            raise ValueError("Sesión de Copilot no encontrada")
        now = datetime.now(timezone.utc).isoformat()
        row = self.conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence FROM assistant_messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        sequence = int(row["next_sequence"])
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO assistant_messages
                  (session_id, sequence, role, content, visualization, data_meta, request_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    sequence,
                    role if role in {"user", "assistant", "system", "tool"} else "assistant",
                    content,
                    json.dumps(visualization, ensure_ascii=False) if visualization else None,
                    json.dumps(data_meta, ensure_ascii=False) if data_meta else None,
                    request_id,
                    now,
                ),
            )
            self.conn.execute(
                "UPDATE assistant_sessions SET updated_at = ?, last_message_at = ?, version = version + 1 WHERE id = ? AND owner_key = ?",
                (now, now, session_id, owner_key),
            )
            self.conn.commit()
        message = self.conn.execute("SELECT * FROM assistant_messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._assistant_message_from_row(message)

    def list_assistant_messages(
        self,
        session_id: int,
        *,
        limit: int = 80,
        before_sequence: int | None = None,
        owner_key: str = "local-revenue",
    ) -> list[dict]:
        if self.get_assistant_session(session_id, owner_key) is None:
            return []
        limit = max(1, min(int(limit), 200))
        if before_sequence is None:
            rows = self.conn.execute(
                "SELECT * FROM assistant_messages WHERE session_id = ? ORDER BY sequence DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM assistant_messages WHERE session_id = ? AND sequence < ? ORDER BY sequence DESC LIMIT ?",
                (session_id, before_sequence, limit),
            ).fetchall()
        return [self._assistant_message_from_row(row) for row in reversed(rows)]

    def add_assistant_attachment(self, session_id: int, owner_key: str, metadata: dict) -> dict:
        session = self.get_assistant_session(session_id, owner_key)
        if session is None:
            raise ValueError("Sesión de Copilot no encontrada")
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            cur = self.conn.execute(
                """INSERT INTO assistant_attachments
                (session_id, owner_key, filename, media_type, size_bytes, sha256, storage_path, extracted_text, extraction_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, owner_key, metadata["filename"], metadata["mediaType"], metadata["sizeBytes"],
                 metadata["sha256"], metadata["storagePath"], metadata.get("extractedText", ""),
                 metadata.get("extractionStatus", "pending"), now),
            )
            self.conn.commit()
        return self.get_assistant_attachment(cur.lastrowid, owner_key) or {}

    def get_assistant_attachment(self, attachment_id: int, owner_key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM assistant_attachments WHERE id = ? AND owner_key = ?",
            (attachment_id, owner_key),
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        return {
            "id": item["id"], "sessionId": item["session_id"], "filename": item["filename"],
            "mediaType": item["media_type"], "sizeBytes": item["size_bytes"], "sha256": item["sha256"],
            "storagePath": item["storage_path"], "extractedText": item["extracted_text"],
            "extractionStatus": item["extraction_status"], "createdAt": item["created_at"],
        }

    def list_assistant_attachments(self, session_id: int, owner_key: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id FROM assistant_attachments WHERE session_id = ? AND owner_key = ? ORDER BY created_at ASC, id ASC",
            (session_id, owner_key),
        ).fetchall()
        return [self.get_assistant_attachment(row["id"], owner_key) for row in rows]

    def create_assistant_run(self, session_id: int, telemetry: dict, assistant_message_id: int | None = None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        usage = telemetry.get("usage") if isinstance(telemetry.get("usage"), dict) else None
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO assistant_runs
                  (session_id, assistant_message_id, request_id, model, mode, outcome, latency_ms,
                   endpoint_latency_ms, tool_rounds, tool_calls, context_chars, usage, cost_usd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    assistant_message_id,
                    telemetry.get("requestId"),
                    telemetry.get("model"),
                    telemetry.get("mode"),
                    telemetry.get("outcome", "unknown"),
                    telemetry.get("latencyMs"),
                    telemetry.get("endpointLatencyMs"),
                    telemetry.get("toolRounds", 0),
                    telemetry.get("toolCalls", 0),
                    telemetry.get("contextChars"),
                    json.dumps(usage, ensure_ascii=False) if usage else None,
                    float(telemetry.get("costUsd") or (usage or {}).get("cost") or 0),
                    now,
                ),
            )
            self.conn.commit()
        return {"id": cursor.lastrowid, "sessionId": session_id, "requestId": telemetry.get("requestId")}

    def assistant_month_spend(self, owner_key: str, month_prefix: str) -> float:
        row = self.conn.execute(
            """SELECT COALESCE(SUM(ar.cost_usd), 0) AS total
               FROM assistant_runs ar JOIN assistant_sessions s ON s.id = ar.session_id
               WHERE s.owner_key = ? AND ar.created_at LIKE ?""",
            (owner_key, f"{month_prefix}%"),
        ).fetchone()
        return float(row["total"] or 0) if row else 0.0

    def reserve_assistant_budget(
        self,
        owner_key: str,
        request_id: str,
        amount_usd: float,
        monthly_budget_usd: float,
        month_prefix: str,
    ) -> dict | None:
        """Atomically hold a task cap while a Copilot request is running.

        The reservation is deliberately conservative: the task cap is held
        until the provider reports usage and ``settle_assistant_budget`` is
        called. This prevents concurrent requests from spending the same
        remaining monthly balance.
        """
        amount = max(0.0, round(float(amount_usd), 6))
        if amount <= 0:
            return {"requestId": request_id, "status": "not_required", "reservedUsd": 0.0}
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            existing = self.conn.execute(
                "SELECT * FROM assistant_budget_reservations WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if existing:
                item = dict(existing)
                return {
                    "requestId": item["request_id"], "status": item["status"],
                    "reservedUsd": float(item["reserved_usd"] or 0),
                    "actualCostUsd": float(item["actual_cost_usd"] or 0),
                }
            spent_row = self.conn.execute(
                """SELECT COALESCE(SUM(ar.cost_usd), 0) AS total
                   FROM assistant_runs ar JOIN assistant_sessions s ON s.id = ar.session_id
                   WHERE s.owner_key = ? AND ar.created_at LIKE ?""",
                (owner_key, f"{month_prefix}%"),
            ).fetchone()
            reserved_row = self.conn.execute(
                """SELECT COALESCE(SUM(reserved_usd), 0) AS total
                   FROM assistant_budget_reservations
                   WHERE owner_key = ? AND month_prefix = ? AND status = 'reserved'""",
                (owner_key, month_prefix),
            ).fetchone()
            committed = float((spent_row or {"total": 0})["total"] or 0) + float((reserved_row or {"total": 0})["total"] or 0)
            if committed + amount > float(monthly_budget_usd):
                return None
            self.conn.execute(
                """INSERT INTO assistant_budget_reservations
                   (request_id, owner_key, month_prefix, reserved_usd, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'reserved', ?, ?)""",
                (request_id, owner_key, month_prefix, amount, now, now),
            )
            self.conn.commit()
        return {"requestId": request_id, "status": "reserved", "reservedUsd": amount, "actualCostUsd": None}

    def settle_assistant_budget(self, request_id: str, actual_cost_usd: float | None = None) -> dict | None:
        """Close a reservation with the provider-reported cost."""
        actual = max(0.0, round(float(actual_cost_usd or 0), 6))
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM assistant_budget_reservations WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if row is None:
                return None
            self.conn.execute(
                """UPDATE assistant_budget_reservations
                   SET actual_cost_usd = ?, status = 'settled', updated_at = ?
                   WHERE request_id = ?""",
                (actual, now, request_id),
            )
            self.conn.commit()
        return {"requestId": request_id, "status": "settled", "actualCostUsd": actual}

    def assistant_budget_state(self, owner_key: str, month_prefix: str, monthly_budget_usd: float) -> dict:
        spent = self.assistant_month_spend(owner_key, month_prefix)
        row = self.conn.execute(
            """SELECT COALESCE(SUM(reserved_usd), 0) AS total
               FROM assistant_budget_reservations
               WHERE owner_key = ? AND month_prefix = ? AND status = 'reserved'""",
            (owner_key, month_prefix),
        ).fetchone()
        reserved = float(row["total"] or 0) if row else 0.0
        return {
            "month": month_prefix,
            "spentUsd": round(spent, 6),
            "reservedUsd": round(reserved, 6),
            "budgetUsd": float(monthly_budget_usd),
            "remainingUsd": round(max(0.0, float(monthly_budget_usd) - spent - reserved), 6),
            "warning": spent + reserved >= float(monthly_budget_usd) * 0.8,
        }

    def record_copilot_evaluation(self, result: dict, *, source: str, provider_live: bool) -> dict:
        """Guarda solo el resultado técnico de una evaluación, nunca el texto generado."""
        groups = ("routing", "dataGate", "cases")
        cases = [item for group in groups for item in result.get(group, []) if isinstance(item, dict)]
        passed_count = sum(
            1
            for item in cases
            if item.get("passed") is True
            or (item.get("status") == "ok" and item.get("assessment", {}).get("status") == "ok")
        )
        warning_count = sum(
            1
            for item in cases
            if item.get("status") == "warning" or item.get("assessment", {}).get("status") == "warning"
        )
        error_count = sum(1 for item in cases if item.get("status") == "error")
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO copilot_evaluation_runs
                  (source, profile, provider_live, passed, case_count, passed_count, warning_count, error_count, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source[:40],
                    str(result.get("profile") or "offline")[:40],
                    1 if provider_live else 0,
                    1 if result.get("passed") else 0,
                    len(cases),
                    passed_count,
                    warning_count,
                    error_count,
                    json.dumps(result, ensure_ascii=False),
                    now,
                ),
            )
            self.conn.commit()
        return {"id": cursor.lastrowid, "createdAt": now, "passed": bool(result.get("passed"))}

    def latest_copilot_evaluation(self) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM copilot_evaluation_runs ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        item = dict(row)
        return {
            "id": item["id"],
            "source": item["source"],
            "profile": item["profile"],
            "providerLive": bool(item["provider_live"]),
            "passed": bool(item["passed"]),
            "caseCount": item["case_count"],
            "passedCount": item["passed_count"],
            "warningCount": item["warning_count"],
            "errorCount": item["error_count"],
            "createdAt": item["created_at"],
        }

    def purge_assistant_runs(self, retention_days: int) -> int:
        """Elimina telemetría vencida; no toca sesiones ni mensajes de Copilot."""
        safe_days = max(1, int(retention_days))
        cutoff = datetime.fromtimestamp(
            datetime.now(timezone.utc).timestamp() - safe_days * 86400, timezone.utc
        ).isoformat()
        with self.lock:
            cursor = self.conn.execute("DELETE FROM assistant_runs WHERE created_at < ?", (cutoff,))
            self.conn.commit()
        return int(cursor.rowcount)

    def _ensure_column(self, table: str, column: str, column_type: str) -> None:
        with self.lock:
            columns = [row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})")]
            if column not in columns:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                self.conn.commit()

    def bootstrap_hotel_review_workspace(self, legacy_dir: Path | None = None) -> dict:
        """Build canonical hotel rows from captured Booking inventory and import pilot TSV once."""
        self._ensure_column("hotel_reviews", "last_run_id", "TEXT")
        now = _now()
        with self.lock:
            self.conn.execute(
                """
                WITH ranked AS (
                  SELECT msh.*, ms.scraped_at,
                         ROW_NUMBER() OVER (PARTITION BY msh.hotel_key ORDER BY ms.scraped_at DESC, msh.id DESC) AS rn
                  FROM market_snapshot_hotels msh
                  JOIN market_snapshots ms ON ms.id = msh.snapshot_id
                )
                INSERT OR IGNORE INTO hotel_inventory (
                  hotel_key, hotel_id, hotel_name, detail_url, stars, accommodation_type,
                  review_score, review_count, source, first_seen_at, last_seen_at, updated_at,
                  latitude, longitude, address, city, country_code, display_location, completeness
                )
                SELECT ranked.hotel_key, ranked.hotel_id, ranked.hotel_name, ranked.detail_url,
                       ranked.rating, ranked.accommodation_type, ranked.rating, ranked.review_count,
                       'booking_graphql', COALESCE(ranked.scraped_at, ?), COALESCE(ranked.scraped_at, ?),
                       COALESCE(ranked.scraped_at, ?), loc.latitude, loc.longitude, loc.address,
                       NULL, NULL, NULL, 0
                FROM ranked LEFT JOIN hotel_locations loc ON loc.hotel_key = ranked.hotel_key
                WHERE ranked.rn = 1 AND ranked.hotel_key <> ''
                """, (now, now, now),
            )
            # `market_snapshot_hotels.rating` is Booking's review score, not
            # the hotel's star category. Older snapshots never collected the
            # classification, so remove the value that the initial backfill
            # copied into `stars` and recalculate completeness from real facts.
            inventory_rows = self.conn.execute("SELECT * FROM hotel_inventory").fetchall()
            for raw in inventory_rows:
                row = dict(raw)
                if row.get("source") == "booking_graphql" and row.get("stars") is not None and row.get("stars") == row.get("review_score"):
                    row["stars"] = None
                    self.conn.execute("UPDATE hotel_inventory SET stars=NULL WHERE hotel_key=?", (row["hotel_key"],))
                self.conn.execute("UPDATE hotel_inventory SET completeness=? WHERE hotel_key=?",
                                  (self._inventory_completeness(row), row["hotel_key"]))
            # Pilot aliases are deterministic; Monte Feliz is not present in the
            # current Booking snapshots and gets its own stable Atlas key.
            pilot_rows = (
                ("Servatur Puerto Azul", "servatur-puerto-azul", "CgsI5PHLm5bztcX7ARAB", "https://www.servatur.com/puerto-azul/"),
                ("Servatur Monte Feliz", "servatur-monte-feliz", "CgsIwPKo4JSArfaRARAB", "https://www.servatur.com/monte-feliz/"),
                ("Servatur Waikiki", "servatur-waikiki", "ChoInI3H9t2BqJDJARoNL2cvMTFjbTE4eWc0MhAB", "https://www.servatur.com/waikiki/"),
            )
            hotel_keys: dict[str, str] = {}
            for name, slug, entity_id, official_url in pilot_rows:
                found = self.conn.execute(
                    "SELECT hotel_key FROM hotel_inventory WHERE lower(hotel_name) = lower(?) ORDER BY last_seen_at DESC LIMIT 1",
                    (name,),
                ).fetchone()
                key = found["hotel_key"] if found else f"atlas:{slug}"
                if not found:
                    self.conn.execute(
                        """INSERT OR IGNORE INTO hotel_inventory
                           (hotel_key, hotel_name, detail_url, source, first_seen_at, last_seen_at, updated_at, completeness)
                           VALUES (?, ?, ?, 'manual', ?, ?, ?, 0)""", (key, name, official_url, now, now, now),
                    )
                hotel_keys[name] = key
                self.conn.execute(
                    "INSERT OR IGNORE INTO hotel_name_aliases(hotel_key, alias, source, created_at) VALUES (?, ?, 'pilot', ?)",
                    (key, name, now),
                )
                self.conn.execute(
                    "INSERT OR IGNORE INTO hotel_source_links(hotel_key,source,external_id,url,external_name,verified,updated_at) VALUES (?,?,?,?,?,1,?)",
                    (key, "google_hotels", entity_id, f"https://www.google.com/travel/hotels/entity/{entity_id}/reviews?gl=es&hl=es", name, now),
                )
                maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(name + ' Gran Canaria')}"
                self.conn.execute(
                    "INSERT OR IGNORE INTO hotel_source_links(hotel_key,source,url,external_name,verified,updated_at) VALUES (?, 'google_maps', ?, ?, 0, ?)",
                    (key, maps_url, name, now),
                )
            for row in self.conn.execute("SELECT hotel_key, hotel_id, hotel_name, detail_url FROM hotel_inventory").fetchall():
                if row["detail_url"] and "booking.com" in row["detail_url"].casefold():
                    self.conn.execute(
                        "INSERT OR IGNORE INTO hotel_source_links(hotel_key,source,external_id,url,external_name,verified,updated_at) VALUES (?, 'booking', ?, ?, ?, 1, ?)",
                        (row["hotel_key"], row["hotel_id"], row["detail_url"], row["hotel_name"], now),
                    )
            for row in self.conn.execute("SELECT hotel_key,hotel_name,city,address FROM hotel_inventory").fetchall():
                search_terms = " ".join(part for part in (row["hotel_name"], row["address"], row["city"], "Gran Canaria") if part)
                candidate_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(search_terms)}"
                self.conn.execute(
                    "INSERT OR IGNORE INTO hotel_source_links(hotel_key,source,url,external_name,verified,updated_at) VALUES (?, 'google_maps', ?, ?, 0, ?)",
                    (row["hotel_key"], candidate_url, row["hotel_name"], now),
                )
            self.conn.commit()
        imported = 0
        if legacy_dir:
            imported = self.import_legacy_google_reviews(legacy_dir, hotel_keys)
        with self.lock:
            self.conn.execute("UPDATE hotel_reviews SET last_run_id=COALESCE(last_run_id,run_id)")
            for raw in self.conn.execute(
                """SELECT r.* FROM hotel_reviews r
                   WHERE NOT EXISTS (SELECT 1 FROM hotel_review_versions v WHERE v.review_id=r.id)"""
            ).fetchall():
                self._record_hotel_review_version(raw["id"], raw["run_id"], dict(raw), raw["first_seen_at"])
            self.conn.commit()
        return {"hotels": self.conn.execute("SELECT COUNT(*) FROM hotel_inventory").fetchone()[0], "pilotReviewsImported": imported}

    def import_legacy_google_reviews(self, legacy_dir: Path, pilot_keys: dict[str, str]) -> int:
        path = legacy_dir / "google-reviews-results.csv"
        if not path.is_file():
            return 0
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        with self.lock:
            marker = self.conn.execute("SELECT sha256 FROM hotel_review_legacy_imports WHERE source_file = ?", (path.name,)).fetchone()
            if marker and marker["sha256"] == digest:
                return 0
        imported = 0
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = csv.DictReader(handle, delimiter="\t")
            for row in rows:
                name = (row.get("requested_hotel") or "").strip()
                hotel_key = pilot_keys.get(name)
                if not hotel_key:
                    continue
                original = (row.get("review_original") or "").strip()
                spanish = (row.get("review_es") or "").strip()
                if not original and spanish:
                    original = spanish
                captured_at = (row.get("captured_at") or _now()).strip()
                rating = _safe_float(row.get("rating"))
                review_id = (row.get("review_id") or "").strip() or None
                fingerprint_source = review_id or "|".join((row.get("author") or "", str(rating), original,
                                                              row.get("relative_published_at") or ""))
                fingerprint = hashlib.sha256(f"google\0{hotel_key}\0{fingerprint_source}".encode("utf-8")).hexdigest()
                values = (hotel_key, "google", review_id, fingerprint, row.get("author") or None, None, rating, 5,
                          None, None, original or None, spanish or None, row.get("language_original") or None,
                          _safe_float(row.get("language_confidence")), row.get("translation_method") or None,
                          row.get("published_at") or None, "exact" if row.get("published_at") else ("relative" if row.get("relative_published_at") else "unknown"),
                          row.get("relative_published_at") or None, row.get("source_url") or "", captured_at, captured_at,
                          None, "[]", json.dumps(["legacy_import"], ensure_ascii=False))
                with self.lock:
                    cursor = self.conn.execute(
                        """INSERT OR IGNORE INTO hotel_reviews
                        (hotel_key,source,source_review_id,review_fingerprint,author,title,rating,rating_scale,
                         positive_text,negative_text,review_original,review_es,language_original,language_confidence,
                         translation_method,published_at,date_precision,relative_published_at,source_url,first_seen_at,
                         last_seen_at,run_id,discovery_contexts_json,quality_flags_json)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values,
                    )
                    imported += max(0, cursor.rowcount)
        with self.lock:
            self.conn.execute(
                "INSERT INTO hotel_review_legacy_imports(source_file,sha256,rows_imported,imported_at) VALUES (?,?,?,?) "
                "ON CONFLICT(source_file) DO UPDATE SET sha256=excluded.sha256,rows_imported=excluded.rows_imported,imported_at=excluded.imported_at",
                (path.name, digest, imported, _now()),
            )
            for name, key in pilot_keys.items():
                status_file = legacy_dir / "hotel-status.csv"
                if not status_file.is_file():
                    continue
                with status_file.open("r", encoding="utf-8-sig", newline="") as handle:
                    for status in csv.DictReader(handle, delimiter="\t"):
                        if status.get("requested_hotel") != name:
                            continue
                        source_url = status.get("source_url") or ""
                        run_id = "legacy-google-" + key.rsplit("/", 1)[-1]
                        self.conn.execute(
                            """INSERT OR IGNORE INTO hotel_review_runs
                            (id,hotel_key,source,status,source_url,max_reviews,rows_seen,rows_inserted,coverage_json,error,started_at,completed_at)
                            VALUES (?,?, 'google', 'partial', ?, 1000, ?, ?, ?, ?, ?, ?)""",
                            (run_id, key, source_url, int(status.get("reviews_captured") or 0),
                             int(status.get("reviews_captured") or 0), json.dumps({
                                 "imported": True, "publishedReviewCount": _safe_int(status.get("google_review_count")),
                                 "aggregateRating": _safe_float(status.get("aggregate_rating")),
                                 "coverageStatement": "Legacy capture sampled public topic and sort views; completeness unverified.",
                             }), status.get("message") or "Cobertura histórica parcial no verificada.",
                             status.get("captured_at") or _now(), status.get("captured_at") or _now()),
                        )
                        self.conn.execute(
                            """INSERT OR IGNORE INTO hotel_attribute_observations
                            (hotel_key,attribute,value_json,source,observed_at,selected) VALUES (?,?,?,?,?,0)""",
                            (key, "google_aggregate", json.dumps({"rating": _safe_float(status.get("aggregate_rating")),
                                                                    "reviewCount": _safe_int(status.get("google_review_count"))}),
                             "google", status.get("captured_at") or _now()),
                        )
            self.conn.commit()
        return imported

    def can_access_hotel(self, owner_key: str, hotel_key: str) -> bool:
        identity = self.conn.execute("SELECT role,active FROM app_identities WHERE owner_key=?", (owner_key,)).fetchone()
        if identity and identity["active"] and identity["role"] == "admin":
            return self.get_hotel_inventory(hotel_key) is not None
        return bool(self.conn.execute(
            """SELECT 1 FROM market_snapshot_hotels msh
               JOIN market_snapshots ms ON ms.id=msh.snapshot_id
               JOIN market_access ma ON ma.target_id=ms.target_id
               WHERE ma.owner_key=? AND msh.hotel_key=?
               UNION ALL
               SELECT 1 FROM hotel_name_aliases hna
               WHERE hna.hotel_key=? AND hna.source='pilot'
                 AND EXISTS (SELECT 1 FROM market_access ma WHERE ma.owner_key=?)
               LIMIT 1""", (owner_key, hotel_key, hotel_key, owner_key)
        ).fetchone())

    def hotel_review_catalog(self, *, query: str = "", limit: int = 100, offset: int = 0, owner_key: str | None = None) -> dict:
        safe_limit = max(1, min(200, int(limit)))
        safe_offset = max(0, int(offset))
        params: list = []
        where = ""
        if query.strip():
            where = "WHERE lower(hi.hotel_name || ' ' || COALESCE(hi.city,'') || ' ' || COALESCE(hi.address,'')) LIKE ?"
            params.append(f"%{query.strip().casefold()[:100]}%")
        if owner_key:
            identity = self.conn.execute("SELECT role,active FROM app_identities WHERE owner_key=?", (owner_key,)).fetchone()
            if not identity or not identity["active"] or identity["role"] != "admin":
                access_clause = "(EXISTS (SELECT 1 FROM market_snapshot_hotels ax JOIN market_snapshots ams ON ams.id=ax.snapshot_id JOIN market_access ama ON ama.target_id=ams.target_id WHERE ax.hotel_key=hi.hotel_key AND ama.owner_key=?) OR (EXISTS (SELECT 1 FROM hotel_name_aliases hna WHERE hna.hotel_key=hi.hotel_key AND hna.source='pilot') AND EXISTS (SELECT 1 FROM market_access ama WHERE ama.owner_key=?)))"
                where = f"{where} {'AND' if where else 'WHERE'} {access_clause}"
                params.extend([owner_key, owner_key])
        total = self.conn.execute(f"SELECT COUNT(*) FROM hotel_inventory hi {where}", params).fetchone()[0]
        rows = self.conn.execute(
            f"""SELECT hi.hotel_key, hi.hotel_name, hi.detail_url, hi.city, hi.country_code, hi.address,
                       hi.stars, hi.accommodation_type, hi.latitude, hi.longitude,
                       (SELECT COUNT(*) FROM hotel_reviews r WHERE r.hotel_key=hi.hotel_key) AS review_count,
                       (SELECT MAX(last_seen_at) FROM hotel_reviews r WHERE r.hotel_key=hi.hotel_key) AS last_review_at
                FROM hotel_inventory hi {where}
                ORDER BY hi.hotel_name COLLATE NOCASE, hi.hotel_key LIMIT ? OFFSET ?""",
            [*params, safe_limit, safe_offset],
        ).fetchall()
        items = []
        for raw in rows:
            item = dict(raw)
            item["links"] = [dict(link) for link in self.conn.execute(
                "SELECT source, external_id AS externalId, url, external_name AS externalName, verified, updated_at AS updatedAt FROM hotel_source_links WHERE hotel_key=? ORDER BY source",
                (item["hotel_key"],),
            ).fetchall()]
            item["reviewSources"] = [dict(source) for source in self.conn.execute(
                "SELECT source,COUNT(*) AS captured,AVG(rating) AS sampleAverage FROM hotel_reviews WHERE hotel_key=? GROUP BY source ORDER BY source",
                (item["hotel_key"],),
            ).fetchall()]
            item["sources"] = [dict(source) for source in self.conn.execute(
                "SELECT source, status, started_at AS startedAt, completed_at AS completedAt, rows_seen AS rowsSeen, rows_inserted AS rowsInserted, error FROM hotel_review_runs WHERE hotel_key=? ORDER BY started_at DESC LIMIT 3",
                (item["hotel_key"],),
            ).fetchall()]
            items.append(item)
        return {"items": items, "total": int(total), "limit": safe_limit, "offset": safe_offset}

    def hotel_review_profile(self, hotel_key: str, owner_key: str | None = None) -> dict | None:
        hotel = self.get_hotel_inventory(hotel_key)
        if hotel is None:
            return None
        inventory = dict(hotel)
        links = [dict(row) for row in self.conn.execute(
            "SELECT source, external_id AS externalId, url, external_name AS externalName, verified, updated_at AS updatedAt FROM hotel_source_links WHERE hotel_key=? ORDER BY source",
            (hotel_key,),
        ).fetchall()]
        aliases = [row[0] for row in self.conn.execute(
            "SELECT alias FROM hotel_name_aliases WHERE hotel_key=? ORDER BY alias COLLATE NOCASE", (hotel_key,)
        ).fetchall()]
        observations: dict[str, list] = defaultdict(list)
        for row in self.conn.execute(
            "SELECT id,attribute,value_json,source,observed_at,selected FROM hotel_attribute_observations WHERE hotel_key=? ORDER BY observed_at DESC,id DESC",
            (hotel_key,),
        ).fetchall():
            try:
                value = json.loads(row["value_json"])
            except (TypeError, ValueError):
                value = row["value_json"]
            observations[row["attribute"]].append({"id": row["id"], "value": value, "source": row["source"],
                                                     "observedAt": row["observed_at"], "selected": bool(row["selected"])})
        source_stats = []
        for row in self.conn.execute(
            "SELECT source, COUNT(*) AS captured, SUM(CASE WHEN COALESCE(review_original,'')<>'' OR COALESCE(review_es,'')<>'' OR COALESCE(positive_text,'')<>'' OR COALESCE(negative_text,'')<>'' THEN 1 ELSE 0 END) AS withText, AVG(rating) AS sampleAverage FROM hotel_reviews WHERE hotel_key=? GROUP BY source ORDER BY source",
            (hotel_key,),
        ).fetchall():
            stats = dict(row)
            stats["ratingScale"] = self.conn.execute(
                "SELECT MAX(rating_scale) FROM hotel_reviews WHERE hotel_key=? AND source=?",
                (hotel_key, row["source"]),
            ).fetchone()[0]
            stats["ratingDistribution"] = [dict(value) for value in self.conn.execute(
                "SELECT rating,COUNT(*) AS count FROM hotel_reviews WHERE hotel_key=? AND source=? AND rating IS NOT NULL GROUP BY rating ORDER BY rating DESC",
                (hotel_key, row["source"]),
            ).fetchall()]
            stats["datedTrend"] = [dict(value) for value in self.conn.execute(
                "SELECT substr(published_at,1,7) AS month,COUNT(*) AS count,AVG(rating) AS sampleAverage FROM hotel_reviews WHERE hotel_key=? AND source=? AND date_precision='exact' AND published_at IS NOT NULL GROUP BY substr(published_at,1,7) ORDER BY month",
                (hotel_key, row["source"]),
            ).fetchall()]
            run_sources = ("google", "google_maps", "google_hotels") if row["source"] == "google" else (row["source"],)
            placeholders = ",".join("?" for _ in run_sources)
            latest = self.conn.execute(
                f"SELECT status,coverage_json,started_at FROM hotel_review_runs WHERE hotel_key=? AND source IN ({placeholders}) ORDER BY started_at DESC LIMIT 1",
                (hotel_key, *run_sources),
            ).fetchone()
            stats["latestRun"] = None
            if latest:
                try:
                    coverage = json.loads(latest["coverage_json"] or "{}")
                except (TypeError, ValueError):
                    coverage = {}
                stats["latestRun"] = {"status": latest["status"], "coverage": coverage, "startedAt": latest["started_at"]}
            source_stats.append(stats)
        if inventory.get("review_score") is not None or inventory.get("review_count") is not None:
            if not any(item["source"] == "booking" for item in source_stats):
                source_stats.append({"source": "booking", "captured": 0, "withText": 0, "sampleAverage": None,
                                     "ratingScale": 10, "ratingDistribution": [], "datedTrend": [], "latestRun": None})
        if self.conn.execute(
            "SELECT 1 FROM hotel_attribute_observations WHERE hotel_key=? AND attribute='google_aggregate' LIMIT 1", (hotel_key,)
        ).fetchone() and not any(item["source"] == "google" for item in source_stats):
            source_stats.append({"source": "google", "captured": 0, "withText": 0, "sampleAverage": None,
                                 "ratingScale": 5, "ratingDistribution": [], "datedTrend": [], "latestRun": None})
        for source, attribute, fallback_score, fallback_count in (
            ("google", "google_aggregate", None, None),
            ("booking", "booking_aggregate", inventory.get("review_score"), inventory.get("review_count")),
        ):
            if not any(item["source"] == source for item in source_stats):
                continue
            observation = self.conn.execute(
                "SELECT value_json,source,observed_at FROM hotel_attribute_observations WHERE hotel_key=? AND attribute=? ORDER BY selected DESC,observed_at DESC,id DESC LIMIT 1",
                (hotel_key, attribute),
            ).fetchone()
            try: aggregate = json.loads(observation["value_json"]) if observation else {}
            except (TypeError, ValueError): aggregate = {}
            source_row = next(item for item in source_stats if item["source"] == source)
            source_row["publishedRating"] = aggregate.get("rating") if aggregate.get("rating") is not None else fallback_score
            source_row["publishedReviewCount"] = aggregate.get("reviewCount") if aggregate.get("reviewCount") is not None else fallback_count
            source_row["aggregateSource"] = observation["source"] if observation else ("booking_graphql" if fallback_score is not None else None)
            source_row["aggregateObservedAt"] = observation["observed_at"] if observation else inventory.get("updated_at")
        latest_run = [dict(row) for row in self.conn.execute(
            "SELECT id,source,status,source_url AS sourceUrl,budget_usd AS budgetUsd,rows_seen AS rowsSeen,rows_inserted AS rowsInserted,rows_updated AS rowsUpdated,estimated_spend_usd AS estimatedSpendUsd,actual_spend_usd AS actualSpendUsd,error,coverage_json,started_at AS startedAt,completed_at AS completedAt FROM hotel_review_runs WHERE hotel_key=? ORDER BY started_at DESC LIMIT 30",
            (hotel_key,),
        ).fetchall()]
        for run in latest_run:
            try: run["coverage"] = json.loads(run.pop("coverage_json") or "{}")
            except (TypeError, ValueError): run["coverage"] = {}
        notes_sql = "SELECT id,review_id AS reviewId,owner_key AS ownerKey,body,created_at AS createdAt,updated_at AS updatedAt FROM hotel_review_notes WHERE hotel_key=?"
        notes_params = [hotel_key]
        if owner_key:
            notes_sql += " AND owner_key=?"; notes_params.append(owner_key)
        notes_sql += " ORDER BY updated_at DESC LIMIT 100"
        notes = [dict(row) for row in self.conn.execute(notes_sql, notes_params).fetchall()]
        analysis = self.latest_hotel_review_analysis(hotel_key)
        return {"hotel": inventory, "links": links, "aliases": aliases, "attributes": observations,
                "sources": source_stats, "runs": latest_run, "notes": notes, "analysis": analysis}

    def hotel_review_rows(self, hotel_key: str, *, source: str | None = None, language: str | None = None,
                          rating: int | None = None, topic: str | None = None, query: str = "",
                          review_id: int | None = None, date_from: str | None = None, date_to: str | None = None,
                          limit: int = 50, offset: int = 0) -> dict:
        safe_limit = max(1, min(100, int(limit)))
        safe_offset = max(0, int(offset))
        clauses, params = ["hotel_key=?"], [hotel_key]
        if review_id is not None:
            clauses.append("id=?"); params.append(int(review_id))
        if source in {"google", "booking"}:
            clauses.append("source=?"); params.append(source)
        if language:
            clauses.append("language_original=?"); params.append(language.upper()[:8])
        if rating is not None:
            clauses.append("rating=?"); params.append(float(rating))
        if date_from:
            clauses.append("date_precision='exact' AND published_at>=?"); params.append(date_from)
        if date_to:
            date_to_exclusive = (datetime.fromisoformat(date_to) + timedelta(days=1)).date().isoformat()
            clauses.append("date_precision='exact' AND published_at<?"); params.append(date_to_exclusive)
        if topic:
            clauses.append("id IN (SELECT review_id FROM hotel_review_topics WHERE hotel_key=? AND topic=?)")
            params.extend([hotel_key, topic[:100]])
        if query.strip():
            needle = f"%{query.strip()[:100]}%"
            clauses.append("(COALESCE(title,'') LIKE ? OR COALESCE(review_original,'') LIKE ? OR COALESCE(review_es,'') LIKE ? OR COALESCE(positive_text,'') LIKE ? OR COALESCE(negative_text,'') LIKE ?)")
            params.extend([needle] * 5)
        where = " AND ".join(clauses)
        total = self.conn.execute(f"SELECT COUNT(*) FROM hotel_reviews WHERE {where}", params).fetchone()[0]
        items = [dict(row) for row in self.conn.execute(
            f"""SELECT id,source,source_review_id AS sourceReviewId,author,title,rating,rating_scale AS ratingScale,
                       positive_text AS positiveText,negative_text AS negativeText,review_original AS reviewOriginal,
                       review_es AS reviewEs,language_original AS languageOriginal,language_confidence AS languageConfidence,
                       translation_method AS translationMethod,published_at AS publishedAt,date_precision AS datePrecision,
                       relative_published_at AS relativePublishedAt,source_url AS sourceUrl,first_seen_at AS firstSeenAt,
                       last_seen_at AS lastSeenAt,run_id AS originRunId,last_run_id AS latestRunId,
                       (SELECT COUNT(*) FROM hotel_review_versions v WHERE v.review_id=hotel_reviews.id) AS versionCount,
                       discovery_contexts_json AS discoveryContextsJson,quality_flags_json AS qualityFlagsJson,
                       (SELECT group_concat(topic, ', ') FROM hotel_review_topics t WHERE t.review_id=hotel_reviews.id) AS topics
                FROM hotel_reviews WHERE {where} ORDER BY published_at IS NULL, published_at DESC, id DESC LIMIT ? OFFSET ?""",
            [*params, safe_limit, safe_offset],
        ).fetchall()]
        for item in items:
            for key, dest in (("discoveryContextsJson", "discoveryContexts"), ("qualityFlagsJson", "qualityFlags")):
                try: item[dest] = json.loads(item.pop(key) or "[]")
                except (TypeError, ValueError): item[dest] = []
        return {"items": items, "total": int(total), "limit": safe_limit, "offset": safe_offset}

    def hotel_review_history(self, hotel_key: str, review_id: int) -> list[dict]:
        rows = self.conn.execute(
            """SELECT v.run_id AS runId,v.captured_at AS capturedAt,v.snapshot_json AS snapshotJson
               FROM hotel_review_versions v JOIN hotel_reviews r ON r.id=v.review_id
               WHERE r.hotel_key=? AND r.id=? ORDER BY v.captured_at DESC,v.id DESC""",
            (hotel_key, review_id),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try: item["snapshot"] = json.loads(item.pop("snapshotJson"))
            except (TypeError, ValueError): item["snapshot"] = {}
            result.append(item)
        return result

    def upsert_hotel_source_link(self, hotel_key: str, source: str, url: str, *, external_id: str | None = None,
                                 external_name: str | None = None, verified: bool = False) -> dict:
        if source not in {"google_maps", "google_hotels", "booking"}:
            raise ValueError("Fuente de hotel no admitida.")
        if self.get_hotel_inventory(hotel_key) is None:
            raise ValueError("Hotel no encontrado.")
        now = _now()
        with self.lock:
            self.conn.execute(
                """INSERT INTO hotel_source_links(hotel_key,source,external_id,url,external_name,verified,updated_at)
                   VALUES (?,?,?,?,?,?,?) ON CONFLICT(hotel_key,source) DO UPDATE SET external_id=excluded.external_id,
                   url=excluded.url,external_name=excluded.external_name,verified=excluded.verified,updated_at=excluded.updated_at""",
                (hotel_key, source, external_id, url, external_name, int(verified), now),
            )
            self.conn.commit()
        return {"hotelKey": hotel_key, "source": source, "externalId": external_id, "url": url,
                "externalName": external_name, "verified": bool(verified), "updatedAt": now}

    def select_hotel_attribute_observation(self, hotel_key: str, attribute: str,
                                           observation_id: int) -> dict:
        with self.lock:
            row = self.conn.execute(
                """SELECT id,value_json,source,observed_at FROM hotel_attribute_observations
                   WHERE id=? AND hotel_key=? AND attribute=?""",
                (observation_id, hotel_key, attribute),
            ).fetchone()
            if row is None:
                raise ValueError("La observación no pertenece a este hotel y atributo.")
            self.conn.execute(
                "UPDATE hotel_attribute_observations SET selected=0 WHERE hotel_key=? AND attribute=?",
                (hotel_key, attribute),
            )
            self.conn.execute(
                "UPDATE hotel_attribute_observations SET selected=1 WHERE id=?", (observation_id,)
            )
            self.conn.commit()
        try:
            value = json.loads(row["value_json"])
        except (TypeError, ValueError):
            value = row["value_json"]
        return {"id": observation_id, "attribute": attribute, "value": value,
                "source": row["source"], "observedAt": row["observed_at"], "selected": True}

    def create_hotel_review_run(self, hotel_key: str, source: str, *, status: str = "queued", source_url: str | None = None,
                                max_reviews: int = 1000, budget_usd: float | None = None, run_id: str | None = None) -> str:
        run_id = run_id or uuid.uuid4().hex
        with self.lock:
            self.conn.execute(
                "INSERT INTO hotel_review_runs(id,hotel_key,source,status,source_url,max_reviews,budget_usd,started_at) VALUES (?,?,?,?,?,?,?,?)",
                (run_id, hotel_key, source, status, source_url, max_reviews, budget_usd, _now()),
            )
            self.conn.commit()
        return run_id

    def update_hotel_review_run(self, run_id: str, *, status: str | None = None, rows_seen: int | None = None,
                                rows_inserted: int | None = None, rows_updated: int | None = None,
                                estimated_spend_usd: float | None = None, actual_spend_usd: float | None = None,
                                cursor: dict | None = None, coverage: dict | None = None, error: str | None = None,
                                complete: bool = False) -> None:
        assignments, values = [], []
        for field, value in (("status", status), ("rows_seen", rows_seen), ("rows_inserted", rows_inserted),
                             ("rows_updated", rows_updated), ("estimated_spend_usd", estimated_spend_usd),
                             ("actual_spend_usd", actual_spend_usd)):
            if value is not None:
                assignments.append(f"{field}=?"); values.append(value)
        if cursor is not None:
            assignments.append("cursor_json=?"); values.append(json.dumps(cursor, ensure_ascii=False))
        if coverage is not None:
            assignments.append("coverage_json=?"); values.append(json.dumps(coverage, ensure_ascii=False))
        if error is not None:
            assignments.append("error=?"); values.append(error[:1000])
        if complete:
            assignments.append("completed_at=?"); values.append(_now())
        if not assignments: return
        values.append(run_id)
        with self.lock:
            self.conn.execute(f"UPDATE hotel_review_runs SET {', '.join(assignments)} WHERE id=?", values)
            self.conn.commit()

    @staticmethod
    def _hotel_review_version_payload(row: dict) -> dict:
        fields = ("author", "title", "rating", "rating_scale", "positive_text", "negative_text",
                  "review_original", "review_es", "language_original", "language_confidence",
                  "translation_method", "published_at", "date_precision", "relative_published_at")
        return {key: row.get(key) for key in fields}

    def _record_hotel_review_version(self, review_id: int, run_id: str | None, row: dict, captured_at: str) -> None:
        payload = self._hotel_review_version_payload(row)
        content_hash = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        self.conn.execute(
            "INSERT OR IGNORE INTO hotel_review_versions(review_id,run_id,captured_at,content_hash,snapshot_json) VALUES (?,?,?,?,?)",
            (review_id, run_id, captured_at or _now(), content_hash, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
        )

    def upsert_hotel_reviews(self, hotel_key: str, source: str, run_id: str | None, reviews: list[dict]) -> dict:
        inserted = updated = 0
        now = _now()
        with self.lock:
            for row in reviews:
                source_id = str(row.get("sourceReviewId") or row.get("reviewId") or "").strip() or None
                content = row.get("reviewOriginal") or row.get("text") or ""
                relative_date = row.get("relativePublishedAt") or ""
                fingerprint_input = source_id or "|".join((row.get("author") or row.get("authorName") or "",
                                                           str(row.get("rating") or ""), content,
                                                           row.get("title") or "", relative_date))
                fingerprint = hashlib.sha256(f"{source}\0{hotel_key}\0{fingerprint_input}".encode("utf-8")).hexdigest()
                published_at = row.get("publishedAt") or row.get("published_at")
                date_precision = row.get("datePrecision") or ("exact" if published_at else ("relative" if relative_date else None))
                contexts = row.get("discoveryContexts") or row.get("contexts") or []
                flags = row.get("qualityFlags") or ([] if source_id else ["provisional_identity"])
                existing = self.conn.execute(
                    "SELECT * FROM hotel_reviews WHERE hotel_key=? AND source=? AND review_fingerprint=?",
                    (hotel_key, source, fingerprint),
                ).fetchone()
                if existing:
                    try: old_contexts = json.loads(existing["discovery_contexts_json"] or "[]")
                    except (TypeError, ValueError): old_contexts = []
                    try: old_flags = json.loads(existing["quality_flags_json"] or "[]")
                    except (TypeError, ValueError): old_flags = []
                    merged_contexts = []
                    context_keys = set()
                    for context in [*old_contexts, *contexts]:
                        context_key = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                        if context_key not in context_keys:
                            context_keys.add(context_key)
                            merged_contexts.append(context)
                    merged_flags = list(dict.fromkeys([*old_flags, *flags]))
                    current = dict(existing)
                    incoming = dict(current)
                    updates = {
                        "author": row.get("author") or row.get("authorName"), "title": row.get("title"),
                        "rating": _safe_float(row.get("rating")), "positive_text": row.get("positiveText"),
                        "negative_text": row.get("negativeText"), "review_original": row.get("reviewOriginal") or row.get("text"),
                        "review_es": row.get("reviewEs"), "language_original": row.get("languageOriginal") or row.get("language"),
                        "language_confidence": _safe_float(row.get("languageConfidence")), "translation_method": row.get("translationMethod"),
                        "published_at": published_at, "date_precision": date_precision,
                        "relative_published_at": relative_date or None,
                    }
                    incoming.update({key: value for key, value in updates.items() if value is not None})
                    content_changed = self._hotel_review_version_payload(current) != self._hotel_review_version_payload(incoming)
                    if content_changed:
                        self._record_hotel_review_version(existing["id"], existing["run_id"], current, existing["last_seen_at"])
                        self._record_hotel_review_version(existing["id"], run_id, incoming, now)
                    self.conn.execute(
                        """UPDATE hotel_reviews SET author=COALESCE(?,author),title=COALESCE(?,title),rating=COALESCE(?,rating),
                           positive_text=COALESCE(?,positive_text),negative_text=COALESCE(?,negative_text),
                           review_original=COALESCE(?,review_original),review_es=COALESCE(?,review_es),
                           language_original=COALESCE(?,language_original),language_confidence=COALESCE(?,language_confidence),
                           translation_method=COALESCE(?,translation_method),published_at=COALESCE(?,published_at),
                           date_precision=COALESCE(?,date_precision),relative_published_at=COALESCE(?,relative_published_at),
                           source_url=?,last_seen_at=?,last_run_id=COALESCE(?,last_run_id),
                           discovery_contexts_json=?,quality_flags_json=? WHERE id=?""",
                        (row.get("author") or row.get("authorName"), row.get("title"), _safe_float(row.get("rating")),
                         row.get("positiveText"), row.get("negativeText"), row.get("reviewOriginal") or row.get("text"),
                         row.get("reviewEs"), row.get("languageOriginal") or row.get("language"),
                         _safe_float(row.get("languageConfidence")), row.get("translationMethod"), published_at, date_precision,
                         relative_date or None, row.get("sourceUrl") or existing["source_url"], now, run_id,
                         json.dumps(merged_contexts, ensure_ascii=False), json.dumps(merged_flags, ensure_ascii=False), existing["id"]),
                    )
                    if (content_changed or merged_contexts != old_contexts or merged_flags != old_flags
                            or bool(row.get("sourceUrl") and row["sourceUrl"] != existing["source_url"])):
                        updated += 1
                    continue
                cursor = self.conn.execute(
                    """INSERT INTO hotel_reviews
                    (hotel_key,source,source_review_id,review_fingerprint,author,title,rating,rating_scale,positive_text,negative_text,
                     review_original,review_es,language_original,language_confidence,translation_method,published_at,date_precision,
                     relative_published_at,source_url,first_seen_at,last_seen_at,run_id,last_run_id,discovery_contexts_json,quality_flags_json)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (hotel_key, source, source_id, fingerprint, row.get("author") or row.get("authorName"), row.get("title"),
                     _safe_float(row.get("rating")), _safe_float(row.get("ratingScale")) or 5.0,
                     row.get("positiveText"), row.get("negativeText"), row.get("reviewOriginal") or row.get("text"),
                     row.get("reviewEs"), row.get("languageOriginal") or row.get("language"), _safe_float(row.get("languageConfidence")),
                     row.get("translationMethod"), published_at, date_precision or "unknown", relative_date or None,
                     row.get("sourceUrl") or "", now, now, run_id, run_id,
                     json.dumps(contexts, ensure_ascii=False), json.dumps(flags, ensure_ascii=False)),
                )
                self._record_hotel_review_version(cursor.lastrowid, run_id, {
                    "author": row.get("author") or row.get("authorName"), "title": row.get("title"),
                    "rating": _safe_float(row.get("rating")), "rating_scale": _safe_float(row.get("ratingScale")) or 5.0,
                    "positive_text": row.get("positiveText"), "negative_text": row.get("negativeText"),
                    "review_original": row.get("reviewOriginal") or row.get("text"), "review_es": row.get("reviewEs"),
                    "language_original": row.get("languageOriginal") or row.get("language"),
                    "language_confidence": _safe_float(row.get("languageConfidence")),
                    "translation_method": row.get("translationMethod"), "published_at": published_at,
                    "date_precision": date_precision or "unknown", "relative_published_at": relative_date or None,
                }, now)
                inserted += 1
            self.conn.commit()
        return {"inserted": inserted, "updated": updated, "seen": len(reviews)}

    def save_hotel_review_note(self, hotel_key: str, owner_key: str, body: str, review_id: int | None = None) -> dict:
        text = (body or "").strip()
        if not text or len(text) > 4000:
            raise ValueError("La nota debe tener entre 1 y 4.000 caracteres.")
        if self.get_hotel_inventory(hotel_key) is None:
            raise ValueError("Hotel no encontrado.")
        if review_id is not None and not self.conn.execute(
            "SELECT 1 FROM hotel_reviews WHERE id=? AND hotel_key=?", (review_id, hotel_key)
        ).fetchone():
            raise ValueError("La reseña vinculada no pertenece a este hotel.")
        now = _now()
        with self.lock:
            cursor = self.conn.execute(
                "INSERT INTO hotel_review_notes(hotel_key,review_id,owner_key,body,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (hotel_key, review_id, owner_key, text, now, now),
            )
            self.conn.commit()
        return {"id": cursor.lastrowid, "hotelKey": hotel_key, "reviewId": review_id, "ownerKey": owner_key,
                "body": text, "createdAt": now, "updatedAt": now}

    def delete_hotel_review_note(self, note_id: int, owner_key: str) -> bool:
        with self.lock:
            cursor = self.conn.execute("DELETE FROM hotel_review_notes WHERE id=? AND owner_key=?", (note_id, owner_key))
            self.conn.commit()
        return cursor.rowcount > 0

    def save_hotel_review_analysis(self, hotel_key: str, *, sources: list[str], model: str, prompt_version: str,
                                   analysis: dict, evidence: list[dict], input_hash: str, cost_usd: float | None,
                                   topics: list[dict] | None = None) -> int:
        now = _now()
        with self.lock:
            cursor = self.conn.execute(
                """INSERT INTO hotel_review_analyses(hotel_key,sources_json,model,prompt_version,analysis_json,evidence_json,input_hash,cost_usd,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (hotel_key, json.dumps(sources), model, prompt_version, json.dumps(analysis, ensure_ascii=False),
                 json.dumps(evidence, ensure_ascii=False), input_hash, cost_usd, now),
            )
            analyzed_ids = [int(item["reviewId"]) for item in evidence if item.get("reviewId")]
            if analyzed_ids:
                self.conn.executemany(
                    "DELETE FROM hotel_review_topics WHERE hotel_key=? AND review_id=?",
                    ((hotel_key, review_id) for review_id in analyzed_ids),
                )
            for item in topics or []:
                review_id = item.get("reviewId")
                topic = str(item.get("topic") or "").strip()[:100]
                sentiment = item.get("sentiment") if item.get("sentiment") in {"positive", "negative", "neutral"} else "neutral"
                if review_id and topic:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO hotel_review_topics(hotel_key,review_id,topic,sentiment,model,created_at) VALUES (?,?,?,?,?,?)",
                        (hotel_key, review_id, topic, sentiment, model, now),
                    )
            self.conn.commit()
        return int(cursor.lastrowid)

    def latest_hotel_review_analysis(self, hotel_key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM hotel_review_analyses WHERE hotel_key=? ORDER BY created_at DESC,id DESC LIMIT 1", (hotel_key,)
        ).fetchone()
        if not row: return None
        result = dict(row)
        for field, target in (("sources_json", "sources"), ("analysis_json", "analysis"), ("evidence_json", "evidence")):
            try: result[target] = json.loads(result.pop(field) or "[]")
            except (TypeError, ValueError): result[target] = [] if target != "analysis" else {}
        return result

    def hotel_review_analysis_candidates(self, hotel_key: str, sources: list[str],
                                         model: str, prompt_version: str,
                                         limit: int = 80) -> tuple[list[dict], int]:
        """Return new or changed review evidence, alternating available sources."""
        processed: dict[int, str] = {}
        for row in self.conn.execute(
            """SELECT evidence_json FROM hotel_review_analyses
               WHERE hotel_key=? AND model=? AND prompt_version=? ORDER BY id ASC""",
            (hotel_key, model, prompt_version),
        ):
            try:
                entries = json.loads(row["evidence_json"] or "[]")
            except (TypeError, ValueError):
                continue
            for item in entries if isinstance(entries, list) else []:
                if isinstance(item, dict) and item.get("reviewId") and item.get("contentHash"):
                    processed[int(item["reviewId"])] = str(item["contentHash"])
        by_source: dict[str, list[dict]] = {}
        pending = 0
        for source in sources:
            candidates: list[dict] = []
            for raw in self.conn.execute(
                """SELECT id,source,rating,rating_scale AS ratingScale,published_at AS publishedAt,
                          review_original AS reviewOriginal,review_es AS reviewEs,
                          positive_text AS positiveText,negative_text AS negativeText
                   FROM hotel_reviews WHERE hotel_key=? AND source=?
                   ORDER BY last_seen_at DESC,id DESC""",
                (hotel_key, source),
            ):
                row = dict(raw)
                text = row.get("reviewEs") or row.get("reviewOriginal") or ""
                if not any((text, row.get("positiveText"), row.get("negativeText"))):
                    continue
                evidence = {"reviewId": row["id"], "source": source, "rating": row["rating"],
                            "ratingScale": row["ratingScale"], "publishedAt": row["publishedAt"],
                            "text": text, "positiveText": row.get("positiveText") or "",
                            "negativeText": row.get("negativeText") or ""}
                content_hash = hashlib.sha256(json.dumps(
                    evidence, sort_keys=True, ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")).hexdigest()
                if processed.get(row["id"]) == content_hash:
                    continue
                evidence["contentHash"] = content_hash
                candidates.append(evidence)
            pending += len(candidates)
            by_source[source] = candidates
        selected: list[dict] = []
        while len(selected) < limit and any(by_source.values()):
            for source in sources:
                if by_source[source] and len(selected) < limit:
                    selected.append(by_source[source].pop(0))
        return selected, pending

    def list_targets(self) -> list[SearchTarget]:
        rows = self.conn.execute(
            """
            SELECT id, name, url, created_at AS createdAt, updated_at AS updatedAt
            FROM search_targets
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [SearchTarget(**dict(row)) for row in rows]

    def ensure_identity(self, owner_key: str, display_name: str | None = None, role: str = "analyst") -> dict:
        clean_key = (owner_key or "").strip()[:80]
        if not clean_key:
            raise ValueError("owner_key no puede estar vacío")
        clean_role = role if role in {"viewer", "analyst", "admin"} else "analyst"
        now = _now()
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO app_identities (owner_key, display_name, role, active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(owner_key) DO UPDATE SET display_name = excluded.display_name,
                  role = excluded.role, active = 1, updated_at = excluded.updated_at
                """,
                (clean_key, (display_name or clean_key)[:120], clean_role, now, now),
            )
            self.conn.commit()
        row = self.conn.execute("SELECT * FROM app_identities WHERE owner_key = ?", (clean_key,)).fetchone()
        item = dict(row)
        item["active"] = bool(item["active"])
        return item

    def grant_market_access(self, owner_key: str, target_id: int, permission: str = "viewer") -> bool:
        clean_permission = permission if permission in {"viewer", "analyst", "admin"} else "viewer"
        self.ensure_identity(owner_key)
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO market_access (owner_key, target_id, permission, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(owner_key, target_id) DO UPDATE SET permission = excluded.permission
                """,
                (owner_key, target_id, clean_permission, _now()),
            )
            self.conn.commit()
        return cursor.rowcount > 0

    def can_access_target(self, owner_key: str, target_id: int, minimum: str = "viewer") -> bool:
        rank = {"viewer": 1, "analyst": 2, "admin": 3}
        required = rank.get(minimum, 1)
        row = self.conn.execute(
            """
            SELECT ai.active, ma.permission
            FROM market_access ma
            JOIN app_identities ai ON ai.owner_key = ma.owner_key
            WHERE ma.owner_key = ? AND ma.target_id = ?
            """,
            (owner_key, target_id),
        ).fetchone()
        return bool(row and row["active"] and rank.get(row["permission"], 0) >= required)

    def list_targets_for_owner(self, owner_key: str) -> list[SearchTarget]:
        rows = self.conn.execute(
            """
            SELECT st.id, st.name, st.url, st.created_at AS createdAt, st.updated_at AS updatedAt
            FROM search_targets st
            JOIN market_access ma ON ma.target_id = st.id AND ma.owner_key = ?
            JOIN app_identities ai ON ai.owner_key = ma.owner_key AND ai.active = 1
            ORDER BY st.updated_at DESC
            """,
            (owner_key,),
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
        target = SearchTarget(**dict(row))
        self.ensure_identity("local-revenue", "Revenue local", "admin")
        self.grant_market_access("local-revenue", target.id, "admin")
        return target

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

    def create_snapshot(
        self,
        target_id: int,
        source_url: str,
        requested_limit: int,
        available_results: int,
        captured_rows: int,
        raw_hash: str,
        capture_profile: dict | None = None,
        capture_group_id: str | None = None,
    ) -> MarketSnapshot:
        scraped_at = _now()
        profile = dict(capture_profile or {})
        group_id = capture_group_id or profile.get("captureGroupId") or uuid.uuid4().hex
        profile["captureGroupId"] = group_id
        profile_json = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        profile_hash = hashlib.sha256(profile_json.encode("utf-8")).hexdigest()
        quality = profile.get("captureQuality") or {}
        capture_status = str(quality.get("status") or ("complete" if quality else "unknown"))
        expected_slices = max(1, int(profile.get("captureExpectedSlices") or 1))
        with self.lock:
            capture_run = self.conn.execute(
                "SELECT id FROM hotel_capture_runs WHERE group_id = ?", (group_id,)
            ).fetchone()
            if capture_run:
                capture_run_id = int(capture_run["id"])
                self.conn.execute(
                    "UPDATE hotel_capture_runs SET expected_slices = MAX(expected_slices, ?) WHERE id = ?",
                    (expected_slices, capture_run_id),
                )
            else:
                capture_cursor = self.conn.execute(
                    """
                    INSERT INTO hotel_capture_runs (
                      captured_at, group_id, target_id, profile_json, status,
                      expected_slices, completed_slices
                    ) VALUES (?, ?, ?, ?, 'running', ?, 0)
                    """,
                    (scraped_at, group_id, target_id, profile_json, expected_slices),
                )
                capture_run_id = int(capture_cursor.lastrowid)
            cursor = self.conn.execute(
            """
            INSERT INTO market_snapshots (
              target_id, source_url, requested_limit, available_results, captured_rows,
              scraped_at, raw_hash, capture_run_id, capture_profile_json,
              capture_group_id, capture_status, capture_profile_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (target_id, source_url, requested_limit, available_results, captured_rows,
             scraped_at, raw_hash, capture_run_id, profile_json, group_id,
             capture_status, profile_hash),
            )
            self.conn.execute(
                """
                UPDATE hotel_capture_runs
                SET completed_slices = completed_slices + 1,
                    status = CASE
                      WHEN completed_slices + 1 < expected_slices THEN 'running'
                      WHEN ? IN ('partial', 'empty', 'unknown') THEN 'partial'
                      ELSE 'complete'
                    END
                WHERE id = ?
                """,
                (capture_status, capture_run_id),
            )
            if not getattr(self._local, 'capture_transaction', False):
                self.conn.commit()
        return MarketSnapshot(
            captureProfile=profile,
            id=int(cursor.lastrowid),
            targetId=target_id,
            sourceUrl=source_url,
            requestedLimit=requested_limit,
            availableResults=available_results,
            capturedRows=captured_rows,
            scrapedAt=scraped_at,
            captureGroupId=group_id,
            captureStatus=capture_status,
            captureProfileHash=profile_hash,
        )

    def persist_market_snapshot(self, *, rows: list[MarketHotelRow], **metadata) -> MarketSnapshot:
        """Publish a complete photo and its observations with one transaction."""
        with self.lock:
            self.conn.execute('BEGIN IMMEDIATE')
            self._local.capture_transaction = True
            try:
                snapshot = self.create_snapshot(**metadata)
                for row in rows:
                    location = self.get_location(row.hotelKey)
                    ready = location is not None and location['latitude'] is not None and location['longitude'] is not None
                    self.insert_market_hotel(snapshot.id, row, 'ready' if ready else 'location_pending')
                self.conn.commit()
                return snapshot
            except Exception:
                self.conn.rollback()
                raise
            finally:
                self._local.capture_transaction = False

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

    @staticmethod
    def _inventory_completeness(values: dict) -> float:
        """Score only the stable attributes that make a useful hotel card."""
        fields = (
            "description", "stars", "accommodation_type", "city", "address",
            "latitude", "longitude", "beach_distance", "main_distance",
            "photo_url", "review_score", "review_count",
        )
        present = sum(values.get(field) not in (None, "", []) for field in fields)
        return round(present / len(fields), 2)

    def get_hotel_inventory(self, hotel_key: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM hotel_inventory WHERE hotel_key = ?", (hotel_key,)
        ).fetchone()

    def upsert_hotel_inventory(self, row: MarketHotelRow) -> None:
        """Merge stable hotel facts without replacing known values with nulls.

        The search capture supplies these fields when Booking exposes them. A
        later capture can fill only the gaps; price and availability never live
        here and therefore cannot make the inventory stale.
        """
        now = _now()
        incoming = {
            "hotel_key": row.hotelKey,
            "hotel_id": row.hotelId,
            "hotel_name": row.hotelName,
            "detail_url": row.detailUrl,
            "description": row.description,
            "stars": row.stars,
            "accommodation_type": row.accommodationType,
            "city": row.city,
            "country_code": row.countryCode,
            "display_location": row.displayLocation,
            "address": row.address,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "beach_distance": row.beachDistance,
            "main_distance": row.mainDistance,
            "nearby_beach_names": json.dumps(row.nearbyBeachNames or [], ensure_ascii=False),
            "top_location": int(row.topLocation) if row.topLocation is not None else None,
            "popular_district": row.popularDistrict,
            "photo_url": row.photoUrl,
            "review_score": row.rating,
            "review_count": row.reviewCount,
            "review_score_text": row.reviewScoreText,
            "no_prepayment": int(row.noPrepayment) if row.noPrepayment is not None else None,
            "ufi": row.ufi,
            "source": "booking_graphql",
        }
        with self.lock:
            existing_row = self.get_hotel_inventory(row.hotelKey)
            existing = dict(existing_row) if existing_row else {}
            merged = dict(existing)
            for key, value in incoming.items():
                if key in {"hotel_key", "source"}:
                    merged[key] = value
                elif value not in (None, "", "[]"):
                    merged[key] = value
            merged.setdefault("hotel_key", row.hotelKey)
            merged.setdefault("hotel_name", row.hotelName)
            merged.setdefault("detail_url", row.detailUrl)
            merged.setdefault("first_seen_at", now)
            merged["last_seen_at"] = now
            merged["updated_at"] = now
            merged["completeness"] = self._inventory_completeness(merged)
            columns = (
                "hotel_key", "hotel_id", "hotel_name", "detail_url", "description",
                "stars", "accommodation_type", "city", "country_code", "display_location",
                "address", "latitude", "longitude", "beach_distance", "main_distance",
                "nearby_beach_names", "top_location", "popular_district", "photo_url",
                "review_score", "review_count", "review_score_text", "no_prepayment", "ufi", "source",
                "first_seen_at", "last_seen_at", "updated_at", "completeness",
            )
            self.conn.execute(
                f"INSERT OR REPLACE INTO hotel_inventory ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                tuple(merged.get(column) for column in columns),
            )
            self.conn.commit()

    def insert_market_hotel(self, snapshot_id: int, row: MarketHotelRow, location_status: str) -> None:
        with self.lock:
            self.conn.execute(
            """
            INSERT INTO market_snapshot_hotels (
              snapshot_id, hotel_key, hotel_name, detail_url, room_type, rating, price, price_text, currency, pax,
              check_in, check_out, nights, price_per_night, price_per_person_night, position, location_status,
              board, review_count, free_cancellation,
              hotel_id, price_original, discount_pct, sold_out, observation_status, closed, units_left, accommodation_type,
              beach_distance, top_location, popular_district, children_free, third_party, occupancy_rate
            ) VALUES (
              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
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
                row.hotelId,
                row.priceOriginal,
                row.discountPct,
                int(row.soldOut) if row.soldOut is not None else None,
                row.observationStatus,
                int(row.closed) if row.closed is not None else None,
                row.unitsLeft,
                row.accommodationType,
                row.beachDistance,
                int(row.topLocation) if row.topLocation is not None else None,
                row.popularDistrict,
                int(row.childrenFree) if row.childrenFree is not None else None,
                int(row.thirdParty) if row.thirdParty is not None else None,
                row.occupancyRate,
            ),
            )
            snapshot = self.conn.execute(
                "SELECT target_id, capture_run_id FROM market_snapshots WHERE id = ?", (snapshot_id,)
            ).fetchone()
            if snapshot:
                flags = [location_status] if location_status else []
                self.conn.execute(
                    """
                    INSERT INTO hotel_price_observations (
                      capture_run_id, snapshot_id, hotel_key, target_id, price_per_night, data_quality_flags
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot["capture_run_id"], snapshot_id, row.hotelKey,
                        snapshot["target_id"], row.pricePerNight, json.dumps(flags),
                    ),
                )
            if not getattr(self._local, 'capture_transaction', False):
                self.conn.commit()

    def latest_snapshot(self, target_id: int) -> MarketSnapshot | None:
        row = self.conn.execute(
            """
            SELECT id, target_id AS targetId, source_url AS sourceUrl, capture_profile_json AS captureProfile,
                   capture_group_id AS captureGroupId, capture_status AS captureStatus,
                   capture_profile_hash AS captureProfileHash, requested_limit AS requestedLimit,
                   available_results AS availableResults, captured_rows AS capturedRows, scraped_at AS scrapedAt
            FROM market_snapshots
            WHERE target_id = ?
            ORDER BY scraped_at DESC, id DESC
            LIMIT 1
            """,
            (target_id,),
        ).fetchone()
        return MarketSnapshot(**dict(row)) if row else None

    def snapshot_by_id(self, target_id: int, snapshot_id: int) -> MarketSnapshot | None:
        """Return an explicitly selected photo only when it belongs to target."""
        row = self.conn.execute(
            """
            SELECT id, target_id AS targetId, source_url AS sourceUrl, capture_profile_json AS captureProfile,
                   capture_group_id AS captureGroupId, capture_status AS captureStatus,
                   capture_profile_hash AS captureProfileHash, requested_limit AS requestedLimit,
                   available_results AS availableResults, captured_rows AS capturedRows, scraped_at AS scrapedAt
            FROM market_snapshots
            WHERE target_id = ? AND id = ?
            """,
            (target_id, snapshot_id),
        ).fetchone()
        return MarketSnapshot(**dict(row)) if row else None

    def snapshot_history(self, target_id: int, limit: int = 20) -> list[MarketSnapshot]:
        rows = self.conn.execute(
            """
            SELECT id, target_id AS targetId, source_url AS sourceUrl, capture_profile_json AS captureProfile,
                   capture_group_id AS captureGroupId, capture_status AS captureStatus,
                   capture_profile_hash AS captureProfileHash, requested_limit AS requestedLimit,
                   available_results AS availableResults, captured_rows AS capturedRows, scraped_at AS scrapedAt
            FROM market_snapshots
            WHERE target_id = ?
            ORDER BY scraped_at DESC, id DESC
            LIMIT ?
            """,
            (target_id, limit),
        ).fetchall()
        return [MarketSnapshot(**dict(row)) for row in rows]

    def capture_group_snapshot_ids(self, target_id: int, snapshot_id: int) -> dict | None:
        """Resolve an anchor snapshot to its coherent extraction (``foto``).

        New captures carry a durable ``capture_group_id``. Older rows predate
        that field and were persisted once per weekly check-in; contiguous
        legacy snapshots less than two minutes apart are therefore exposed as
        one explicitly labelled inferred group. This is read-only: we do not
        rewrite historical evidence merely to make it easier to display.
        """
        snapshots = self.snapshot_history(target_id, limit=500)
        anchor_index = next((index for index, item in enumerate(snapshots) if item.id == snapshot_id), None)
        if anchor_index is None:
            return None
        anchor = snapshots[anchor_index]
        if anchor.captureGroupId:
            members = [item for item in snapshots if item.captureGroupId == anchor.captureGroupId]
            kind = "capture_group"
            group_id = anchor.captureGroupId
        else:
            chronological = list(reversed(snapshots))
            anchor_index = next(index for index, item in enumerate(chronological) if item.id == snapshot_id)
            members = [anchor]
            left = anchor_index - 1
            right = anchor_index + 1
            while left >= 0:
                current, next_item = chronological[left], chronological[left + 1]
                if datetime.fromisoformat(next_item.scrapedAt.replace("Z", "+00:00")) - datetime.fromisoformat(current.scrapedAt.replace("Z", "+00:00")) > timedelta(minutes=2):
                    break
                members.append(current)
                left -= 1
            while right < len(chronological):
                previous, current = chronological[right - 1], chronological[right]
                if datetime.fromisoformat(current.scrapedAt.replace("Z", "+00:00")) - datetime.fromisoformat(previous.scrapedAt.replace("Z", "+00:00")) > timedelta(minutes=2):
                    break
                members.append(current)
                right += 1
            members = sorted({item.id: item for item in members}.values(), key=lambda item: (item.scrapedAt, item.id))
            kind = "legacy_inferred_capture_group"
            group_id = f"legacy:{members[0].id}-{members[-1].id}"
        ordered = sorted(members, key=lambda item: (item.scrapedAt, item.id))
        return {
            "id": group_id,
            "kind": kind,
            "anchorSnapshotId": anchor.id,
            "snapshotIds": [item.id for item in ordered],
            "observedAt": ordered[-1].scrapedAt,
        }

    def capture_history(self, target_id: int, limit: int = 24) -> list[dict]:
        """Return extraction-level history, keeping legacy inference visible."""
        snapshots = self.snapshot_history(target_id, limit=500)
        groups: dict[str, dict] = {}
        for snapshot in snapshots:
            resolved = self.capture_group_snapshot_ids(target_id, snapshot.id)
            if not resolved or resolved["id"] in groups:
                continue
            rows = [row for member_id in resolved["snapshotIds"] for row in self.snapshot_rows(member_id)]
            comparable = [row for row in rows if row.price is not None and row.nights and row.nights > 0 and row.currency == "EUR"]
            groups[resolved["id"]] = {
                **resolved,
                "capturedRows": len(rows),
                "comparableRows": len(comparable),
                "checkIns": sorted({row.checkIn for row in rows if row.checkIn}),
            }
        return sorted(groups.values(), key=lambda item: item["observedAt"], reverse=True)[:limit]

    def snapshot_rows(self, snapshot_id: int) -> list[MarketHotelRow]:
        rows = self.conn.execute(
            """
            SELECT
              msh.id AS id,
              msh.snapshot_id AS snapshotId,
              msh.hotel_key AS hotelKey,
              COALESCE(msh.hotel_name, hi.hotel_name) AS hotelName,
              COALESCE(msh.detail_url, hi.detail_url) AS detailUrl,
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
              msh.hotel_id AS hotelId,
              msh.price_original AS priceOriginal,
              msh.discount_pct AS discountPct,
              msh.sold_out AS soldOut,
              msh.observation_status AS observationStatus,
              msh.closed AS closed,
              msh.units_left AS unitsLeft,
              msh.accommodation_type AS accommodationType,
              msh.beach_distance AS beachDistance,
              msh.top_location AS topLocation,
              msh.popular_district AS popularDistrict,
              msh.children_free AS childrenFree,
              msh.third_party AS thirdParty,
              msh.occupancy_rate AS occupancyRate,
              COALESCE(hl.latitude, hi.latitude) AS latitude,
              COALESCE(hl.longitude, hi.longitude) AS longitude,
              COALESCE(hl.address, hi.address) AS address,
              hi.description AS description,
              hi.stars AS stars,
              hi.city AS city,
              hi.country_code AS countryCode,
              hi.display_location AS displayLocation,
              hi.main_distance AS mainDistance,
              hi.nearby_beach_names AS nearbyBeachNames,
              hi.photo_url AS photoUrl,
              hi.review_score_text AS reviewScoreText,
              hi.no_prepayment AS noPrepayment,
              hi.completeness AS inventoryCompleteness,
              hi.updated_at AS inventoryUpdatedAt
            FROM market_snapshot_hotels msh
            LEFT JOIN hotel_locations hl ON hl.hotel_key = msh.hotel_key
            LEFT JOIN hotel_inventory hi ON hi.hotel_key = msh.hotel_key
            WHERE msh.snapshot_id = ?
            ORDER BY msh.position ASC
            """,
            (snapshot_id,),
        ).fetchall()
        result: list[MarketHotelRow] = []
        for row in rows:
            values = dict(row)
            try:
                values["nearbyBeachNames"] = json.loads(values.get("nearbyBeachNames") or "[]")
            except (TypeError, json.JSONDecodeError):
                values["nearbyBeachNames"] = []
            result.append(MarketHotelRow(**values))
        return result

    def comparable_snapshot(self, target_id: int, current_rows: list[MarketHotelRow], current_snapshot_id: int) -> dict:
        """Find the latest capture matching the current rate product.

        A hotel key alone is not enough for pickup: dates, occupancy, room,
        board, currency and cancellation conditions can all change the public
        price. Return matched pairs so callers cannot fall back to a key-only
        comparison.
        """
        current_comparable = [
            row for row in current_rows
            if row.price is not None and row.nights and row.nights > 0
        ]
        empty = {
            "snapshot": None,
            "rows": [],
            "matchedCurrentRows": [],
            "matchedPreviousRows": [],
            "coveragePct": 0,
        }
        if not current_comparable:
            return empty

        current_unique = unique_products(current_comparable)
        anchor = self.conn.execute("SELECT scraped_at, id, source_url, capture_profile_json FROM market_snapshots WHERE id = ? AND target_id = ?", (current_snapshot_id, target_id)).fetchone()
        if anchor is None:
            return empty
        anchor_profile = json.loads(anchor['capture_profile_json']) if anchor['capture_profile_json'] else profile_from_url(anchor['source_url'])
        history = self.snapshot_history(target_id, 120)
        for candidate in history:
            if (candidate.scrapedAt, candidate.id) >= (anchor["scraped_at"], anchor["id"]):
                continue
            other_profile = candidate.captureProfile or {}
            occupancy_fields = ('adults', 'children', 'rooms', 'childAges')
            if any(anchor_profile.get(key) != other_profile.get(key) for key in occupancy_fields):
                continue
            candidate_rows = self.snapshot_rows(candidate.id)
            candidate_by_signature = unique_products(candidate_rows)
            matched_current = [row for key, row in current_unique.items() if key in candidate_by_signature]
            coverage = len(matched_current) / len(current_comparable)
            if coverage < 0.70:
                continue
            matched_previous = [
                candidate_by_signature[_market_row_comparison_signature(row)]
                for row in matched_current
            ]
            return {
                "snapshot": candidate,
                "rows": candidate_rows,
                "matchedCurrentRows": matched_current,
                "matchedPreviousRows": matched_previous,
                "coveragePct": _round(coverage * 100),
            }
        return empty

    def insert_rate_detail_rows(self, target_id: int, rows: list[HotelRateDetailRow]) -> None:
        with self.lock:
            self.conn.executemany(
                """
                INSERT INTO hotel_rate_details (
                  target_id, hotel_key, hotel_name, hotel_pagename, room_type, max_occupancy,
                  price_original, price_final, currency, board, prepayment_text, program, cancellation_text, free_cancellation,
                  units_left, block_uid, sold_out, genius, breakfast_score, breakfast_type_id,
                  bed_comfort_score, bed_comfort_reviews, stars, check_in, check_out, adults,
                  children, rooms, captured_at, snapshot_id
                ) VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                [
                    (
                        target_id,
                        row.hotelKey,
                        row.hotelName,
                        row.hotelPagename,
                        row.roomType,
                        row.maxOccupancy,
                        row.priceOriginal,
                        row.priceFinal,
                        row.currency,
                        row.board,
                        row.prepaymentText,
                        row.program,
                        row.cancellationText,
                        int(row.freeCancellation) if row.freeCancellation is not None else None,
                        row.unitsLeft,
                        row.blockUid,
                        int(row.soldOut) if row.soldOut is not None else None,
                        int(row.genius) if row.genius is not None else None,
                        row.breakfastScore,
                        row.breakfastTypeId,
                        row.bedComfortScore,
                        row.bedComfortReviews,
                        row.stars,
                        row.checkIn,
                        row.checkOut,
                        row.adults,
                        row.children,
                        row.rooms,
                        row.capturedAt or _now(),
                        row.snapshotId,
                    )
                    for row in rows
                ],
            )
            self.conn.commit()

    def create_hotel_detail_tasks(self, batch_id: str, payload: dict, hotels: list[dict]) -> int:
        """Create one durable task per hotel for a detail capture batch."""
        with self.lock:
            self.conn.executemany(
                """
                INSERT INTO hotel_detail_capture_tasks (
                  batch_id, target_id, snapshot_id, hotel_key, hotel_name, detail_url,
                  check_in, check_out, adults, children, rooms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(batch_id, hotel_key) DO NOTHING
                """,
                [
                    (
                        batch_id, payload["targetId"], payload.get("snapshotId"),
                        hotel["hotelKey"], hotel.get("hotelName"), hotel["detailUrl"],
                        payload["checkIn"], payload["checkOut"], payload.get("adults", 2),
                        payload.get("children", 0), payload.get("rooms", 1),
                    )
                    for hotel in hotels
                ],
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT COUNT(*) AS total FROM hotel_detail_capture_tasks WHERE batch_id = ?", (batch_id,)
            ).fetchone()
        return int(row["total"])

    def list_hotel_detail_tasks(self, batch_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM hotel_detail_capture_tasks WHERE batch_id = ? ORDER BY id ASC", (batch_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def get_hotel_detail_batch_owner(self, batch_id: str) -> str | None:
        """Owner recorded on the batch's job payload. None if unknown (deny by default)."""
        rows = self.conn.execute(
            "SELECT payload FROM background_jobs WHERE kind = 'hotel_detail_capture'"
        ).fetchall()
        for row in rows:
            try:
                payload = json.loads(row["payload"] or "{}")
            except (TypeError, ValueError):
                continue
            if payload.get("batchId") == batch_id:
                owner = payload.get("ownerKey")
                return owner if owner else None
        return None

    def reset_hotel_detail_tasks(self, batch_id: str) -> None:
        """Make tasks left running by a crashed process eligible again."""
        with self.lock:
            self.conn.execute(
                "UPDATE hotel_detail_capture_tasks SET status = 'queued', error = NULL WHERE batch_id = ? AND status = 'running'",
                (batch_id,),
            )
            self.conn.commit()

    def update_hotel_detail_task(self, task_id: int, *, status: str, attempts: int | None = None,
                                 rows_captured: int | None = None, error: str | None = None) -> None:
        now = _now()
        with self.lock:
            self.conn.execute(
                """
                UPDATE hotel_detail_capture_tasks
                SET status = ?, attempts = COALESCE(?, attempts), rows_captured = COALESCE(?, rows_captured),
                    error = ?, started_at = CASE WHEN ? = 'running' THEN COALESCE(started_at, ?) ELSE started_at END,
                    completed_at = CASE WHEN ? IN ('succeeded', 'failed') THEN ? ELSE completed_at END
                WHERE id = ?
                """,
                (status, attempts, rows_captured, error, status, now, status, now, task_id),
            )
            self.conn.commit()

    def delete_rate_details_for_tasks(self, target_id: int, snapshot_id: int | None, hotel_keys: list[str]) -> None:
        """Replace a batch's rows on retry without duplicating the same photo."""
        if not hotel_keys:
            return
        placeholders = ", ".join("?" for _ in hotel_keys)
        with self.lock:
            if snapshot_id is None:
                self.conn.execute(
                    f"DELETE FROM hotel_rate_details WHERE target_id = ? AND snapshot_id IS NULL AND hotel_key IN ({placeholders})",
                    [target_id, *hotel_keys],
                )
            else:
                self.conn.execute(
                    f"DELETE FROM hotel_rate_details WHERE target_id = ? AND snapshot_id = ? AND hotel_key IN ({placeholders})",
                    [target_id, snapshot_id, *hotel_keys],
                )
            self.conn.commit()

    _RATE_DETAIL_COLUMNS = """
              id, snapshot_id AS snapshotId, target_id AS targetId, hotel_key AS hotelKey, hotel_name AS hotelName,
              hotel_pagename AS hotelPagename, room_type AS roomType, max_occupancy AS maxOccupancy,
              price_original AS priceOriginal, price_final AS priceFinal, currency,
               board, prepayment_text AS prepaymentText, program, cancellation_text AS cancellationText, free_cancellation AS freeCancellation,
              units_left AS unitsLeft, block_uid AS blockUid, sold_out AS soldOut, genius,
              breakfast_score AS breakfastScore, breakfast_type_id AS breakfastTypeId,
              bed_comfort_score AS bedComfortScore, bed_comfort_reviews AS bedComfortReviews,
              stars, check_in AS checkIn, check_out AS checkOut, adults, children, rooms,
              captured_at AS capturedAt
    """

    def rate_details_for_target(self, target_id: int, limit: int = 200, hotel_key: str | None = None) -> list[HotelRateDetailRow]:
        if hotel_key:
            rows = self.conn.execute(
                f"""
                SELECT {self._RATE_DETAIL_COLUMNS}
                FROM hotel_rate_details
                WHERE target_id = ? AND hotel_key = ?
                ORDER BY captured_at DESC, id DESC
                LIMIT ?
                """,
                (target_id, hotel_key, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                f"""
                SELECT {self._RATE_DETAIL_COLUMNS}
                FROM hotel_rate_details
                WHERE target_id = ?
                ORDER BY captured_at DESC, id DESC
                LIMIT ?
                """,
                (target_id, limit),
            ).fetchall()
        return [HotelRateDetailRow(**dict(row)) for row in rows]

    def latest_rate_details_for_target(self, target_id: int, limit: int = 1000) -> list[HotelRateDetailRow]:
        """Return all rates from each hotel's most recent detail capture.

        A target can contain several detail scrapes over time. The workbook
        should compare a coherent capture per hotel instead of interleaving
        historical rows into one current-looking table.
        """
        rows = self.conn.execute(
            f"""
            WITH latest AS (
              SELECT hotel_key, MAX(captured_at) AS captured_at
              FROM hotel_rate_details
              WHERE target_id = ?
              GROUP BY hotel_key
            )
            SELECT
              d.id, d.snapshot_id AS snapshotId, d.target_id AS targetId, d.hotel_key AS hotelKey,
              d.hotel_name AS hotelName, d.hotel_pagename AS hotelPagename,
              d.room_type AS roomType, d.max_occupancy AS maxOccupancy,
              d.price_original AS priceOriginal, d.price_final AS priceFinal,
               d.currency, d.board, d.prepayment_text AS prepaymentText, d.program, d.cancellation_text AS cancellationText,
              d.free_cancellation AS freeCancellation, d.units_left AS unitsLeft,
              d.block_uid AS blockUid, d.sold_out AS soldOut, d.genius,
              d.breakfast_score AS breakfastScore, d.breakfast_type_id AS breakfastTypeId,
              d.bed_comfort_score AS bedComfortScore,
              d.bed_comfort_reviews AS bedComfortReviews, d.stars,
              d.check_in AS checkIn, d.check_out AS checkOut, d.adults,
              d.children, d.rooms, d.captured_at AS capturedAt
            FROM hotel_rate_details d
            JOIN latest l
              ON l.hotel_key = d.hotel_key AND l.captured_at = d.captured_at
            WHERE d.target_id = ?
            ORDER BY d.captured_at DESC, d.hotel_name ASC, d.room_type ASC, d.id ASC
            LIMIT ?
            """,
            (target_id, target_id, limit),
        ).fetchall()
        return [HotelRateDetailRow(**dict(row)) for row in rows]

    def latest_rate_details_page_for_target(self, target_id: int, limit: int = 50, offset: int = 0) -> dict:
        """Return one page of the latest coherent detail captures.

        Keeping the latest-capture CTE in the database prevents the client
        from downloading every historical rate just to show one 50-row page.
        """
        count_row = self.conn.execute(
            """
            WITH latest AS (
              SELECT hotel_key, MAX(captured_at) AS captured_at
              FROM hotel_rate_details
              WHERE target_id = ?
              GROUP BY hotel_key
            )
            SELECT COUNT(*) AS total
            FROM hotel_rate_details d
            JOIN latest l
              ON l.hotel_key = d.hotel_key AND l.captured_at = d.captured_at
            WHERE d.target_id = ?
            """,
            (target_id, target_id),
        ).fetchone()
        page_columns = """
              d.id, d.snapshot_id AS snapshotId, d.target_id AS targetId, d.hotel_key AS hotelKey,
              d.hotel_name AS hotelName, d.hotel_pagename AS hotelPagename,
              d.room_type AS roomType, d.max_occupancy AS maxOccupancy,
              d.price_original AS priceOriginal, d.price_final AS priceFinal,
              d.currency, d.board, d.prepayment_text AS prepaymentText, d.program, d.cancellation_text AS cancellationText,
              d.free_cancellation AS freeCancellation, d.units_left AS unitsLeft,
              d.block_uid AS blockUid, d.sold_out AS soldOut, d.genius,
              d.breakfast_score AS breakfastScore, d.breakfast_type_id AS breakfastTypeId,
              d.bed_comfort_score AS bedComfortScore,
              d.bed_comfort_reviews AS bedComfortReviews, d.stars,
              d.check_in AS checkIn, d.check_out AS checkOut, d.adults,
              d.children, d.rooms, d.captured_at AS capturedAt
        """
        rows = self.conn.execute(
            f"""
            WITH latest AS (
              SELECT hotel_key, MAX(captured_at) AS captured_at
              FROM hotel_rate_details
              WHERE target_id = ?
              GROUP BY hotel_key
            )
            SELECT {page_columns}
            FROM hotel_rate_details d
            JOIN latest l
              ON l.hotel_key = d.hotel_key AND l.captured_at = d.captured_at
            WHERE d.target_id = ?
            ORDER BY d.captured_at DESC, d.hotel_name ASC, d.room_type ASC, d.id ASC
            LIMIT ? OFFSET ?
            """,
            (target_id, target_id, limit, offset),
        ).fetchall()
        return {
            "rows": [HotelRateDetailRow(**dict(row)) for row in rows],
            "total": int(count_row["total"] if count_row else 0),
            "limit": limit,
            "offset": offset,
        }

    def latest_rate_details_for_hotel(self, target_id: int, hotel_key: str) -> list[HotelRateDetailRow]:
        """Solo las tarifas de la captura de detalle MÁS RECIENTE para este
        hotel (no mezcla filas de capturas distintas en el tiempo), para
        mostrar un desglose de habitaciones coherente en la fila expandida
        de la tabla principal."""
        latest = self.conn.execute(
            "SELECT MAX(captured_at) AS latest FROM hotel_rate_details WHERE target_id = ? AND hotel_key = ?",
            (target_id, hotel_key),
        ).fetchone()
        if not latest or not latest["latest"]:
            return []
        rows = self.conn.execute(
            f"""
            SELECT {self._RATE_DETAIL_COLUMNS}
            FROM hotel_rate_details
            WHERE target_id = ? AND hotel_key = ? AND captured_at = ?
            ORDER BY id ASC
            """,
            (target_id, hotel_key, latest["latest"]),
        ).fetchall()
        return [HotelRateDetailRow(**dict(row)) for row in rows]

    def rate_detail_evidence(self, target_id: int, hotel_key: str, snapshot_id: int) -> dict:
        photo = self.photo_detail(snapshot_id)
        if photo is None or photo['snapshot']['targetId'] != target_id:
            raise ValueError('La foto no pertenece al mercado seleccionado.')
        products = [row for row in photo['rows'] if row.hotelKey == hotel_key]
        if not products:
            raise ValueError('El hotel no pertenece a la foto seleccionada.')
        linked = self.conn.execute(
            f"SELECT {self._RATE_DETAIL_COLUMNS} FROM hotel_rate_details WHERE snapshot_id = ? AND target_id = ? AND hotel_key = ? ORDER BY captured_at DESC, id DESC",
            (snapshot_id, target_id, hotel_key),
        ).fetchall()
        if linked:
            latest_at = linked[0]['capturedAt']
            result = [dict(row) for row in linked if row['capturedAt'] == latest_at]
            scope = 'linked_snapshot'
        else:
            # Legacy detail is independent evidence, never silently attached to a photo.
            result = [row.model_dump() for row in self.latest_rate_details_for_hotel(target_id, hotel_key)]
            scope = 'independent_latest_detail' if result else 'no_linked_detail'
        return {'rows': result, 'provenance': {'scope': scope, 'snapshotId': snapshot_id,
                'snapshotScrapedAt': photo['snapshot']['scrapedAt'],
                'detailCapturedAt': result[0]['capturedAt'] if result else None,
                'note': 'Detalle capturado por separado y vinculado a esta foto.' if scope == 'linked_snapshot' else 'Detalle independiente: no vinculado a esta foto. Su fecha de captura, estancia y ocupación pueden ser distintas; no acredita el desglose de la tarifa de la foto.' if result else 'No existe detalle vinculado a esta foto.'}}

    def hotel_row_history(self, target_id: int, limit_snapshots: int = 12) -> list[dict]:
        """Every hotel row across the most recent snapshots for a target, each
        tagged with its own capture date — unlike snapshot_rows()/photo_detail()
        which only look at a single snapshot. Powers the "Histórico" tab so
        weekly captures of the same zone can be compared side by side."""
        rows = self.conn.execute(
            """
            SELECT
              msh.id AS id,
              msh.snapshot_id AS snapshotId,
              ms.scraped_at AS scrapedAt,
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
              msh.hotel_id AS hotelId,
              msh.price_original AS priceOriginal,
              msh.discount_pct AS discountPct,
              msh.sold_out AS soldOut,
              msh.observation_status AS observationStatus,
              msh.closed AS closed,
              msh.units_left AS unitsLeft,
              msh.accommodation_type AS accommodationType,
              msh.beach_distance AS beachDistance,
              msh.top_location AS topLocation,
              msh.popular_district AS popularDistrict,
              msh.children_free AS childrenFree,
              msh.third_party AS thirdParty,
              msh.occupancy_rate AS occupancyRate,
              hi.stars AS stars,
              hi.city AS city,
              hi.description AS description,
              hi.beach_distance AS inventoryBeachDistance,
              hi.completeness AS inventoryCompleteness
            FROM market_snapshot_hotels msh
            JOIN market_snapshots ms ON ms.id = msh.snapshot_id
            LEFT JOIN hotel_inventory hi ON hi.hotel_key = msh.hotel_key
            WHERE ms.target_id = ?
              AND ms.id IN (
                SELECT id FROM market_snapshots
                WHERE target_id = ?
                ORDER BY scraped_at DESC, id DESC
                LIMIT ?
              )
            ORDER BY ms.scraped_at DESC, ms.id DESC, msh.position ASC
            """,
            (target_id, target_id, limit_snapshots),
        ).fetchall()
        return [dict(row) for row in rows]

    def hotel_price_history(self, hotel_key: str, target_id: int | None = None, limit: int = 24) -> list[dict]:
        """Price/rating trail for a hotel, oldest first.

        The optional target scope keeps dashboard analysis inside the active
        market. Omitting it is still useful for a cross-market investigation.
        """
        rows = self.conn.execute(
            """
            SELECT
              msh.hotel_key AS hotelKey,
              msh.snapshot_id AS snapshotId,
              ms.scraped_at AS scrapedAt,
              msh.price AS price,
              msh.price_per_night AS pricePerNight,
              msh.price_per_person_night AS pricePerPersonPerNight,
              msh.rating AS rating,
              msh.review_count AS reviewCount,
              msh.room_type AS roomType,
              msh.board AS board,
              msh.currency AS currency,
              msh.pax AS pax,
              msh.free_cancellation AS freeCancellation,
              msh.check_in AS checkIn,
              msh.check_out AS checkOut,
              msh.nights AS nights,
              hpo.data_quality_flags AS dataQualityFlags
            FROM market_snapshot_hotels msh
            JOIN market_snapshots ms ON ms.id = msh.snapshot_id
            LEFT JOIN hotel_price_observations hpo
              ON hpo.snapshot_id = msh.snapshot_id AND hpo.hotel_key = msh.hotel_key
            WHERE msh.hotel_key = ?
              AND (? IS NULL OR ms.target_id = ?)
            ORDER BY ms.scraped_at DESC, ms.id DESC
            LIMIT ?
            """,
            (hotel_key, target_id, target_id, limit),
        ).fetchall()
        history = []
        for row in reversed(rows):
            item = dict(row)
            item["dataQualityFlags"] = json.loads(item["dataQualityFlags"] or "[]")
            history.append(item)
        return history

    def photo_history(self, target_id: int, limit: int = 24) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT
              ms.id AS id,
              ms.target_id AS targetId,
              ms.scraped_at AS scrapedAt,
              ms.captured_rows AS capturedRows,
              ms.available_results AS availableResults,
              SUM(CASE WHEN msh.price IS NOT NULL AND (msh.currency IS NULL OR msh.currency != 'EUR') THEN 1 ELSE 0 END) AS invalidCurrencyRows,
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
                "currency": "EUR" if not row["invalidCurrencyRows"] else None,
                "invalidCurrencyRows": row["invalidCurrencyRows"],
                "id": row["id"],
                "targetId": row["targetId"],
                "scrapedAt": row["scrapedAt"],
                "capturedRows": row["capturedRows"],
                "availableResults": row["availableResults"],
                "avgPricePerNight": _round(row["avgPricePerNight"] or 0) if not row["invalidCurrencyRows"] else None,
                "avgPricePerPersonNight": _round(row["avgPricePerPersonNight"] or 0) if not row["invalidCurrencyRows"] else None,
                "avgPriceTotal": _round(row["avgPriceTotal"] or 0) if not row["invalidCurrencyRows"] else None,
                "minPricePerNight": _round(row["minPricePerNight"] or 0) if not row["invalidCurrencyRows"] else None,
                "maxPricePerNight": _round(row["maxPricePerNight"] or 0) if not row["invalidCurrencyRows"] else None,
                "pricedRows": int(row["pricedRows"] or 0),
                "comparableRows": int(row["comparableRows"] or 0),
            }
            for row in rows
        ]

    def photo_detail(self, snapshot_id: int) -> dict | None:
        snapshot = self.conn.execute(
            """
            SELECT id, target_id AS targetId, source_url AS sourceUrl, capture_profile_json AS captureProfile,
                   capture_group_id AS captureGroupId, capture_status AS captureStatus,
                   capture_profile_hash AS captureProfileHash, requested_limit AS requestedLimit,
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
        result = {
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

        valid_currency = all(row.currency == 'EUR' for row in rows if row.price is not None)
        result['summary']['currency'] = 'EUR' if valid_currency else None
        if not valid_currency:
            for field in ('avgPricePerNight', 'avgPricePerPersonNight', 'minPricePerNight', 'maxPricePerNight'):
                result['summary'][field] = None
        return result

    def market_heatmap(self, target_id: int, photos: int = 1) -> dict:
        photo_limit = max(1, min(photos, 24))
        photos_in_scope = self.snapshot_history(target_id, photo_limit)
        ids = [photo.id for photo in photos_in_scope]
        if ids:
            placeholders = ','.join('?' for _ in ids)
            invalid = self.conn.execute(f"SELECT 1 FROM market_snapshot_hotels WHERE snapshot_id IN ({placeholders}) AND price IS NOT NULL AND (currency IS NULL OR currency != 'EUR') LIMIT 1", ids).fetchone()
            if invalid:
                return {'photosUsed': len(ids), 'snapshotIds': ids, 'scope': 'currency_blocked', 'points': [], 'note': 'No se agregan monedas distintas o desconocidas en un mapa en EUR.', 'scale': {'minPricePerNight': None, 'maxPricePerNight': None}}
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
            "photosUsed": min(photo_limit, len(self.snapshot_history(target_id, photo_limit))),
            "scope": "snapshot" if photo_limit == 1 else "historical_aggregate",
            "snapshotIds": [s.id for s in self.snapshot_history(target_id, photo_limit)],
            "note": "Tarifa de la última foto" if photo_limit == 1 else "Media histórica; puede incluir estancias y productos diferentes",
            "points": points,
            "scale": {"minPricePerNight": _round(min_val), "maxPricePerNight": _round(max_val)},
        }

    def dashboard_metrics(self, target_id: int, snapshot_id: int | None = None) -> dict:
        latest = self.snapshot_by_id(target_id, snapshot_id) if snapshot_id is not None else self.latest_snapshot(target_id)
        if latest is None:
            return _empty_dashboard()

        rows = self.snapshot_rows(latest.id)
        if any(row.price is not None and row.currency != 'EUR' for row in rows):
            result = _empty_dashboard()
            result['latestSnapshot'] = latest.model_dump()
            result['market'] = {key: None for key in result['market']}
            result['currencyPolicy'] = {'status': 'blocked', 'currency': 'EUR', 'reason': 'La foto contiene tarifas en otra moneda o sin moneda. No se calcula un agregado en EUR ni se aplica conversión.'}
            result['dataQuality'].update(totalRows=len(rows), freshness=freshness(latest.scrapedAt),
                currencyWarnings=sorted({row.currency or 'desconocida' for row in rows if row.price is not None}),
                notes=[result['currencyPolicy']['reason']])
            return result
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

        comparison = self.comparable_snapshot(target_id, comparable, latest.id)
        previous = comparison["snapshot"]
        previous_rows = comparison["rows"]
        matched_current_rows = comparison["matchedCurrentRows"]
        matched_previous_rows = comparison["matchedPreviousRows"]
        comparison_coverage = comparison["coveragePct"]
        previous_priced = [r for r in matched_previous_rows if r.price is not None]
        previous_avg = sum(float(r.price) for r in previous_priced) / len(previous_priced) if previous_priced else 0
        previous_comp = matched_previous_rows
        previous_ppn_values = [float(r.pricePerNight or (r.price / r.nights)) for r in previous_comp if r.price is not None and r.nights]
        previous_avg_ppn = sum(previous_ppn_values) / len(previous_ppn_values) if previous_ppn_values else 0
        previous_pppn_values = [float(r.pricePerPersonPerNight if r.pricePerPersonPerNight is not None else r.price / r.nights / r.pax) for r in previous_comp]
        previous_avg_pppn = sum(previous_pppn_values) / len(previous_pppn_values) if previous_pppn_values else 0

        def paired_mean(field):
            values = [getattr(row, field) if getattr(row, field) is not None else (row.price / row.nights if field == "pricePerNight" else row.price / row.nights / row.pax) for row in matched_current_rows]
            return sum(values) / len(values) if values else 0
        matched_avg = paired_mean("price")
        matched_avg_ppn = paired_mean("pricePerNight")
        matched_avg_pppn = paired_mean("pricePerPersonPerNight")
        previous_by_key = {
            product_signature(current): previous_row
            for current, previous_row in zip(matched_current_rows, matched_previous_rows)
        }
        changed = increases = drops = 0
        for row in comparable:
            prev = previous_by_key.get(product_signature(row))
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
            prev_row = previous_by_key.get(product_signature(row))
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
                    "gapVsMedianPct": _round((current_ppn / median(per_night) - 1) * 100) if per_night else None,
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
        ppn_change = _pct_change(matched_avg_ppn, previous_avg_ppn)
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
            avg_ppn, _pct_change(matched_avg, previous_avg), _pct_change(matched_avg_ppn, previous_avg_ppn),
            competitive, notes, rows, comparable, changed, increases, drops,
            fill_ratio, booking_pressure, new_entrants, disappeared, rating_price,
        )

        return {
            "latestSnapshot": latest.model_dump(),
            "cards": [
                {"label": "Precio medio", "value": _round(avg)},
                {"label": "Tarifa pública media/noche", "value": _round(avg_ppn)},
                {"label": "Precio minimo noche", "value": _round(min(per_night) if per_night else 0)},
                {"label": "Precio maximo noche", "value": _round(max(per_night) if per_night else 0)},
            ],
            "rateShoppingIndex": {
                "marketAvgAdr": _round(avg_ppn),
                "medianAdr": _round(median(per_night)) if per_night else None,
                "totalCompetitors": len(comparable),
                "topQuartileThreshold": _round(_percentile(per_night, 75)) if per_night else None,
                "bottomQuartileThreshold": _round(_percentile(per_night, 25)) if per_night else None,
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
                "medianPricePerNight": _round(median(per_night)) if per_night else None,
            },
            "movement": {
                "previousSnapshotId": previous.id if previous else None,
                "avgPriceChangePct": _pct_change(matched_avg, previous_avg),
                "avgPricePerNightChangePct": _pct_change(matched_avg_ppn, previous_avg_ppn),
                "avgPricePerPersonNightChangePct": _pct_change(matched_avg_pppn, previous_avg_pppn),
                "changedHotels": changed,
                "priceIncreases": increases,
                "priceDrops": drops,
                "matchedCoveragePct": comparison_coverage,
                "isComparable": bool(previous),
                "currentMean": _round(matched_avg_ppn) if previous else None,
                "previousMean": _round(previous_avg_ppn) if previous else None,
            },
            "comparison": {
                "status": "matched" if previous else "unmatched",
                "matchedCoveragePct": comparison_coverage,
                "matchedRows": len(matched_current_rows),
                "currentComparableRows": len(comparable),
                "criteria": "hotel, estancia, ocupación, habitación, régimen, moneda y cancelación",
                "limits": "Equivalencia de campos observados; impuestos, elegibilidad y plazos de pago no verificados.",
                "previousSnapshotId": previous.id if previous else None,
                "reason": None if previous else "No hay otra captura con la misma estancia y producto en al menos el 70% de la muestra.",
            },
            "dataQuality": {
                "freshness": freshness(latest.scrapedAt),
                "productComparableRows": len(unique_products(rows)),
                "productComparablePct": _round(len(unique_products(rows)) / len(rows) * 100) if rows else 0,
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
            SELECT ms.id AS snapshotId, ms.scraped_at AS scrapedAt,
              AVG(msh.price) AS avgPrice,
              AVG(COALESCE(msh.price_per_night, msh.price * 1.0 / NULLIF(msh.nights, 0))) AS avgPricePerNight,
              CASE WHEN COUNT(DISTINCT msh.currency) = 1 AND COUNT(msh.currency) = COUNT(*) THEN MIN(msh.currency) END AS currency,
              COUNT(msh.id) AS hotels
            FROM market_snapshots ms
            JOIN market_snapshot_hotels msh ON msh.snapshot_id = ms.id
            WHERE ms.target_id = ? AND msh.price IS NOT NULL
            GROUP BY ms.id
            ORDER BY ms.scraped_at DESC, ms.id DESC LIMIT 12
            """, (target_id,),
        ).fetchall()
        return [{"snapshotId": row["snapshotId"], "scrapedAt": row["scrapedAt"],
                 "avgPrice": _round(row["avgPrice"]) if row["currency"] else None,
                 "avgPricePerNight": _round(row["avgPricePerNight"]) if row["currency"] and row["avgPricePerNight"] is not None else None,
                 "currency": row["currency"], "hotels": row["hotels"]} for row in reversed(rows)]

    # ------------------------------------------------------------------
    # Pickup / Pace Analysis
    # ------------------------------------------------------------------

    def pickup_analysis(self, target_id: int, hotel_key: str | None = None, check_in: str | None = None, limit: int = 50) -> list[dict]:
        """Compare the same hotel and rate product across consecutive snapshots."""
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
              msh.snapshot_id AS snapshotId,
              msh.hotel_name AS hotelName,
              msh.check_in AS checkIn,
              msh.check_out AS checkOut,
              ms.scraped_at AS observedAt,
              msh.price AS price,
              msh.nights AS nights,
              msh.pax AS pax,
              msh.room_type AS roomType,
              msh.board AS board,
              msh.currency AS currency,
              msh.free_cancellation AS freeCancellation,
              COALESCE(msh.price_per_night,
                CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END
              ) AS pricePerNight
            FROM market_snapshot_hotels msh
            JOIN market_snapshots ms ON ms.id = msh.snapshot_id
            WHERE msh.snapshot_id IN ({placeholders})
              AND msh.price IS NOT NULL
              AND msh.nights > 0
              {where_extra}
            ORDER BY msh.hotel_key, msh.check_in, msh.check_out, msh.room_type, msh.board, ms.scraped_at DESC, ms.id DESC
            """,
            params,
        ).fetchall()

        grouped: dict[tuple, list[dict]] = defaultdict(list)
        by_snapshot = defaultdict(list)
        for row in rows:
            by_snapshot[row["snapshotId"]].append(dict(row))
        for observations in by_snapshot.values():
            for signature, item in unique_products(observations).items():
                grouped[signature].append(item)
        for observations in grouped.values():
            observations.sort(key=lambda item: (item["observedAt"], item["snapshotId"]), reverse=True)

        entries: list[dict] = []
        for signature, observations in grouped.items():
            h_key, ci = signature[0], signature[1]
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
                    ).model_dump() | {
                        "snapshotId": current["snapshotId"], "previousSnapshotId": prev["snapshotId"],
                        "checkOut": current["checkOut"], "nights": current["nights"], "pax": current["pax"],
                        "roomType": current["roomType"], "board": current["board"],
                        "currency": current["currency"], "freeCancellation": current["freeCancellation"],
                        "metric": "observed_rate_change",
                    }
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
            WITH recent_snapshots AS (
              SELECT id, scraped_at
              FROM market_snapshots
              WHERE target_id = ?
              ORDER BY scraped_at DESC, id DESC
              LIMIT ?
            )
            SELECT
              CAST(julianday(msh.check_in) - julianday(date(ms.scraped_at)) AS INTEGER) AS daysUntilCheckIn,
              COALESCE(msh.price_per_night,
                CASE WHEN msh.price IS NOT NULL AND msh.nights > 0 THEN msh.price * 1.0 / msh.nights END
              ) AS ppn, msh.currency AS currency
            FROM market_snapshot_hotels msh
            JOIN recent_snapshots ms ON ms.id = msh.snapshot_id
            AND msh.price IS NOT NULL
              AND msh.nights > 0
              AND msh.check_in IS NOT NULL
              AND CAST(julianday(msh.check_in) - julianday(date(ms.scraped_at)) AS INTEGER) >= 0
            ORDER BY daysUntilCheckIn
            """,
            (target_id, max(1, min(120, int(limit_snapshots)))),
        ).fetchall()

        if not rows:
            return []

        grouped: dict[int, list[float]] = defaultdict(list)
        for row in rows:
            days = int(row["daysUntilCheckIn"])
            ppn = float(row["ppn"])
            grouped[(row["currency"], days)].append(ppn)

        points: list[dict] = []
        for currency, days in sorted(grouped.keys(), key=lambda key: (key[0] or "", key[1])):
            if not currency:
                continue
            values = grouped[(currency, days)]
            points.append(
                DemandCurvePoint(
                    daysUntilCheckIn=days,
                    avgAdr=_round(sum(values) / len(values)),
                    medianAdr=_round(median(values)),
                    minAdr=_round(min(values)),
                    maxAdr=_round(max(values)),
                    observations=len(values),
                ).model_dump() | {"currency": currency, "scope": "historical_aggregate"}
            )
        return points

    # ------------------------------------------------------------------
    # Competitive Stability
    # ------------------------------------------------------------------

    def competitive_stability(self, target_id: int, snapshots_count: int = 10) -> list[dict]:
        """Consistency of each current product across repeated, equivalent observations."""
        latest = self.latest_snapshot(target_id)
        if latest is None:
            return []
        current = unique_products(self.snapshot_rows(latest.id))
        history = self.hotel_row_history(target_id, limit_snapshots=snapshots_count)
        by_snapshot = defaultdict(list)
        for row in history:
            by_snapshot[row["snapshotId"]].append(row)
        series = defaultdict(list)
        for rows in by_snapshot.values():
            for key, row in unique_products(rows).items():
                if key in current:
                    series[key].append(row)
        entries = []
        for key, records in series.items():
            if len(records) < 2:
                continue
            values = [float(r["pricePerNight"] or r["price"] / r["nights"]) for r in records]
            avg = sum(values) / len(values)
            sd = stdev(values)
            row = current[key]
            entries.append({
                "hotelKey": row.hotelKey, "hotelName": row.hotelName,
                "avgPricePerNight": _round(avg), "stddevPricePerNight": _round(sd),
                "consistencyScore": _round(max(0, 100 - sd / avg * 100)),
                "positioningLabel": "Mismo producto observado", "avgGapVsMarketPct": None,
                "observations": len(values), "snapshotIds": [r["snapshotId"] for r in records],
                "checkIn": row.checkIn, "checkOut": row.checkOut, "roomType": row.roomType,
                "board": row.board, "currency": row.currency, "pax": row.pax,
                "freeCancellation": row.freeCancellation,
            })
        return sorted(entries, key=lambda row: row["consistencyScore"])

    # ------------------------------------------------------------------
    # Revenue Opportunities
    # ------------------------------------------------------------------

    def revenue_opportunities(self, target_id: int, air_data: dict | None = None) -> list[dict]:
        """Score date windows by demand signals, competitive gaps, and flight data."""
        latest = self.latest_snapshot(target_id)
        if latest is None:
            return []
        rows = self.snapshot_rows(latest.id)
        if any(row.price is not None and row.currency != 'EUR' for row in rows):
            return []
        comparable = [r for r in rows if r.price is not None and r.nights and r.nights > 0]
        if not comparable:
            return []

        per_night = [float(r.pricePerNight or (r.price / r.nights)) for r in comparable if r.price is not None and r.nights]
        avg_ppn = sum(per_night) / len(per_night) if per_night else 0

        # Previous snapshot for movement. Reuse the same strict product
        # matching rule as dashboard_metrics; key-only joins create false
        # opportunities when a weekly capture changes its stay window.
        baseline = self.comparable_snapshot(target_id, comparable, latest.id)
        previous = baseline["snapshot"]
        previous_rows = baseline["rows"]
        matched_current_rows = baseline["matchedCurrentRows"]
        matched_previous_rows = baseline["matchedPreviousRows"]
        previous_by_key = {
            product_signature(current): previous_row
            for current, previous_row in zip(matched_current_rows, matched_previous_rows)
        }
        previous_comp = matched_previous_rows
        prev_per_night = [float(r.pricePerNight or (r.price / r.nights)) for r in previous_comp if r.price is not None and r.nights]
        prev_avg_ppn = sum(prev_per_night) / len(prev_per_night) if prev_per_night else 0

        opportunities: list[dict] = []
        opp_id = 0

        # 1. Hotels below rising market trend
        matched_mean = sum(float(r.pricePerNight or r.price / r.nights) for r in matched_current_rows) / len(matched_current_rows) if matched_current_rows else 0
        ppn_change = _pct_change(matched_mean, prev_avg_ppn) if prev_avg_ppn else None
        if ppn_change and ppn_change > 3:
            for r in comparable:
                current_ppn = float(r.pricePerNight or (r.price / r.nights)) if r.price and r.nights else 0
                prev_r = previous_by_key.get(product_signature(r))
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
                                title="Revisar posicionamiento tarifario",
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
            prev_r = previous_by_key.get(product_signature(r))
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
                        message=f"{best_rated.hotelName} tiene rating {best_rated.rating} pero precio por debajo del premium. Revisar producto y condiciones antes de inferir potencial de precio.",
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
                            message=f"Vuelos desde {route.get('market', route.get('origin'))} a {flight_price} EUR (barato). Señal de acceso aéreo; no demuestra demanda hotelera.",
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
                            type="air_access",
                            severity="info",
                            title="Tarifa aérea elevada",
                            message=f"Vuelos desde {route.get('market', route.get('origin'))} caros ({flight_price} EUR). No demuestra compras realizadas ni disposición a pagar una tarifa hotelera mayor.",
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
                        type="data_quality",
                        severity="critical",
                        title="Cobertura de extracción limitada",
                        message=f"Solo se capturaron {latest.capturedRows} de {latest.availableResults} resultados ({_round(fill * 100)}%). No permite inferir ocupación ni demanda.",
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

    # ------------------------------------------------------------------
    # Background work queue
    # ------------------------------------------------------------------

    def enqueue_job(
        self,
        job_id: str,
        kind: str,
        payload: dict,
        max_attempts: int = 3,
        idempotency_key: str | None = None,
    ) -> dict:
        now = _now()
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO background_jobs (
                  id, kind, status, payload, progress, message, attempts, max_attempts, idempotency_key, created_at, updated_at
                ) VALUES (?, ?, 'queued', ?, 0, 'En cola', 0, ?, ?, ?, ?)
                """,
                (job_id, kind, json.dumps(payload), max_attempts, idempotency_key, now, now),
            )
            self.conn.commit()
        return self.get_job(job_id)  # type: ignore[return-value]

    def get_job_by_idempotency(self, kind: str, idempotency_key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM background_jobs WHERE kind = ? AND idempotency_key = ?",
            (kind, idempotency_key),
        ).fetchone()
        return _deserialize_job(dict(row)) if row else None

    def active_assistant_job(self, session_id: int, owner_key: str) -> dict | None:
        """Return the queued/running Copilot job for a session, if any."""
        rows = self.conn.execute(
            "SELECT * FROM background_jobs WHERE kind = 'assistant_analysis' "
            "AND status IN ('queued', 'running') ORDER BY created_at DESC"
        ).fetchall()
        for row in rows:
            job = _deserialize_job(dict(row))
            payload = job.get("payload") or {}
            if payload.get("sessionId") == session_id and payload.get("ownerKey") == owner_key:
                return job
        return None

    def get_job(self, job_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM background_jobs WHERE id = ?", (job_id,)).fetchone()
        return _deserialize_job(dict(row)) if row else None

    def claim_next_job(self, kinds: list[str]) -> dict | None:
        if not kinds:
            return None
        placeholders = ", ".join("?" for _ in kinds)
        with self.lock:
            row = self.conn.execute(
                f"SELECT id FROM background_jobs WHERE status = 'queued' AND kind IN ({placeholders}) ORDER BY created_at ASC LIMIT 1",
                kinds,
            ).fetchone()
            if not row:
                return None
            now = _now()
            changed = self.conn.execute(
                """
                UPDATE background_jobs
                SET status = 'running', attempts = attempts + 1, progress = CASE WHEN progress < 1 THEN 1 ELSE progress END,
                    message = 'En ejecución', started_at = COALESCE(started_at, ?), updated_at = ?
                WHERE id = ? AND status = 'queued'
                """,
                (now, now, row["id"]),
            ).rowcount
            self.conn.commit()
        return self.get_job(row["id"]) if changed else None

    def recover_stale_jobs(self, stale_after_seconds: int = 900) -> dict[str, int]:
        """Reencola trabajos sin progreso tras una caída del proceso.

        Se comprueba al arrancar y periódicamente. Los trabajos que ya
        consumieron sus intentos no se repiten para evitar capturas duplicadas.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=max(60, int(stale_after_seconds)))).isoformat()
        now = _now()
        with self.lock:
            stale_capture_jobs = self.conn.execute(
                """SELECT id,payload,attempts,max_attempts FROM background_jobs
                   WHERE kind='hotel_review_capture' AND status='running' AND updated_at < ?""",
                (cutoff,),
            ).fetchall()
            retry = self.conn.execute(
                """UPDATE background_jobs
                   SET status = 'queued', message = 'Recuperado tras reinicio', updated_at = ?, completed_at = NULL
                   WHERE status = 'running' AND updated_at < ? AND attempts < max_attempts""",
                (now, cutoff),
            ).rowcount
            failed = self.conn.execute(
                """UPDATE background_jobs
                   SET status = 'failed', error = COALESCE(error, 'Trabajo abandonado tras agotar sus intentos'),
                       message = 'Falló tras reinicio', updated_at = ?, completed_at = ?
                   WHERE status = 'running' AND updated_at < ? AND attempts >= max_attempts""",
                (now, now, cutoff),
            ).rowcount
            for job in stale_capture_jobs:
                try:
                    tasks = json.loads(job["payload"]).get("tasks", [])
                except (TypeError, ValueError, AttributeError):
                    continue
                requeued = job["attempts"] < job["max_attempts"]
                for task in tasks:
                    if not isinstance(task, dict) or not task.get("runId"):
                        continue
                    if requeued:
                        self.conn.execute(
                            """UPDATE hotel_review_runs SET status='queued', completed_at=NULL
                               WHERE id=? AND status IN ('queued','running')""",
                            (task["runId"],),
                        )
                    else:
                        self.conn.execute(
                            """UPDATE hotel_review_runs
                               SET status=CASE WHEN rows_seen > 0 THEN 'partial' ELSE 'error' END,
                                   error='Captura interrumpida; reinicia la fuente para continuar', completed_at=?
                               WHERE id=? AND status IN ('queued','running')""",
                            (now, task["runId"]),
                        )
            self.conn.commit()
        return {"requeued": int(retry), "failed": int(failed)}

    def update_job_progress(self, job_id: str, progress: int, message: str) -> None:
        with self.lock:
            self.conn.execute(
                "UPDATE background_jobs SET progress = ?, message = ?, updated_at = ? WHERE id = ? AND status = 'running'",
                (max(0, min(99, progress)), message[:300], _now(), job_id),
            )
            self.conn.commit()

    def is_job_cancel_requested(self, job_id: str) -> bool:
        row = self.conn.execute(
            "SELECT cancel_requested, status FROM background_jobs WHERE id = ?", (job_id,)
        ).fetchone()
        return bool(row and (row["cancel_requested"] or row["status"] == "cancelled"))

    def request_job_cancel(self, job_id: str) -> dict | None:
        """Request cooperative cancellation and cancel queued work immediately."""
        now = _now()
        with self.lock:
            row = self.conn.execute("SELECT status FROM background_jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            status = row["status"]
            if status == "queued":
                self.conn.execute(
                    "UPDATE background_jobs SET status = 'cancelled', cancel_requested = 1, message = 'Cancelado', completed_at = ?, updated_at = ? WHERE id = ?",
                    (now, now, job_id),
                )
            elif status == "running":
                self.conn.execute(
                    "UPDATE background_jobs SET cancel_requested = 1, message = 'Cancelación solicitada', updated_at = ? WHERE id = ?",
                    (now, job_id),
                )
            self.conn.commit()
        return self.get_job(job_id)

    def cancel_job(self, job_id: str, message: str = "Cancelado") -> None:
        now = _now()
        with self.lock:
            self.conn.execute(
                "UPDATE background_jobs SET status = 'cancelled', cancel_requested = 1, message = ?, completed_at = ?, updated_at = ? WHERE id = ?",
                (message[:300], now, now, job_id),
            )
            self.conn.commit()

    def complete_job(self, job_id: str, result: dict) -> None:
        now = _now()
        with self.lock:
            self.conn.execute(
                """
                UPDATE background_jobs
                SET status = 'succeeded', result = ?, progress = 100, message = 'Completado',
                    error = NULL, completed_at = ?, updated_at = ?
                WHERE id = ? AND cancel_requested = 0 AND status = 'running'
                """,
                (json.dumps(result), now, now, job_id),
            )
            self.conn.commit()

    def fail_job(self, job_id: str, error: str) -> None:
        job = self.get_job(job_id)
        if not job:
            return
        retry = job["attempts"] < job["maxAttempts"]
        now = _now()
        with self.lock:
            self.conn.execute(
                """
                UPDATE background_jobs
                SET status = ?, error = ?, message = ?, updated_at = ?, completed_at = CASE WHEN ? THEN NULL ELSE ? END
                WHERE id = ?
                """,
                (
                    "queued" if retry else "failed", error[:1000],
                    "Reintentando" if retry else "Falló", now, int(retry), now, job_id,
                ),
            )
            self.conn.commit()

    def create_air_capture_run(self, payload: dict, requested_routes: int, source: str = "serpapi") -> dict:
        """Create one auditable run for an explicit UI capture request."""
        run_id = self.create_air_run(source, requested_routes)
        profile = {
            "adults": payload.get("adults", 1),
            "children": payload.get("children", 0),
            "travelClass": payload.get("travelClass", "economy"),
            "currency": payload.get("currency", "EUR"),
            "pointOfSale": payload.get("pointOfSale", "ES"),
            "direct": bool(payload.get("direct", True)),
            "forceLive": bool(payload.get("forceLive", True)),
        }
        single_date = bool(payload.get("singleDate"))
        coverage = {
            "dailyDays": 1 if single_date else payload.get("dailyDays", 14),
            "weeklyUntilDays": 1 if single_date else payload.get("weeklyUntilDays", 90),
            "maxQueries": payload.get("maxQueries", 500),
            "mode": "single_date" if single_date else "gradual_horizon",
        }
        with self.lock:
            self.conn.execute(
                "UPDATE air_runs SET provider=?, profile_json=?, coverage_json=?, queries_requested=? WHERE id=?",
                (source, json.dumps(profile, ensure_ascii=False), json.dumps(coverage), requested_routes, run_id),
            )
            self.conn.commit()
        return {
            "id": run_id,
            "source": source,
            "requestedRoutes": requested_routes,
            "capturedRoutes": 0,
            "capturedFlights": 0,
            "tripType": payload.get("tripType", "one_way"),
            "direct": bool(payload.get("direct")),
            "provider": source,
            "status": "running",
            "queriesRequested": requested_routes,
            "profile": profile,
            "coverage": coverage,
        }

    def finish_air_run(self, run_id: int, routes_captured: int, flights_captured: int) -> None:
        with self.lock:
            self.conn.execute(
                "UPDATE air_runs SET routes_captured=?, flights_captured=?, queries_completed=?, status='completed' WHERE id=?",
                (routes_captured, flights_captured, routes_captured, run_id),
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
                  google_price_level, price_history, provider, observed_at, currency,
                  departure_at, arrival_at, departure_token, booking_token, segment_signature,
                  baggage_json, extensions_json, emissions_json
                ) VALUES (
                  ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
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
                    row.get("provider", "serpapi"), row.get("observed_at") or row.get("search_datetime"),
                    row.get("currency", "EUR"), row.get("departure_at"), row.get("arrival_at"),
                    row.get("departure_token"), row.get("booking_token"), row.get("segment_signature"),
                    json.dumps(row.get("baggage") or []), json.dumps(row.get("extensions") or []),
                    json.dumps(row.get("emissions") or {}),
                ),
            )
            self.conn.commit()

    def insert_air_route_snapshot(
        self,
        run_id: int,
        route_definition: dict,
        snapshot: dict,
        flights: list[dict],
        *,
        direct: bool,
        currency: str,
    ) -> dict:
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO air_route_snapshots (
                  run_id, route_key, area_id, area_name, country, origin, destination,
                  outbound_date, return_date, lowest_price, avg_price, num_options,
                  num_direct_options, num_airlines, airlines_detected, direct, currency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, snapshot["route_key"], route_definition.get("areaId"),
                    route_definition.get("areaName"), route_definition.get("country"),
                    snapshot["origin"], snapshot["destination"], snapshot.get("outbound_date"),
                    snapshot.get("return_date"), snapshot.get("lowest_price"), snapshot.get("avg_price"),
                    snapshot.get("num_options", 0), snapshot.get("num_direct_options", 0),
                    snapshot.get("num_airlines", 0), json.dumps(snapshot.get("airlines_detected") or []),
                    int(direct), currency,
                ),
            )
            route_snapshot_id = int(cursor.lastrowid)
            for flight in flights:
                self.insert_air_flight(run_id, flight)
                self.conn.execute(
                    """
                    INSERT INTO flight_price_observations (run_id, route_snapshot_id, itinerary_id, price, observed_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (run_id, route_snapshot_id, flight.get("itinerary_id"), flight.get("price"), _now()),
                )
            self.conn.commit()
        return {
            "id": route_snapshot_id, "routeKey": snapshot["route_key"],
            "lowestPrice": snapshot.get("lowest_price"), "avgPrice": snapshot.get("avg_price"),
            "numOptions": snapshot.get("num_options", 0), "numDirectOptions": snapshot.get("num_direct_options", 0),
        }

    def latest_air_flights(self) -> list[dict]:
        return self.list_air_flights()

    def latest_air_run(self, exclude_demo: bool = False) -> dict | None:
        query = "SELECT id, captured_at, source, provider, routes_requested, routes_captured, flights_captured, status, queries_requested, queries_completed, queries_failed, cache_hits FROM air_runs"
        if exclude_demo:
            query += " WHERE source != 'mock'"
        query += " ORDER BY captured_at DESC, id DESC LIMIT 1"
        row = self.conn.execute(query).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "capturedAt": row["captured_at"],
            "source": row["source"],
            "routesRequested": row["routes_requested"],
            "routesCaptured": row["routes_captured"],
            "flightsCaptured": row["flights_captured"],
        }

    def get_air_run(self, run_id: int) -> dict | None:
        row = self.conn.execute(
            """
            SELECT id, captured_at, source, provider, routes_requested, routes_captured, flights_captured, status, queries_requested, queries_completed, queries_failed, cache_hits, profile_json, coverage_json
            FROM air_runs WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"], "capturedAt": row["captured_at"], "source": row["source"], "provider": row["provider"],
            "routesRequested": row["routes_requested"], "routesCaptured": row["routes_captured"],
            "flightsCaptured": row["flights_captured"], "status": row["status"],
            "queriesRequested": row["queries_requested"], "queriesCompleted": row["queries_completed"],
            "queriesFailed": row["queries_failed"], "cacheHits": row["cache_hits"],
            "profile": _json_object(row["profile_json"]), "coverage": _json_object(row["coverage_json"]),
        }

    def list_air_runs(self, limit: int = 100, exclude_demo: bool = False) -> list[dict]:
        query = """
            SELECT ar.id, ar.captured_at, ar.source, ar.provider, ar.routes_requested, ar.routes_captured,
                   ar.flights_captured, ar.status, ar.queries_requested, ar.queries_completed,
                   ar.queries_failed, ar.cache_hits, ar.profile_json, ar.coverage_json,
                   COUNT(af.id) AS stored_flights
            FROM air_runs ar
            LEFT JOIN air_flights af ON af.run_id = ar.id
        """
        params: list[Any] = []
        if exclude_demo:
            query += " WHERE ar.source != 'mock'"
        query += " GROUP BY ar.id ORDER BY ar.captured_at DESC, ar.id DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [
            {
                "id": row["id"], "capturedAt": row["captured_at"], "source": row["source"], "provider": row["provider"],
                "routesRequested": row["routes_requested"], "routesCaptured": row["routes_captured"],
                "flightsCaptured": row["stored_flights"], "status": row["status"],
                "queriesRequested": row["queries_requested"], "queriesCompleted": row["queries_completed"],
                "queriesFailed": row["queries_failed"], "cacheHits": row["cache_hits"],
                "profile": _json_object(row["profile_json"]), "coverage": _json_object(row["coverage_json"]),
            }
            for row in rows
        ]

    def list_air_flights(self, run_id: int | None = None, exclude_demo: bool = False) -> list[dict]:
        if run_id is not None:
            rows = self.conn.execute(
                "SELECT * FROM air_flights WHERE run_id=? ORDER BY origin, destination, price ASC",
                (run_id,),
            ).fetchall()
        else:
            query = "SELECT id FROM air_runs"
            if exclude_demo:
                query += " WHERE source != 'mock'"
            query += " ORDER BY captured_at DESC LIMIT 1"
            latest_run = self.conn.execute(query).fetchone()
            if latest_run is None:
                return []
            rows = self.conn.execute(
                "SELECT * FROM air_flights WHERE run_id=? ORDER BY origin, destination, price ASC",
                (latest_run["id"],),
            ).fetchall()
        return [_deserialize_air_row(dict(row)) for row in rows]

    def list_air_flights_history(self, exclude_demo: bool = True) -> list[dict]:
        query = """
            SELECT af.*, ar.id AS capture_run_id, ar.captured_at AS capture_run_at
            FROM air_flights af
            JOIN air_runs ar ON ar.id = af.run_id
        """
        if exclude_demo:
            query += " WHERE ar.source != 'mock'"
        query += " ORDER BY ar.captured_at DESC, ar.id DESC, af.origin, af.destination, af.price ASC"
        rows = self.conn.execute(query).fetchall()
        return [_deserialize_air_row(dict(row)) for row in rows]

    def air_route_history(self, route_key: str, direct: bool | None = None, limit: int = 20, outbound_date: str | None = None) -> list[dict]:
        snapshot_rows = self.conn.execute(
            """
            SELECT ars.*, ar.captured_at AS capturedAt
            FROM air_route_snapshots ars
            JOIN air_runs ar ON ar.id = ars.run_id
            WHERE ars.route_key = ? AND (? IS NULL OR ars.direct = ?) AND (? IS NULL OR ars.outbound_date = ?)
            ORDER BY ar.captured_at DESC, ars.id DESC
            LIMIT ?
            """,
            (route_key, None if direct is None else int(direct), None if direct is None else int(direct), outbound_date, outbound_date, limit),
        ).fetchall()
        if snapshot_rows:
            return [
                {
                    "routeKey": row["route_key"], "lowestPrice": row["lowest_price"],
                    "avgPrice": row["avg_price"], "numOptions": row["num_options"],
                    "numDirectOptions": row["num_direct_options"], "capturedAt": row["capturedAt"],
                }
                for row in snapshot_rows
            ]
        parts = route_key.split("_", 1)
        if len(parts) != 2:
            return []
        origin, destination = parts
        rows = self.conn.execute(
            """
            SELECT
              af.run_id,
              ? || '_' || ? AS route_key,
              MIN(COALESCE(af.lowest_price, af.price)) AS lowest_price,
              ROUND(AVG(COALESCE(af.lowest_price, af.price)), 1) AS avg_price,
              COUNT(*) AS num_options,
              SUM(CASE WHEN COALESCE(af.stops, 0) = 0 THEN 1 ELSE 0 END) AS num_direct_options,
              ar.captured_at AS captured_at
            FROM air_flights af
            JOIN air_runs ar ON ar.id = af.run_id
            WHERE af.origin = ? AND af.destination = ?
              AND (? IS NULL OR CASE WHEN COALESCE(af.stops, 0) = 0 THEN 1 ELSE 0 END = ?)
              AND (? IS NULL OR af.outbound_date = ?)
            GROUP BY af.run_id, ar.captured_at
            ORDER BY ar.captured_at DESC, af.run_id DESC
            LIMIT ?
            """,
            (
                origin,
                destination,
                origin,
                destination,
                None if direct is None else int(direct),
                None if direct is None else int(direct),
                outbound_date,
                outbound_date,
                limit,
            ),
        ).fetchall()
        return [
            {
                "routeKey": row["route_key"],
                "lowestPrice": row["lowest_price"],
                "avgPrice": row["avg_price"],
                "numOptions": row["num_options"],
                "numDirectOptions": row["num_direct_options"] or 0,
                "capturedAt": row["captured_at"],
            }
            for row in rows
        ]

def _market_row_comparison_signature(row: MarketHotelRow):
    return product_signature(row)


def _pickup_row_comparison_signature(row: dict):
    return product_signature(row)


def _deserialize_air_row(row: dict) -> dict:
    for field in ("airlines", "flight_numbers", "aircraft_models", "travel_classes", "layover_airports", "price_history", "baggage_json", "extensions_json", "emissions_json"):
        val = row.get(field)
        parsed = json.loads(val) if isinstance(val, str) and val else []
        output = field.removesuffix("_json") if field.endswith("_json") else field
        row[output] = parsed
        if output != field:
            row.pop(field, None)
    if row.get("origin") and row.get("destination"):
        row["route_key"] = f"{row['origin']}_{row['destination']}"
    if row.get("stops") is not None:
        row["is_direct"] = int(row["stops"] or 0) == 0
    row["observed_at"] = row.get("observed_at") or row.get("search_datetime")
    row["price_observed"] = row.get("price")
    return row


def _deserialize_job(row: dict) -> dict:
    for field in ("payload", "result"):
        value = row.get(field)
        row[field] = json.loads(value) if isinstance(value, str) and value else None
    row["maxAttempts"] = row.pop("max_attempts")
    row["createdAt"] = row.pop("created_at")
    row["updatedAt"] = row.pop("updated_at")
    row["startedAt"] = row.pop("started_at")
    row["completedAt"] = row.pop("completed_at")
    row["cancelRequested"] = bool(row.pop("cancel_requested", 0))
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
        "movement": {"previousSnapshotId": None, "avgPriceChangePct": None, "avgPricePerNightChangePct": None, "avgPricePerPersonNightChangePct": None, "changedHotels": 0, "priceIncreases": 0, "priceDrops": 0, "matchedCoveragePct": 0, "isComparable": False},
        "comparison": {"status": "unmatched", "matchedCoveragePct": 0, "matchedRows": 0, "currentComparableRows": 0, "criteria": "hotel, estancia, ocupación, habitación, régimen, moneda y cancelación", "previousSnapshotId": None, "reason": "No hay capturas para comparar."},
        "dataQuality": {"totalRows": 0, "pricedRows": 0, "missingPriceRows": 0, "comparableRows": 0, "comparablePct": 0, "currencyWarnings": [], "notes": ["No hay capturas todavia para este mercado."]},
        "competitiveSet": [],
        "newEntrants": [],
        "disappearedHotels": [],
        "insights": [],
    }


def _pct_es(value: float | None) -> str:
    """Porcentaje para el texto de una señal: una cifra decimal con coma («131,9 %»)."""
    if value is None:
        return "—"
    return f"{abs(value):.1f}".replace(".", ",") + " %"


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
            title="Revisar subida competitiva",
            message=f"El ADR del mercado ha subido un {_pct_es(ppn_change)}. Revisa si tu hotel sigue la tendencia.",
            changePct=ppn_change,
        ))

    # --- Market cooling ---
    if drops >= 3 and ppn_change is not None and ppn_change < -3:
        insights.append(RevenueInsight(
            id="market-cooling", type="market_cooling", severity="warning",
            title="Bajadas de tarifa observadas",
            message=f"{drops} competidores bajaron precio a la vez. El ADR del set cayó un {_pct_es(ppn_change)}.",
            changePct=ppn_change,
        ))
    elif ppn_change is not None and abs(ppn_change) >= 5:
        insights.append(RevenueInsight(
            id="market-movement", type="market_movement",
            severity="critical" if abs(ppn_change) >= 12 else "warning",
            title="Mercado en subida" if ppn_change > 0 else "Mercado en bajada",
            message=f"El ADR competitivo {'subió' if ppn_change > 0 else 'bajó'} un {_pct_es(ppn_change)} frente a la lectura anterior.",
            changePct=ppn_change,
        ))

    # --- Demand surge (fill ratio) ---
    if fill_ratio is not None and fill_ratio < 65:
        insights.append(RevenueInsight(
            id="demand-surge", type="data_quality", severity="critical",
            title="Cobertura de extracción limitada",
            message=f"Ratio de captura bajo ({_pct_es(fill_ratio)}). Revisa el límite solicitado y los errores de extracción; no mide ocupación.",
            value=fill_ratio,
        ))

    # --- Price leader ---
    if competitive:
        leader = competitive[0]
        if leader.get("gapVsMarketPct") is not None and leader["gapVsMarketPct"] >= 15:
            insights.append(RevenueInsight(
                id="price-leader", type="price_leader", severity="info",
                title="Líder de precio identificado",
                message=f"{leader['hotelName']} está un {_pct_es(leader['gapVsMarketPct'])} por encima de la media del set.",
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
                message=f"{worst['hotelName']} ha bajado un {_pct_es(worst['priceChangePct'])}. Vigila tu posicionamiento.",
                hotelName=worst["hotelName"], value=worst["pricePerNight"],
                benchmark=_round(avg_ppn), changePct=worst["priceChangePct"],
            ))
        # --- Aggressive pricing ---
        aggressive = next((h for h in competitive if h.get("gapVsMarketPct") is not None and h["gapVsMarketPct"] <= -15), None)
        if aggressive:
            insights.append(RevenueInsight(
                id="aggressive-pricing", type="aggressive_pricing", severity="warning",
                title="Precio agresivo en el mercado",
                message=f"{aggressive['hotelName']} está un {_pct_es(aggressive['gapVsMarketPct'])} por debajo de la media del set.",
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
                    message=f"{best.hotelName} tiene nota {str(best.rating).replace('.', ',')} pero no cobra prima. Revisa producto y condiciones antes de inferir potencial de precio.",
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
            message=f"{len(disappeared)} hoteles ya no aparecen: {names}. Ausencia en los resultados; disponibilidad no verificada.",
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
            message=f"Solo el {_pct_es(comparable_pct)} de las filas tiene precio y noches válidas.",
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


def _json_object(value: str | None) -> dict | None:
    """Decode optional JSON metadata without making old rows unreadable."""
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_utc_optional(value: str | None) -> datetime | None:
    """Parse a persisted instant without allowing naive timestamps."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


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
