"""Public-interface Booking.com review capture.

This module reads visible page content only. It does not call undocumented site
endpoints, bypass a challenge, or claim complete history unless pagination
provided an explicit end signal.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
import re
import time
from typing import Any

from playwright.async_api import async_playwright


_BLOCK_MARKERS = (
    "captcha", "verify you are human", "unusual traffic", "robot check",
    "access denied", "too many requests",
)
_REVIEW_CARD_SELECTORS = '[data-testid="review-card"], .review_list_new_item_block'


def _number(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"\d+(?:[.,]\d+)?", str(value).replace(",", "."))
    try:
        number = float(match.group()) if match else None
        return number if number is not None and 0 <= number <= 10 else None
    except ValueError:
        return None


def _review_count(value: Any) -> int | None:
    if value is None:
        return None
    match = re.search(r"([\d][\d.,\s]*)\s*(?:reviews?|reseñas?|comentarios?|opiniones|bewertungen)", str(value), re.I)
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(1))
    try:
        return int(digits) if digits else None
    except ValueError:
        return None


def _exact_public_datetime(value: Any) -> str | None:
    """Keep an explicit ISO date/time from the page, never guess a locale date."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?", value):
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value


async def _read_page(page, source_url: str, hotel_name: str) -> dict:
    return await page.evaluate(
        """({sourceUrl, hotelName}) => {
          const all = (root, selectors) => {
            for (const selector of selectors) {
              const nodes = [...root.querySelectorAll(selector)];
              if (nodes.length) return nodes;
            }
            return [];
          };
          const text = (root, selectors) => {
            for (const selector of selectors) {
              const node = root.querySelector(selector);
              const value = node?.innerText?.trim();
              if (value) return value;
            }
            return '';
          };
          const cards = all(document, ['[data-testid="review-card"]', '.review_list_new_item_block']);
          const reviews = cards.map((card) => {
            const id = card.getAttribute('data-review-id') || card.id ||
              card.querySelector('[data-review-id]')?.getAttribute('data-review-id') || '';
            const author = text(card, ['[data-testid="reviewer-name"]', '[data-testid="review-avatar"] h4', '.reviewer_name', '[itemprop="author"]']);
            const title = text(card, ['[data-testid="review-title"]', '.c-review__title', '.review_item_header_content']);
            const scoreText = text(card, ['[data-testid="review-score"]', '.review-score-badge', '.review-score-badge__score']);
            const positiveText = text(card, ['[data-testid="review-positive-text"]', '.review_pos', '.c-review__body--positive']);
            const negativeText = text(card, ['[data-testid="review-negative-text"]', '.review_neg', '.c-review__body--negative']);
            const dateText = text(card, ['[data-testid="review-date"]', '.review_item_date', 'time']);
            const dateTime = card.querySelector('time[datetime]')?.getAttribute('datetime') || '';
            return { id, author, title, rating: Number((scoreText.match(/[0-9]+(?:[.,][0-9]+)?/) || [])[0]?.replace(',', '.')) || null,
                     positiveText, negativeText, dateText, dateTime, sourceUrl };
          }).filter((row) => row.author || row.title || row.positiveText || row.negativeText || row.rating != null);
          const bodyText = document.body?.innerText || '';
          const scoreText = text(document, ['[data-testid="review-score-component"]', '[data-testid="review-score-right-component"]', '.js-hotel-review-score', '.review-score-badge__score']);
          const countText = text(document, ['[data-testid="review-score-component"]', '[data-testid="review-score-right-component"]', '[data-testid="review-count"]', '.review_list_score_count']);
          const nextSelectors = ['[data-testid="review-pagination-next"]',
            '[data-testid="review-list-container"] button[aria-label*="Página siguiente" i]',
            '[data-testid="review-list-container"] button[aria-label*="Siguiente" i]',
            '[data-testid="review-list-container"] button[aria-label*="Next" i]',
            '[data-testid="review-list-container"] a[aria-label*="Página siguiente" i]',
            '[data-testid="review-list-container"] a[aria-label*="Siguiente" i]',
            '[data-testid="review-list-container"] a[aria-label*="Next" i]',
            '.review_list_pagination_button--next'];
          let next = null;
          for (const selector of nextSelectors) { next = document.querySelector(selector); if (next) break; }
          const nextDisabled = !!next && (next.hasAttribute('disabled') || next.getAttribute('aria-disabled') === 'true' || next.classList.contains('disabled'));
          return {hotelName, reviews, bodyText: bodyText.slice(0, 12000), aggregateRating: Number((scoreText.match(/[0-9]+(?:[.,][0-9]+)?/) || [])[0]?.replace(',', '.')) || null,
                  reviewCountText: countText, hasNext: !!next, nextDisabled, nextLabel: next?.innerText?.trim() || '',
                  nextSelector: next ? nextSelectors.find((selector) => document.querySelector(selector) === next) : null,
                  firstReviewText: cards[0]?.innerText?.slice(0, 300) || '',
                  pageUrl: location.href, reviewCardCount: cards.length};
        }""",
        {"sourceUrl": source_url, "hotelName": hotel_name},
    )


async def _capture(url: str, hotel_name: str, max_reviews: int | None, checkpoint=None) -> dict:
    captured_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    collected: dict[str, dict] = {}
    pages = 0
    end_verified = False
    blocked = False
    pagination_stalled = False
    limit_reached = False
    async with async_playwright() as playwright:
        cdp_url = os.getenv("ATLAS_BOOKING_CDP_URL", "").strip()
        owns_browser = not cdp_url
        if cdp_url:
            # Booking can serve incomplete review markup to a fresh browser
            # session. Copy only Booking cookies into an isolated context so
            # capture does not depend on, or close, the user's open tabs.
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            context = await browser.new_context(locale="es-ES")
            owns_context = True
            if browser.contexts:
                booking_cookies = [
                    cookie for cookie in await browser.contexts[0].cookies()
                    if "booking.com" in cookie.get("domain", "")
                ]
                if booking_cookies:
                    await context.add_cookies(booking_cookies)
        else:
            headless_setting = os.getenv("ATLAS_BOOKING_HEADLESS", "1").strip().casefold()
            headless = headless_setting not in {"0", "false", "no", "off"}
            browser = await playwright.chromium.launch(headless=headless)
            context = await browser.new_context(locale="en-GB")
            owns_context = True
        page = await context.new_page()
        try:
            review_url = url.split("#", 1)[0] + "#tab-reviews"
            response = await page.goto(review_url, wait_until="domcontentloaded", timeout=45000)
            if response and response.status >= 400:
                return {"status": "error", "reviews": [], "capturedAt": captured_at,
                        "message": f"Booking devolvió HTTP {response.status}.", "pagesVisited": 0}
            for button in await page.get_by_role("button").all():
                try:
                    label = (await button.inner_text(timeout=300)).strip().casefold()
                    if any(word in label for word in ("reject", "rechazar")):
                        await button.click(timeout=800)
                        break
                except Exception:
                    continue
            cards = page.locator(_REVIEW_CARD_SELECTORS).first
            try:
                await cards.wait_for(timeout=7000)
            except Exception:
                for locator in (
                    page.locator('[data-testid="Property-Header-Nav-Tab-Trigger-reviews"]'),
                    page.locator('a[href*="#tab-reviews"]'),
                    page.locator('a[href="#blockdisplay4"]'),
                    page.locator('[data-testid*="review-tab"]'),
                    page.get_by_role("link", name=re.compile(r"reviews|reseñas", re.I)),
                    page.get_by_role("button", name=re.compile(r"reviews|reseñas", re.I)),
                ):
                    try:
                        if await locator.count():
                            await locator.first.click(timeout=1500)
                            break
                    except Exception:
                        continue
                try:
                    await cards.wait_for(timeout=20000)
                except Exception:
                    pass
            while pages < 500 and (not max_reviews or len(collected) < max_reviews):
                pages += 1
                snapshot = await _read_page(page, url, hotel_name)
                page_text = snapshot.get("bodyText", "").casefold()
                if any(marker in page_text for marker in _BLOCK_MARKERS):
                    blocked = True
                    break
                page_fully_processed = True
                for row_index, row in enumerate(snapshot["reviews"]):
                    signature = row.get("id") or "|".join((row.get("author", ""), str(row.get("rating") or ""), row.get("title", ""), row.get("positiveText", ""), row.get("negativeText", ""), row.get("dateText", "")))
                    row["sourceReviewId"] = row.get("id") or None
                    row["languageOriginal"] = "UND"
                    row["translationMethod"] = "booking_public_ui_language_unverified"
                    row["qualityFlags"] = ["language_unverified", "translation_not_available"]
                    row["publishedAt"] = _exact_public_datetime(row.get("dateTime")) or _exact_public_datetime(row.get("dateText"))
                    # Relative labels change between runs and Atlas uses them
                    # in provisional fingerprints when no source ID exists.
                    row["relativePublishedAt"] = (
                        row.get("dateText") or None
                    ) if not row["publishedAt"] and row.get("dateText") else None
                    row["datePrecision"] = "exact" if row["publishedAt"] else ("relative" if row["relativePublishedAt"] else "unknown")
                    row["reviewOriginal"] = "\n".join(
                        str(row.get(part) or "").strip() for part in ("title", "positiveText", "negativeText")
                        if str(row.get(part) or "").strip()
                    ) or None
                    row["ratingScale"] = 10
                    row["discoveryContexts"] = [{"page": pages, "source": "booking"}]
                    if signature in collected:
                        # Preserve the first observation and its provenance.
                        continue
                    collected[signature] = row
                    if max_reviews and len(collected) >= max_reviews:
                        limit_reached = True
                        page_fully_processed = row_index == len(snapshot["reviews"]) - 1
                        break
                if checkpoint:
                    checkpoint({"status": "partial", "reviews": list(collected.values()),
                                "capturedAt": captured_at, "pagesVisited": pages,
                                "coverage": {"strategy": "booking_public_review_pages_v1",
                                             "paginationEndVerified": False,
                                             "historicalCompletenessVerified": False,
                                             "interfaceLanguage": "en-GB"}})
                if snapshot["nextDisabled"]:
                    # Reaching the configured limit is still partial if this
                    # page contained more cards than we stored.
                    end_verified = page_fully_processed
                    break
                if limit_reached:
                    break
                if not snapshot["hasNext"] or not snapshot["nextSelector"]:
                    break
                old_url = page.url
                old_first = snapshot.get("firstReviewText") or ""
                next_button = page.locator(snapshot["nextSelector"]).first
                click_error = None
                try:
                    await next_button.click(timeout=4000)
                except Exception as exc:
                    click_error = exc
                    # The public Booking paginator can be visible and enabled
                    # while its expanding review container prevents Playwright
                    # from completing a native pointer click. Try the same
                    # visible control through the DOM after scrolling it in.
                    try:
                        await next_button.evaluate("button => { button.scrollIntoView({block: 'center'}); button.click(); }")
                    except Exception:
                        raise click_error
                try:
                    await page.wait_for_function(
                        "({url, first}) => location.href !== url || (document.querySelector('[data-testid=review-card]')?.innerText || document.querySelector('.review_list_new_item_block')?.innerText || '').slice(0, 300) !== first",
                        arg={"url": old_url, "first": old_first or ""}, timeout=10000,
                    )
                except Exception:
                    if click_error:
                        pagination_stalled = True
                        break
                    # One retry is safe only after proving the page did not
                    # advance, avoiding duplicate clicks while it is loading.
                    await next_button.evaluate("button => { button.scrollIntoView({block: 'center'}); button.click(); }")
                    try:
                        await page.wait_for_function(
                            "({url, first}) => location.href !== url || (document.querySelector('[data-testid=review-card]')?.innerText || document.querySelector('.review_list_new_item_block')?.innerText || '').slice(0, 300) !== first",
                            arg={"url": old_url, "first": old_first or ""}, timeout=10000,
                        )
                    except Exception:
                        pagination_stalled = True
                        break
            aggregate = snapshot.get("aggregateRating") if "snapshot" in locals() else None
            if blocked:
                status = "partial" if collected else "blocked"
                message = "La página mostró una barrera de acceso; se conservaron las reseñas ya visibles."
            elif limit_reached and not end_verified:
                status = "partial"
                message = "Se alcanzó el máximo de reseñas configurado antes de verificar el final de paginación."
            elif pages >= 500 and not end_verified:
                status = "partial"
                message = "Se alcanzó el límite técnico de 500 páginas; el recorrido puede continuar en otra captura."
            elif end_verified:
                status = "exhausted"
                message = "Se llegó al control de paginación desactivado; esto solo cubre el historial que Booking expone."
            elif collected:
                status = "partial"
                message = ("El control de paginación no avanzó; se conservaron las reseñas visibles."
                           if pagination_stalled else
                           "No se encontró un control de paginación reconocible; no se puede confirmar que el recorrido esté completo.")
            else:
                status = "parse_error"
                message = "La página cargó, pero no se reconocieron tarjetas de reseñas."
            return {"status": status, "reviews": list(collected.values())[:max_reviews] if max_reviews else list(collected.values()), "capturedAt": captured_at,
                    "aggregateRating": aggregate,
                    "publishedReviewCount": _review_count(snapshot.get("reviewCountText")) if "snapshot" in locals() else None,
                    "pagesVisited": pages,
                    "coverage": {"strategy": "booking_public_review_pages_v1", "paginationEndVerified": end_verified,
                                 "limitReached": limit_reached, "pageCapReached": pages >= 500 and not end_verified,
                                 "paginationStalled": pagination_stalled,
                                 "paginationControl": snapshot.get("nextSelector") if "snapshot" in locals() else None,
                                 "paginationNextDisabled": snapshot.get("nextDisabled") if "snapshot" in locals() else None,
                                 "historicalCompletenessVerified": False,
                                 "interfaceLanguage": "en-GB", "durationSeconds": round(time.monotonic() - started, 2)},
                    "message": message, "sourceUrl": url}
        except Exception as exc:
            message = str(exc)
            is_blocked = any(marker in message.casefold() for marker in _BLOCK_MARKERS)
            return {"status": "partial" if collected else ("blocked" if is_blocked else "parse_error"),
                    "reviews": list(collected.values()), "capturedAt": captured_at, "pagesVisited": pages,
                    "coverage": {"strategy": "booking_public_review_pages_v1", "historicalCompletenessVerified": False,
                                 "interfaceLanguage": "en-GB", "durationSeconds": round(time.monotonic() - started, 2),
                                 "exceptionType": type(exc).__name__,
                                 "exceptionMessage": re.sub(r"https?://[^\s]+", "<url>", str(exc))[:800],
                                 "publishedReviewCount": _review_count(snapshot.get("reviewCountText")) if "snapshot" in locals() else None,
                                 "aggregateRating": snapshot.get("aggregateRating") if "snapshot" in locals() else None},
                    "message": "Booking bloqueó o modificó la página de reseñas." if is_blocked else "No se pudo recorrer la página pública de reseñas."}
        finally:
            await page.close()
            if owns_context:
                await context.close()
            if owns_browser:
                await browser.close()


def collect_booking_reviews(url: str, hotel_name: str, max_reviews: int | None = 1000, checkpoint=None) -> dict:
    if max_reviews is not None and not 1 <= max_reviews <= 10000:
        raise ValueError("max_reviews debe ser None (hasta agotar recorrido) o estar entre 1 y 10.000.")
    return asyncio.run(_capture(url, hotel_name, max_reviews, checkpoint))
