from __future__ import annotations

import asyncio
import hashlib
import os
import uuid
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .booking_parser import parse_booking_location, parse_booking_search_results
from .capture_profile import effective_search_url, profile_from_url
from .database import Database
from .decodo import DecodoClient
from .graphql_scraper import scrape_search_graphql
from .models import MarketHotelRow, ScrapeSearchPayload, ScrapeSearchResponse

MAX_HOTELS_PER_SCRAPE = 500
MAX_SEARCH_PAGES = 20
BOOKING_PAGE_SIZE = 25
MAX_LOCATION_ENRICHMENT_PER_SCRAPE = 120
# Max concurrent Decodo detail-page scrapes for geolocation enrichment.
DECODO_CONCURRENCY = max(1, int(os.getenv("DECODO_CONCURRENCY", "6")))


class MarketService:
    def __init__(self, db: Database, decodo: DecodoClient, scraper_backend: str = "graphql") -> None:
        self.db = db
        self.decodo = decodo
        self.scraper_backend = scraper_backend

    async def scrape_search(
        self,
        payload: ScrapeSearchPayload,
        capture_group_id: str | None = None,
        capture_expected_slices: int = 1,
    ) -> ScrapeSearchResponse:
        source_url = effective_search_url(str(payload.url), payload.profile)
        target = self._resolve_target(payload)
        limit = max(1, min(payload.limit or MAX_HOTELS_PER_SCRAPE, MAX_HOTELS_PER_SCRAPE))
        scraper_diagnostics = None

        if self.scraper_backend == "graphql":
            scrape_result = await scrape_search_graphql(source_url, limit)
            selected, raw_hash, available_results = scrape_result
            scraper_diagnostics = getattr(scrape_result, 'diagnostics', None)
            # Las coordenadas ya vienen en la respuesta GraphQL: sin petición
            # extra por hotel (a diferencia de Decodo, que las saca de la
            # ficha).
            self._persist_locations_from_rows(selected)
        else:
            # Sticky session: reuse the same proxy IP across this capture (pagination + geo) for
            # consistent pricing and fewer blocks (Decodo keeps the IP for up to 10 minutes).
            session_id = uuid.uuid4().hex[:16]
            rows, raw_hash = await self._collect_rows_with_pagination(source_url, limit, session_id)
            selected = rows[:limit]
            available_results = len(rows)
            await self._enrich_locations(selected, session_id)

        # Conservamos una señal explícita de cobertura junto a la foto. El
        # total anunciado por Booking puede ser mayor que el límite solicitado
        # (muestra intencionada) o puede haber menos filas de las esperadas por
        # una respuesta incompleta/parcial del proveedor.
        captured_rows = len(selected)
        expected_rows = min(available_results, limit) if available_results is not None and available_results >= 0 else None
        if expected_rows is None:
            quality_status = 'unknown'
            coverage_pct = None
        elif captured_rows == expected_rows:
            quality_status = 'sampled' if available_results > limit else 'complete'
            coverage_pct = 100.0
        elif captured_rows == 0 and expected_rows > 0:
            quality_status = 'empty'
            coverage_pct = 0.0
        else:
            quality_status = 'partial'
            coverage_pct = round(captured_rows / expected_rows * 100, 1) if expected_rows else None
        capture_quality = {
            'status': quality_status,
            'availableResults': available_results,
            'expectedRows': expected_rows,
            'capturedRows': captured_rows,
            'coveragePct': coverage_pct,
            'limitApplied': bool(available_results is not None and available_results > limit),
        }
        if scraper_diagnostics:
            capture_quality.update({
                'pagesRequested': scraper_diagnostics.get('pagesRequested'),
                'pagesReceived': scraper_diagnostics.get('pagesReceived'),
                'pagesFailed': scraper_diagnostics.get('pagesFailed', 0),
                'terminationReason': scraper_diagnostics.get('terminationReason'),
                'blockDetected': bool(scraper_diagnostics.get('blockDetected')),
            })

        # La ficha estable se guarda una vez y se completa sólo con campos
        # nuevos. Precio, disponibilidad y política de la tarifa permanecen
        # en la foto de mercado y nunca contaminan el inventario.
        for row in selected:
            self.db.upsert_hotel_inventory(row)

        snapshot = self.db.persist_market_snapshot(
            rows=selected,
            target_id=target.id,
            source_url=source_url,
            requested_limit=limit,
            available_results=available_results,
            captured_rows=captured_rows,
            raw_hash=raw_hash,
            capture_profile=profile_from_url(source_url, origin='explicit_profile' if payload.profile else 'effective_url') | {
                'scraperBackend': self.scraper_backend,
                'captureGroupId': capture_group_id,
                'captureExpectedSlices': max(1, int(capture_expected_slices)),
                'captureQuality': capture_quality,
                'captureDiagnostics': scraper_diagnostics,
            },
        )

        stored = self.db.snapshot_rows(snapshot.id)
        return ScrapeSearchResponse(target=target, snapshot=snapshot, rows=stored)

    def _persist_locations_from_rows(self, rows: list[MarketHotelRow]) -> None:
        """Vuelca a `hotel_locations` las coordenadas que ya vienen incluidas
        en la fila (backend GraphQL). `insert_market_hotel`/`snapshot_rows`
        leen la ubicación de esa tabla vía JOIN, no del campo de la fila."""
        for row in rows:
            if (row.latitude is not None and row.longitude is not None) or self.db.get_location(row.hotelKey) is None:
                self.db.upsert_location(row.hotelKey, row.detailUrl, row.latitude, row.longitude, row.address)

    async def _enrich_locations(self, rows: list[MarketHotelRow], session_id: str | None = None) -> None:
        """Resolve hotel coordinates with the cheapest source first.

        1. Already stored in the DB → reuse.
        2. Coordinates parsed straight from the search-results card → store, no extra request.
        3. Otherwise → scrape the detail page, but do it CONCURRENTLY (was one-by-one),
           capped at MAX_LOCATION_ENRICHMENT_PER_SCRAPE.
        """
        pending: list[MarketHotelRow] = []
        for row in rows:
            existing = self.db.get_location(row.hotelKey)
            if existing and existing["latitude"] is not None and existing["longitude"] is not None:
                continue
            if row.latitude is not None and row.longitude is not None:
                self.db.upsert_location(row.hotelKey, row.detailUrl, row.latitude, row.longitude, row.address)
                continue
            pending.append(row)

        pending = pending[:MAX_LOCATION_ENRICHMENT_PER_SCRAPE]
        if not pending:
            return

        semaphore = asyncio.Semaphore(DECODO_CONCURRENCY)

        async def enrich(row: MarketHotelRow) -> None:
            async with semaphore:
                try:
                    detail_html = await self.decodo.scrape_html(row.detailUrl, session_id=session_id)
                    parsed = parse_booking_location(detail_html)
                    if parsed["latitude"] is not None and parsed["longitude"] is not None:
                        self.db.upsert_location(
                            row.hotelKey,
                            row.detailUrl,
                            parsed["latitude"],
                            parsed["longitude"],
                            parsed["address"],
                        )
                except Exception as exc:  # noqa: BLE001 - scraping should continue with partial location
                    print(f"[market] Ubicacion pendiente para {row.hotelName}: {exc}")

        await asyncio.gather(*(enrich(row) for row in pending))

    async def _collect_rows_with_pagination(self, source_url: str, limit: int, session_id: str | None = None) -> tuple[list[MarketHotelRow], str]:
        all_rows: list[MarketHotelRow] = []
        seen_keys: set[str] = set()
        hash_accumulator = hashlib.sha256()
        offset = 0

        for page in range(MAX_SEARCH_PAGES):
            page_url = self._with_offset(source_url, offset) if page else source_url
            html = await self.decodo.scrape_html(page_url, session_id=session_id)
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
