from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .booking_parser import parse_booking_location, parse_booking_search_results
from .database import Database
from .decodo import DecodoClient
from .models import MarketHotelRow, ScrapeSearchPayload, ScrapeSearchResponse

MAX_HOTELS_PER_SCRAPE = 500
MAX_SEARCH_PAGES = 20
BOOKING_PAGE_SIZE = 25
MAX_LOCATION_ENRICHMENT_PER_SCRAPE = 120


class MarketService:
    def __init__(self, db: Database, decodo: DecodoClient) -> None:
        self.db = db
        self.decodo = decodo

    async def scrape_search(self, payload: ScrapeSearchPayload) -> ScrapeSearchResponse:
        source_url = str(payload.url)
        target = self._resolve_target(payload)
        limit = max(1, min(payload.limit or MAX_HOTELS_PER_SCRAPE, MAX_HOTELS_PER_SCRAPE))
        rows, raw_hash = await self._collect_rows_with_pagination(source_url, limit)
        selected = rows[:limit]

        snapshot = self.db.create_snapshot(
            target_id=target.id,
            source_url=source_url,
            requested_limit=limit,
            available_results=len(rows),
            captured_rows=len(selected),
            raw_hash=raw_hash,
        )

        for index, row in enumerate(selected):
            location = self.db.get_location(row.hotelKey)
            should_enrich_location = index < MAX_LOCATION_ENRICHMENT_PER_SCRAPE
            if should_enrich_location and (location is None or location["latitude"] is None or location["longitude"] is None):
                try:
                    detail_html = await self.decodo.scrape_html(row.detailUrl)
                    parsed = parse_booking_location(detail_html)
                    self.db.upsert_location(
                        row.hotelKey,
                        row.detailUrl,
                        parsed["latitude"],
                        parsed["longitude"],
                        parsed["address"],
                    )
                    location = self.db.get_location(row.hotelKey)
                except Exception as exc:  # noqa: BLE001 - scraping should continue with partial location
                    print(f"[market] Ubicacion pendiente para {row.hotelName}: {exc}")

            ready = location is not None and location["latitude"] is not None and location["longitude"] is not None
            self.db.insert_market_hotel(snapshot.id, row, "ready" if ready else "location_pending")

        stored = self.db.snapshot_rows(snapshot.id)
        return ScrapeSearchResponse(target=target, snapshot=snapshot, rows=stored)

    async def _collect_rows_with_pagination(self, source_url: str, limit: int) -> tuple[list[MarketHotelRow], str]:
        all_rows: list[MarketHotelRow] = []
        seen_keys: set[str] = set()
        hash_accumulator = hashlib.sha256()
        offset = 0

        for page in range(MAX_SEARCH_PAGES):
            page_url = self._with_offset(source_url, offset) if page else source_url
            html = await self.decodo.scrape_html(page_url)
            hash_accumulator.update(html.encode())

            parsed_rows = parse_booking_search_results(html, source_url)
            added = 0
            for row in parsed_rows:
                if row.hotelKey in seen_keys:
                    continue
                seen_keys.add(row.hotelKey)
                row.position = len(all_rows) + 1
                all_rows.append(row)
                added += 1
                if len(all_rows) >= limit:
                    break

            if len(all_rows) >= limit:
                break
            if not parsed_rows or added == 0 or len(parsed_rows) < BOOKING_PAGE_SIZE:
                break

            offset += BOOKING_PAGE_SIZE

        return all_rows, hash_accumulator.hexdigest()

    @staticmethod
    def _with_offset(source_url: str, offset: int) -> str:
        parts = urlsplit(source_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["offset"] = str(max(0, offset))
        new_query = urlencode(query, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    def latest(self, target_id: int) -> dict | None:
        snapshot = self.db.latest_snapshot(target_id)
        if not snapshot:
            return None
        return {"snapshot": snapshot, "rows": self.db.snapshot_rows(snapshot.id)}

    def _resolve_target(self, payload: ScrapeSearchPayload):
        source_url = str(payload.url)
        if payload.targetId:
            existing = self.db.get_target(payload.targetId)
            if not existing:
                return self.db.upsert_target(payload.targetName or "Mercado Booking", source_url)
            if existing.url == source_url and (not payload.targetName or payload.targetName == existing.name):
                return existing
            return self.db.update_target(existing.id, payload.targetName or existing.name, source_url)
        return self.db.upsert_target(payload.targetName or "Mercado Booking", source_url)
