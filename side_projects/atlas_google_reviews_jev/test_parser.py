from __future__ import annotations

import unittest

from .parser import parse_reviews_html


def parse(html: str):
    return parse_reviews_html(
        html,
        source_url="https://www.google.com/travel/hotels/entity/example/reviews",
        captured_at="2026-09-22T00:00:00+00:00",
        fallback_hotel_name="Hotel de prueba",
    )


class ReviewParserTests(unittest.TestCase):
    def test_maps_nested_review_id_is_one_review(self):
        result = parse("""
            <html><body><div class="jANrlb"><span class="fontDisplayLarge">4,3</span></div>
            <span>1.234 reseñas</span>
            <div data-review-id="review-1" aria-label="Ada">
              <span class="fontBodyLarge fzvQIb" aria-label="4 de 5 estrellas"></span>
              <span class="xRkPPb">hace 2 días</span>
              <div class="wiI7pd">Una estancia agradable con vistas al mar.</div>
              <button data-review-id="review-1">Compartir</button>
            </div></body></html>
        """)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.aggregateRating, 4.3)
        self.assertEqual(result.reviewCount, 1234)
        self.assertEqual(len(result.reviews), 1)
        self.assertEqual(result.reviews[0].reviewId, "review-1")
        self.assertEqual(result.reviews[0].authorName, "Ada")

    def test_hotels_excludes_other_sources_and_owner_reply(self):
        result = parse("""
            <html><body><span class="iDqPh BgYkof">4,2</span><span>2.960 reseñas</span>
            <div class="Svr5cf bKhjM">
              <a class="DHIhE" href="/maps/contrib/123">Luis</a>
              <span class="iUtr1">hace 3 días en Google</span>
              <span class="GDWaad" aria-label="5/5">5/5</span>
              <a href="/local/content/rap/report?postId=google-1">Denunciar</a>
              <div class="K7oBsc">Respuesta del propietario que no es una reseña</div>
            </div>
            <div class="Svr5cf bKhjM"><span class="iUtr1">en Tripadvisor</span>
              <span aria-label="5/5">5/5</span><div class="kVathc"><span class="K7oBsc">Externa</span></div>
            </div></body></html>
        """)
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.reviews), 1)
        self.assertEqual(result.reviews[0].reviewId, "google-1")
        self.assertEqual(result.reviews[0].rating, 5)
        self.assertIsNone(result.reviews[0].text)

    def test_review_without_platform_id_remains_provisional(self):
        result = parse("""
            <html><body><div class="Svr5cf bKhjM">
              <a class="DHIhE" href="/maps/contrib/123">Luis</a>
              <span class="iUtr1">hace 3 días en Google</span>
              <span aria-label="5/5">5/5</span>
              <div class="kVathc"><span class="K7oBsc">Una estancia muy buena.</span></div>
            </div></body></html>
        """)
        self.assertEqual(len(result.reviews), 1)
        self.assertIsNone(result.reviews[0].reviewId)


if __name__ == "__main__":
    unittest.main()
