"""Capture all room/rate rows for the current hotel snapshots.

This is intentionally a resumable, low-concurrency batch. Booking detail pages
are slower and more sensitive to blocking than search snapshots, so each batch
uses the existing 15-hotel hard cap and writes results before continuing.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import load_settings  # noqa: E402
from backend.app.database import Database  # noqa: E402
from backend.app.graphql_scraper import scrape_rate_details  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("capture-all-hotel-details")
BATCH_SIZE = 15


def main() -> None:
    db = Database(load_settings().sqlite_path)
    snapshots = db.conn.execute(
        "SELECT id, target_id FROM market_snapshots ORDER BY id ASC"
    ).fetchall()
    total_hotels = 0
    total_rows = 0

    for snapshot_index, snapshot in enumerate(snapshots, start=1):
        snapshot_rows = db.snapshot_rows(snapshot["id"])
        hotels: dict[str, dict] = {}
        for row in snapshot_rows:
            if not row.detailUrl:
                continue
            hotels.setdefault(
                row.hotelKey,
                {
                    "hotelKey": row.hotelKey,
                    "detailUrl": row.detailUrl,
                    "hotelName": row.hotelName,
                },
            )
        hotel_list = list(hotels.values())
        if not hotel_list:
            log.warning("snapshot=%s sin fichas con URL", snapshot["id"])
            continue

        check_in = snapshot_rows[0].checkIn
        check_out = snapshot_rows[0].checkOut
        if not check_in or not check_out:
            log.warning("snapshot=%s sin fechas; se omite", snapshot["id"])
            continue

        log.info(
            "snapshot=%s target=%s (%d/%d): %d hoteles %s -> %s",
            snapshot["id"], snapshot["target_id"], snapshot_index, len(snapshots),
            len(hotel_list), check_in, check_out,
        )
        for offset in range(0, len(hotel_list), BATCH_SIZE):
            batch = hotel_list[offset : offset + BATCH_SIZE]
            try:
                rows = asyncio.run(
                    scrape_rate_details(
                        snapshot["target_id"],
                        batch,
                        checkin=check_in,
                        checkout=check_out,
                        adults=2,
                        children=0,
                        rooms=1,
                        snapshot_id=snapshot["id"],
                    )
                )
                if rows:
                    db.insert_rate_detail_rows(snapshot["target_id"], rows)
                total_rows += len(rows)
                total_hotels += len(batch)
                log.info(
                    "snapshot=%s batch=%d-%d/%d hotels=%d detail_rows=%d total_rows=%d",
                    snapshot["id"], offset + 1, offset + len(batch), len(hotel_list),
                    len(batch), len(rows), total_rows,
                )
            except Exception:  # noqa: BLE001 - continue other hotels after a provider failure
                log.exception(
                    "snapshot=%s batch=%d-%d failed; continuing",
                    snapshot["id"], offset + 1, offset + len(batch),
                )

    log.info("completed hotels=%d detail_rows=%d", total_hotels, total_rows)


if __name__ == "__main__":
    main()
