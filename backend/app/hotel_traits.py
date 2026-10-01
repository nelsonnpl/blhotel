"""Rasgos de un hotel que Booking no entrega como campo y se leen del nombre.

Booking no publica la cadena ni el segmento «solo adultos» en los resultados de
búsqueda. Para poder agrupar y filtrar la hoja de mercado se derivan del propio
nombre con reglas explícitas y conservadoras:

* Solo se reconoce una marca cuando aparece literalmente en el nombre.
* Si ninguna regla coincide, el valor es ``None`` (desconocido); nunca se supone.
* ``adults_only`` es ``True`` solo si el nombre lo declara; ``False`` significa
  «el nombre no lo indica», no que el hotel admita niños.
"""
from __future__ import annotations

import re
import unicodedata

# (etiqueta mostrada, patrón sobre el nombre normalizado: minúsculas y sin acentos)
# El orden importa: la primera coincidencia gana. «by lopesan» va antes que las
# marcas propias para que «Corallium … by Lopesan Hotels» sea Lopesan.
_CHAIN_RULES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(pattern))
    for label, pattern in (
        ("Lopesan", r"\blopesan\b"),
        ("Dunas", r"\bby dunas\b"),
        ("Servatur", r"^servatur\b"),
        ("Barceló", r"\bbarcelo\b"),
        ("Occidental", r"^occidental\b"),
        ("BLUESEA", r"\bbluesea\b"),
        ("H10", r"^h10\b"),
        ("HL", r"^hl\b"),
        ("LIVVO", r"\blivvo\b"),
        ("Riu", r"\briu\b"),
        ("Seaside", r"^seaside\b"),
        ("Gloria Palace", r"\bgloria palace\b"),
        ("Relaxia", r"^relaxia\b"),
        ("MUR", r"^mur\b"),
        ("Paradisus", r"^paradisus\b"),
        ("HD", r"^hd\b"),
        ("Princess", r"\bprincess\b"),
        ("eó", r"^eo\b"),
        ("Iberostar", r"\biberostar\b"),
        ("Meliá", r"\bmelia\b"),
    )
)

_ADULTS_ONLY = re.compile(r"\b(adults? only|only adults?|solo adultos|adultos solamente)\b")


def _normalise(name: str | None) -> str:
    text = unicodedata.normalize("NFD", name or "")
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", text.lower()).strip()


def detect_chain(name: str | None) -> str | None:
    """Cadena o marca reconocible en el nombre, o ``None`` si no hay ninguna."""
    normalised = _normalise(name)
    for label, pattern in _CHAIN_RULES:
        if pattern.search(normalised):
            return label
    return None


def is_adults_only(name: str | None) -> bool:
    """``True`` solo si el nombre declara que el hotel es solo para adultos."""
    return bool(_ADULTS_ONLY.search(_normalise(name)))
