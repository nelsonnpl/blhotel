from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup, Tag

from .schema import GoogleReview, GoogleReviewsResult


_RATING_RE = re.compile(
    r"(?P<rating>[1-5](?:[\.,]\d+)?)\s*(?:/\s*5|de\s*5|out\s*of\s*5|stars?|estrellas?)",
    re.IGNORECASE,
)
_COUNT_RE = re.compile(
    r"(?<![\d.,])(?P<count>\d{1,3}(?:[.,]\d{3})*|\d+)\s*(?:reviews?|reseñas?|opiniones?)",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T[^\s]+)?$")
_STANDALONE_RATING_RE = re.compile(r"^[1-5](?:[\.,]\d)?$")
_BLOCKED_RE = re.compile(
    r"captcha|verify you are human|unusual traffic|robot check|inicia sesión|sign in to continue",
    re.IGNORECASE,
)


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    value = " ".join(value.split()).strip()
    return value or None


def _visible_text(node: Tag) -> str:
    return _clean(node.get_text(" ", strip=True)) or ""


def _first_text(node: Tag, selectors: Iterable[str]) -> str | None:
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            if found.name == "meta":
                raw_value = found.get("content")
            else:
                raw_value = found.get("data-hotel-name") or found.get("data-author") or found.get_text(" ", strip=True)
            value = _clean(raw_value)
            if value:
                return value
    return None


def _rating(node: Tag) -> float | None:
    candidates: list[str] = []
    for item in [node, *node.select("[aria-label], [data-rating], [rating]")]:
        for attr in ("aria-label", "data-rating", "rating"):
            value = item.get(attr)
            if value:
                candidates.append(str(value))
        text = _visible_text(item)
        if text:
            candidates.append(text[:240])
    for candidate in candidates:
        match = _RATING_RE.search(candidate)
        if match:
            return float(match.group("rating").replace(",", "."))
    return None


def _review_text(node: Tag) -> str | None:
    if "Svr5cf" in (node.get("class") or []):
        # Google Hotels can have rating-only reviews. Do not mistake hotel
        # aspect ratings or an owner reply for the reviewer's written text.
        return _first_text(node, (
            ".kVathc .eLNT1d .K7oBsc",
            ".kVathc .K7oBsc",
        ))
    value = _first_text(node, (
        "[data-review-text]",
        "[data-review-content]",
        "[itemprop='reviewBody']",
        ".wiI7pd",  # Google Maps' visible review body
    ))
    if value:
        return value
    # Prefer a reasonably long leaf text over labels such as the star rating.
    candidates = []
    for child in node.select("span, div, p"):
        text = _visible_text(child)
        if 35 <= len(text) <= 5000 and not _RATING_RE.search(text):
            candidates.append(text)
    return max(candidates, key=len, default=None)


def _review_blocks(soup: BeautifulSoup) -> list[Tag]:
    # Google Maps repeats data-review-id on a card's buttons and inner divs.
    # Keep the outermost node for each id so one visible review becomes one row.
    cards: list[Tag] = []
    seen_ids: set[str] = set()
    for node in soup.select("[data-review-id]"):
        review_id = str(node.get("data-review-id"))
        if review_id in seen_ids or node.find_parent(attrs={"data-review-id": review_id}):
            continue
        if len(_visible_text(node)) < 20:
            continue
        seen_ids.add(review_id)
        cards.append(node)
    if cards:
        return cards

    # Google Hotels renders more reviews than the limited Maps preview. Its
    # default list mixes Google and external providers, so accept only cards
    # whose visible source is Google.
    travel_cards = [
        node for node in soup.select(".Svr5cf.bKhjM")
        if "google" in (_first_text(node, (".iUtr1",)) or "").casefold()
    ]
    if travel_cards:
        return travel_cards

    selectors = (
        "[data-review]",
        "[itemprop='review']",
        "[jsaction*='review']",
    )
    blocks: list[Tag] = []
    seen: set[int] = set()
    for selector in selectors:
        for node in soup.select(selector):
            marker = id(node)
            if marker not in seen:
                seen.add(marker)
                blocks.append(node)
    return blocks


def _aggregate_rating(soup: BeautifulSoup) -> float | None:
    # Read a displayed aggregate value, not a hotel's star category or the
    # first individual review rating found elsewhere on the page.
    for selector in (
        ".jANrlb .fontDisplayLarge",  # Google Maps Reviews summary
        ".iDqPh.BgYkof",  # Google Hotels Reviews summary
        ".F7nice [aria-hidden='true']",  # Google Maps place overview
        "[itemprop='ratingValue']",
        "meta[itemprop='ratingValue']",
    ):
        node = soup.select_one(selector)
        if node:
            raw = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
            value = _clean(raw)
            if value and _STANDALONE_RATING_RE.match(value):
                return float(value.replace(",", "."))
    return None


def _hotel_attributes(soup: BeautifulSoup, final_url: str | None) -> dict:
    """Extract a small allowlist of objective facts visible on the place page."""
    values: dict[str, str] = {}
    for node in soup.select("[data-item-id]"):
        item_id = str(node.get("data-item-id") or "").casefold()
        text = _visible_text(node)
        if not text:
            continue
        if item_id == "address": values.setdefault("address", text)
        elif item_id.startswith("phone:"): values.setdefault("phone", text)
        elif item_id in {"oh", "hours"}: values.setdefault("hours", text)
        elif item_id == "authority":
            href = str(node.get("href") or "").strip()
            if href.startswith("https://"): values.setdefault("website", href)
    category = _first_text(soup, ("button[jsaction*='pane.rating.category']", "[data-item-id='category']"))
    if category: values["category"] = category
    if final_url:
        coordinate = re.search(r"@(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)", final_url)
        if coordinate:
            values["latitude"], values["longitude"] = coordinate.group(1), coordinate.group(2)
    return values


def parse_reviews_html(
    html: str,
    *,
    source_url: str,
    captured_at: str,
    final_url: str | None = None,
    fallback_hotel_name: str | None = None,
    navigation_steps: int = 0,
) -> GoogleReviewsResult:
    """Parse visible review markup without relying on Google's internal RPCs."""

    soup = BeautifulSoup(html or "", "html.parser")
    page_text = _visible_text(soup.body or soup)
    if _BLOCKED_RE.search(page_text):
        return GoogleReviewsResult(
            status="blocked",
            sourceUrl=source_url,
            finalUrl=final_url,
            hotelName=fallback_hotel_name,
            capturedAt=captured_at,
            navigationSteps=navigation_steps,
            message="La página requiere una comprobación, una sesión o no permite continuar.",
        )

    title = _clean(soup.title.get_text(" ", strip=True) if soup.title else None)
    hotel_name = _first_text(soup, ("[data-hotel-name]", "[itemprop='name']")) or fallback_hotel_name or title
    aggregate_rating = _aggregate_rating(soup)
    hotel_attributes = _hotel_attributes(soup, final_url)
    review_count = None
    count_match = _COUNT_RE.search(page_text)
    if count_match:
        digits = re.sub(r"\D", "", count_match.group("count"))
        review_count = int(digits) if digits else None

    reviews: list[GoogleReview] = []
    for block in _review_blocks(soup):
        text = _review_text(block)
        rating = _rating(block)
        author = _first_text(block, (
            "[data-review-author]", "[itemprop='author']", "[data-author]",
            "a.DHIhE[href*='/maps/contrib/']",  # Google Hotels reviewer name
        ))
        if not author and block.get("data-review-id"):
            author = _clean(block.get("aria-label"))
        if not author:
            author_node = block.select_one("a[aria-label*='profile' i], a[href*='/maps/contrib/']")
            author = _clean(author_node.get_text(" ", strip=True) if author_node else None)
        time_node = block.select_one("time[datetime], [data-review-date], [itemprop='datePublished']")
        published = None
        relative = None
        if time_node:
            published = _clean(time_node.get("datetime") or time_node.get("content"))
            visible_date = _clean(time_node.get_text(" ", strip=True))
            relative = visible_date if visible_date and not _DATE_RE.match(visible_date) else None
        if not published and not relative:
            relative = _first_text(block, (".xRkPPb", ".iUtr1"))
        if not text and rating is None:
            continue
        report_link = block.select_one("a[href*='/local/content/rap/report?']")
        report_id = None
        if report_link and report_link.get("href"):
            report_id = (parse_qs(urlsplit(str(report_link["href"])).query).get("postId") or [None])[0]
        # Only a platform-provided ID is stable across sorting and reruns.
        # Atlas assigns a provisional fingerprint when neither is visible.
        review_id = block.get("data-review-id") or report_id or None
        reviews.append(
            GoogleReview(
                reviewId=str(review_id) if review_id else None,
                hotelName=hotel_name,
                authorName=author,
                rating=rating,
                text=text,
                publishedAt=published,
                relativePublishedAt=relative,
                sourceUrl=source_url,
                capturedAt=captured_at,
            )
        )

    status = "ok" if reviews else "empty"
    return GoogleReviewsResult(
        status=status,
        sourceUrl=source_url,
        finalUrl=final_url,
        hotelName=hotel_name,
        aggregateRating=aggregate_rating,
        reviewCount=review_count,
        hotelAttributes=hotel_attributes,
        reviews=reviews,
        capturedAt=captured_at,
        navigationSteps=navigation_steps,
        message=None if reviews else "No se encontraron reseñas visibles con la estructura actual.",
    )
