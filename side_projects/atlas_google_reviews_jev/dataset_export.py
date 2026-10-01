"""Normalize review text and write spreadsheet-friendly tab-delimited CSVs."""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Iterable

from langdetect import DetectorFactory, detect_langs


DetectorFactory.seed = 0

_GOOGLE_TRANSLATION = re.compile(
    r"\(Traducido por Google\)\s*(.*?)\s*\(Original\)\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)
_WORD = re.compile(r"[a-z]+", re.IGNORECASE)
_ENGLISH_SHORT_TEXT = {
    "i", "the", "and", "with", "for", "this", "is", "of", "was", "are",
    "ever", "stayed", "lovely", "very", "nice", "great", "worst", "bad",
    "place", "quiet", "families", "beautiful", "stay", "food", "staff", "gym",
}


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFC", value).replace("\u200b", "").replace("\xa0", " ")
    return value.strip()


def _language(text: str, *, translated_by_google: bool) -> tuple[str, str, str]:
    if not text:
        return "UND", "", "no_text"
    try:
        guesses = detect_langs(text)
    except Exception:  # noqa: BLE001 - short or unusual strings can defeat language detection
        guesses = []
    if not guesses:
        return "UND", "", "undetermined"

    detected = guesses[0]
    code = detected.lang.split("-")[0].upper()
    confidence = round(float(detected.prob), 3)
    words = set(_WORD.findall(text.casefold()))
    english_hits = len(words & _ENGLISH_SHORT_TEXT)

    # Language detectors often misclassify one-line English reviews as Danish,
    # Czech, or Spanish. Only apply this narrow correction when Google itself
    # provided a translation and the original contains several English cues.
    if translated_by_google and len(text) < 60 and english_hits >= 2 and code != "EN":
        return "EN", "0.65", "short_text_english_heuristic"

    # Avoid presenting a highly uncertain short snippet as a certain language.
    if len(words) < 3 and confidence < 0.9:
        return "UND", f"{confidence:.2f}", "low_confidence_short_text"
    return code, f"{confidence:.2f}", "langdetect"


def review_text_fields(raw_text: str | None) -> dict[str, str]:
    """Split Google's Spanish translation and original, retaining both texts."""

    raw = _clean_text(raw_text)
    if not raw:
        return {
            "review_es": "",
            "review_original": "",
            "language_original": "UND",
            "language_confidence": "",
            "translation_method": "no_text",
        }

    match = _GOOGLE_TRANSLATION.search(raw)
    if match:
        spanish = _clean_text(match.group(1))
        original = _clean_text(match.group(2))
        language, confidence, detection_method = _language(original, translated_by_google=True)
        method = "google_ui" if original else "google_ui_original_missing"
        return {
            "review_es": spanish,
            "review_original": original,
            "language_original": language,
            "language_confidence": confidence,
            "translation_method": method if detection_method != "short_text_english_heuristic" else "google_ui_heuristic",
        }

    original = raw
    language, confidence, detection_method = _language(original, translated_by_google=False)
    spanish = original if language == "ES" else ""
    method = "original_es" if language == "ES" else "no_spanish_translation_available"
    if detection_method == "low_confidence_short_text":
        method += ";language_uncertain"
    return {
        "review_es": spanish,
        "review_original": original,
        "language_original": language,
        "language_confidence": confidence,
        "translation_method": method,
    }


REVIEW_COLUMNS = (
    "requested_hotel", "observed_hotel", "review_id", "author", "rating",
    "review_es", "review_original", "language_original", "language_confidence",
    "translation_method", "published_at", "relative_published_at", "captured_at",
    "source_url",
)

STATUS_COLUMNS = (
    "requested_hotel", "observed_hotel", "status", "reviews_captured", "aggregate_rating",
    "google_review_count", "captured_at", "source_url", "final_url", "message",
)


def write_tsv(path: Path, rows: Iterable[dict], columns: tuple[str, ...]) -> None:
    """Write tab-separated rows with CSV quoting and a UTF-8 BOM for Excel."""

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def enrich_existing_review_csv(path: Path) -> int:
    """Convert the existing comma-separated raw export to the requested TSV CSV."""

    with path.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    rows: list[dict] = []
    for row in source_rows:
        rows.append({
            "requested_hotel": row.get("requested_hotel", ""),
            "observed_hotel": row.get("observed_hotel", ""),
            "review_id": row.get("review_id", ""),
            "author": row.get("author", ""),
            "rating": row.get("rating", ""),
            **review_text_fields(row.get("text")),
            "published_at": row.get("published_at", ""),
            "relative_published_at": row.get("relative_published_at", ""),
            "captured_at": row.get("captured_at", ""),
            "source_url": row.get("source_url", ""),
        })
    write_tsv(path, rows, REVIEW_COLUMNS)
    return len(rows)
