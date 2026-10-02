"""B1-01: gzip en memoria para estáticos versionados por mtime."""

from __future__ import annotations

import gzip
from pathlib import Path

from backend.app import flask_app

app = flask_app.app
STATIC_ROOT = Path(flask_app.app.static_folder).resolve()


def _get(path: str, gzip_ok: bool):
    headers = {"Accept-Encoding": "gzip" if gzip_ok else "identity"}
    return app.test_client().get(path, headers=headers)


def test_static_js_gzip_encoding_vary_immutable() -> None:
    flask_app._STATIC_GZIP_CACHE.clear()
    response = _get("/static/atlas.js", gzip_ok=True)

    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") == "gzip"
    assert "Accept-Encoding" in response.headers.get("Vary", "")
    assert "immutable" in response.headers.get("Cache-Control", "")

    raw_len = (STATIC_ROOT / "atlas.js").stat().st_size
    assert raw_len >= 400_000, raw_len
    wire_len = len(response.get_data())
    assert 100_000 <= wire_len <= 135_000, wire_len

    plain = _get("/static/atlas.js", gzip_ok=False)
    assert plain.headers.get("Content-Encoding") is None
    assert "immutable" in plain.headers.get("Cache-Control", "")
    assert gzip.decompress(response.get_data()) == plain.get_data()


def test_static_css_gzip_encoding_vary_immutable() -> None:
    flask_app._STATIC_GZIP_CACHE.clear()
    response = _get("/static/atlas.css", gzip_ok=True)

    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") == "gzip"
    assert "Accept-Encoding" in response.headers.get("Vary", "")
    assert "immutable" in response.headers.get("Cache-Control", "")

    raw_len = (STATIC_ROOT / "atlas.css").stat().st_size
    assert raw_len >= 150_000, raw_len
    wire_len = len(response.get_data())
    # Cota holgada: el CSS crece con tokens/motion/forced-colors (oleada 3);
    # el objetivo vinculante es el total js+css <= 160 KB.
    assert 25_000 <= wire_len <= 42_000, wire_len

    plain = _get("/static/atlas.css", gzip_ok=False)
    assert gzip.decompress(response.get_data()) == plain.get_data()


def test_static_gzip_cache_keyed_by_path_and_mtime() -> None:
    flask_app._STATIC_GZIP_CACHE.clear()
    first = _get("/static/atlas.js", gzip_ok=True)
    assert first.status_code == 200
    assert len(flask_app._STATIC_GZIP_CACHE) == 1
    key = next(iter(flask_app._STATIC_GZIP_CACHE))
    resolved = str((STATIC_ROOT / "atlas.js").resolve())
    assert key[0] == resolved

    second = _get("/static/atlas.js", gzip_ok=True)
    assert second.get_data() == first.get_data()
    assert len(flask_app._STATIC_GZIP_CACHE) == 1


def test_static_gzip_content_type_matches_plain() -> None:
    gzipped = _get("/static/atlas.js", gzip_ok=True)
    plain = _get("/static/atlas.js", gzip_ok=False)
    assert gzipped.headers["Content-Type"].split(";")[0] == plain.headers["Content-Type"].split(";")[0]

    gzipped_css = _get("/static/atlas.css", gzip_ok=True)
    plain_css = _get("/static/atlas.css", gzip_ok=False)
    assert gzipped_css.headers["Content-Type"].split(";")[0] == plain_css.headers["Content-Type"].split(";")[0]


def test_api_gzip_without_regression() -> None:
    # B1-02: la API ya comprimía; debe seguir igual tras el cambio B1-01.
    response = _get("/api/air-data?includeFlights=0", gzip_ok=True)

    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") == "gzip"
    assert "Accept-Encoding" in response.headers.get("Vary", "")
