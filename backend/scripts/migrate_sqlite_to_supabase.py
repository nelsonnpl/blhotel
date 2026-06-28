from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import load_settings  # noqa: E402
from backend.app.database import Database  # noqa: E402


TABLES = [
    "search_targets",
    "capture_runs",
    "hotel_locations",
    "market_snapshots",
    "market_snapshot_hotels",
    "hotel_price_observations",
    "air_capture_runs",
    "air_route_snapshots",
    "air_snapshot_flights",
    "flight_price_observations",
]

ID_TABLES = [
    "search_targets",
    "capture_runs",
    "market_snapshots",
    "market_snapshot_hotels",
    "hotel_price_observations",
    "air_capture_runs",
    "air_route_snapshots",
    "air_snapshot_flights",
    "flight_price_observations",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra datos locales SQLite a Supabase/PostgreSQL.")
    parser.add_argument("--force", action="store_true", help="Vacía las tablas destino antes de migrar.")
    args = parser.parse_args()

    settings = load_settings()
    if settings.database_provider != "postgres" or not settings.database_url:
        raise SystemExit("Configura DATABASE_PROVIDER=postgres y DATABASE_URL en .env antes de migrar.")

    source = Database(settings.sqlite_path, provider="sqlite")
    target = Database(database_url=settings.database_url, provider="postgres")

    if args.force:
        truncate_target(target)
    else:
        existing = target_counts(target)
        non_empty = {table: count for table, count in existing.items() if count}
        if non_empty:
            raise SystemExit(f"Supabase ya contiene datos: {non_empty}. Usa --force si quieres recargar desde cero.")

    for table in TABLES:
        copied = copy_table(source, target, table)
        print(f"{table}: {copied}")

    reset_sequences(target)
    target.conn.commit()
    print("Migración completada.")


def truncate_target(target: Database) -> None:
    joined = ", ".join(TABLES)
    target.conn.execute(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE")
    target.conn.commit()


def target_counts(target: Database) -> dict[str, int]:
    return {table: int(target.conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]) for table in TABLES}


def copy_table(source: Database, target: Database, table: str) -> int:
    source_columns = [row["name"] for row in source.conn.execute(f"PRAGMA table_info({table})")]
    target_columns = [
        row["column_name"]
        for row in target.conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ?
            ORDER BY ordinal_position
            """,
            (table,),
        )
    ]
    columns = [column for column in source_columns if column in target_columns]
    if not columns:
        return 0

    rows = source.conn.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY rowid").fetchall()
    if not rows:
        return 0

    column_sql = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
    for row in rows:
        target.conn.execute(sql, tuple(row[column] for column in columns))
    target.conn.commit()
    return len(rows)


def reset_sequences(target: Database) -> None:
    for table in ID_TABLES:
        target.conn.execute(
            """
            SELECT setval(
              pg_get_serial_sequence(?, 'id'),
              GREATEST(COALESCE((SELECT MAX(id) FROM {table}), 1), 1),
              true
            )
            """.format(table=table),
            (table,),
        )


if __name__ == "__main__":
    main()
