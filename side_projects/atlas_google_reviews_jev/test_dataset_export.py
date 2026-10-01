from __future__ import annotations

import unittest
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from .dataset_export import review_text_fields, write_tsv


class DatasetExportTests(unittest.TestCase):
    def test_splits_google_translation_and_detects_original_language(self):
        fields = review_text_fields(
            "(Traducido por Google) El hotel es excelente. (Original) The hotel is excellent."
        )
        self.assertEqual(fields["review_es"], "El hotel es excelente.")
        self.assertEqual(fields["review_original"], "The hotel is excellent.")
        self.assertEqual(fields["language_original"], "EN")
        self.assertEqual(fields["translation_method"], "google_ui")

    def test_keeps_native_spanish_in_both_text_fields(self):
        fields = review_text_fields("La estancia fue muy agradable para toda la familia.")
        self.assertEqual(fields["review_es"], fields["review_original"])
        self.assertEqual(fields["language_original"], "ES")
        self.assertEqual(fields["translation_method"], "original_es")

    def test_rating_only_review_has_no_language_guess(self):
        fields = review_text_fields(None)
        self.assertEqual(fields["review_es"], "")
        self.assertEqual(fields["review_original"], "")
        self.assertEqual(fields["language_original"], "UND")
        self.assertEqual(fields["translation_method"], "no_text")

    def test_short_english_original_gets_low_confidence_english_tag(self):
        fields = review_text_fields("(Traducido por Google) Mal sitio. (Original) Bad place")
        self.assertEqual(fields["language_original"], "EN")
        self.assertEqual(fields["language_confidence"], "0.65")

    def test_tab_separator_keeps_language_punctuation_inside_review(self):
        value = "Muy bien, aunque hubo detalles; aun así: volvería.\tNota extra"
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reviews.csv"
            write_tsv(path, [{"review_es": value}], ("review_es",))
            with path.open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(row["review_es"], value)


if __name__ == "__main__":
    unittest.main()
