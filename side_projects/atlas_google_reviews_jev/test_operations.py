from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.app.public_booking_reviews import _capture, _exact_public_datetime, _read_page
from playwright.async_api import async_playwright
from .jev_runner import _collect_travel_reviews
from .openrouter_jev import JevBudgetExceeded, route_jev_through_openrouter
from .schema import GoogleReview, GoogleReviewsResult


class OpenRouterBudgetTests(unittest.TestCase):
    def setUp(self):
        self.key = patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
        self.key.start()
        self.addCleanup(self.key.stop)

    def test_zero_budget_is_rejected(self):
        module = type("Module", (), {"post_json": lambda *args: {}})()
        with self.assertRaises(ValueError):
            with route_jev_through_openrouter(module, budget_usd=0,
                                             estimated_decision_cost_usd=0.1):
                pass

    def test_estimated_budget_stops_before_another_decision(self):
        calls = []
        module = type("Module", (), {})()
        module.post_json = lambda *args: (calls.append(args), {"decision": "done"})[1]
        usage = {}
        with route_jev_through_openrouter(module, budget_usd=0.1,
                                         estimated_decision_cost_usd=0.06,
                                         usage=usage):
            module.post_json("https://api.typesafe.ai/v1/systemone", "ignored", {})
            with self.assertRaises(JevBudgetExceeded):
                module.post_json("https://api.typesafe.ai/v1/systemone", "ignored", {})
        self.assertEqual(len(calls), 1)
        self.assertEqual(usage["decisions"], 1)

    def test_provider_cost_over_estimate_prevents_next_decision(self):
        calls = []
        module = type("Module", (), {})()
        module.post_json = lambda *args: (calls.append(args), {"usage": {"cost": 0.2}})[1]
        usage = {}
        with route_jev_through_openrouter(module, budget_usd=0.1,
                                         estimated_decision_cost_usd=0.05,
                                         usage=usage):
            module.post_json("https://api.typesafe.ai/v1/systemone", "ignored", {})
            with self.assertRaises(JevBudgetExceeded):
                module.post_json("https://api.typesafe.ai/v1/systemone", "ignored", {})
        self.assertTrue(usage["budgetExceededByProviderCost"])
        self.assertEqual(len(calls), 1)


class _FakeLocator:
    @property
    def first(self):
        return self

    async def wait_for(self, **kwargs):
        return None

    async def click(self, **kwargs):
        return None


class _FakePage:
    url = "https://www.booking.com/hotel/example.html"

    async def goto(self, *args, **kwargs):
        return None

    def get_by_role(self, *args, **kwargs):
        return self

    async def all(self):
        return []

    def locator(self, *args, **kwargs):
        return _FakeLocator()

    async def wait_for_function(self, *args, **kwargs):
        raise TimeoutError("No apareció otra página")


class _FakeContext:
    async def new_page(self):
        return _FakePage()

    async def close(self):
        return None


class _FakeBrowser:
    async def new_context(self, **kwargs):
        return _FakeContext()

    async def close(self):
        return None


class _FakeChromium:
    async def launch(self, **kwargs):
        return _FakeBrowser()


class _FakePlaywright:
    chromium = _FakeChromium()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class BookingPaginationTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_time_datetime_is_read_from_local_html(self):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.set_content("""
                    <article data-testid="review-card" data-review-id="one">
                      <span data-testid="reviewer-name">Ana</span>
                      <span data-testid="review-positive-text">Limpio</span>
                      <time data-testid="review-date" datetime="2026-07-15">Reviewed recently</time>
                    </article>
                """)
                snapshot = await _read_page(page, "https://www.booking.com/hotel/example.html", "Hotel")
            finally:
                await browser.close()
        self.assertEqual(snapshot["reviews"][0]["dateTime"], "2026-07-15")
        self.assertEqual(snapshot["reviews"][0]["dateText"], "Reviewed recently")
        self.assertEqual(_exact_public_datetime(snapshot["reviews"][0]["dateTime"]), "2026-07-15")
        self.assertIsNone(_exact_public_datetime("15/07/2026"))
        self.assertIsNone(_exact_public_datetime("2026-02-30"))

    async def test_stalled_next_control_stays_partial_and_does_not_repeat_pages(self):
        snapshot = {
            "reviews": [{"id": "review-1", "author": "A", "title": "Bien",
                         "rating": 9, "positiveText": "Limpio", "negativeText": "",
                         "dateText": "Reviewed recently", "dateTime": "2026-01-01"}],
            "bodyText": "Hotel",
            "aggregateRating": 8.7,
            "reviewCountText": "100 reviews",
            "hasNext": True,
            "nextDisabled": False,
            "nextSelector": "a.next",
            "firstReviewText": "A Bien",
        }
        calls = []

        async def read_page(*args):
            calls.append(1)
            return snapshot

        with patch("backend.app.public_booking_reviews.async_playwright", return_value=_FakePlaywright()), \
             patch("backend.app.public_booking_reviews._read_page", new=read_page):
            result = await _capture("https://www.booking.com/hotel/example.html", "Hotel", 10)

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["pagesVisited"], 1)
        self.assertEqual(len(calls), 1)
        self.assertTrue(result["coverage"]["paginationStalled"])
        self.assertEqual(len(result["reviews"]), 1)
        self.assertEqual(result["reviews"][0]["publishedAt"], "2026-01-01")
        self.assertIsNone(result["reviews"][0]["relativePublishedAt"])
        self.assertEqual(result["reviews"][0]["reviewOriginal"], "Bien\nLimpio")


class _FakeGoogleBrowser:
    def evaluate(self, expression):
        if "aria-selected" in expression:
            return "Más recientes"
        if "outerHTML" in expression:
            return "<html></html>"
        if "location.href" in expression:
            return "https://www.google.com/travel/hotels/entity/test/reviews"
        return None


class GoogleCoverageTests(unittest.TestCase):
    def test_unverified_filters_cannot_be_reported_as_exhausted(self):
        review = GoogleReview(
            reviewId="r1", sourceUrl="https://www.google.com/travel/hotels/entity/test/reviews",
            capturedAt="2026-09-23T00:00:00+00:00", text="Habitación limpia")

        def parsed(*args, **kwargs):
            return GoogleReviewsResult(status="ok", sourceUrl=review.sourceUrl, reviews=[review])

        with patch("side_projects.atlas_google_reviews_jev.jev_runner._choose_travel_option", return_value=False), \
             patch("side_projects.atlas_google_reviews_jev.jev_runner._expand_travel_topics", return_value=[]), \
             patch("side_projects.atlas_google_reviews_jev.jev_runner._selected_topic", return_value=True), \
             patch("side_projects.atlas_google_reviews_jev.jev_runner._travel_card_signature", return_value=[]), \
             patch("side_projects.atlas_google_reviews_jev.jev_runner._blocked_page", return_value=False), \
             patch("side_projects.atlas_google_reviews_jev.jev_runner.parse_reviews_html", side_effect=parsed):
            result = _collect_travel_reviews(
                _FakeGoogleBrowser(), source_url=review.sourceUrl, hotel_name="Hotel",
                captured_at=review.capturedAt, navigation_steps=1, max_reviews=10)

        self.assertEqual(result.status, "partial")
        self.assertFalse(result.coverage["googleSourceFilterVerified"])
        self.assertEqual(result.coverage["completedContextCount"], 1)


if __name__ == "__main__":
    unittest.main()
