from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECODO_API_URL = "https://scraper-api.decodo.com/v2/scrape"


@dataclass(frozen=True)
class DecodoSettings:
    username: str
    password: str
    api_url: str
    locale: str | None = "es-es"
    geo: str | None = "Spain"
    proxy_pool: str | None = "premium"


@dataclass(frozen=True)
class AppSettings:
    decodo: DecodoSettings
    sqlite_path: Path


def _read_token() -> tuple[str, str]:
    raw = (os.getenv("DECODO_TOKEN") or os.getenv("DECODO_BASIC_AUTH_TOKEN") or "").strip()
    if not raw:
        return "", ""

    normalized = raw.removeprefix("Basic ").strip()
    decoded = base64.b64decode(normalized).decode("utf-8")
    username, separator, password = decoded.partition(":")
    if not separator:
        return "", ""
    return username.strip(), password.strip()


def load_settings(require_decodo: bool = False) -> AppSettings:
    load_dotenv(ROOT / ".env", override=True)

    username = (os.getenv("DECODO_USERNAME") or "").strip()
    password = (os.getenv("DECODO_PASSWORD") or "").strip()
    if not username or not password:
        token_user, token_password = _read_token()
        username = username or token_user
        password = password or token_password

    if require_decodo and (not username or not password):
        raise ValueError("Faltan credenciales Decodo. Configura DECODO_USERNAME/DECODO_PASSWORD o DECODO_TOKEN en .env")

    sqlite_env = (os.getenv("SQLITE_PATH") or "./data/booking-prices.sqlite").strip()
    sqlite_path = Path(sqlite_env)
    if not sqlite_path.is_absolute():
        sqlite_path = ROOT / sqlite_path

    return AppSettings(
        decodo=DecodoSettings(
            username=username,
            password=password,
            api_url=(os.getenv("DECODO_API_URL") or DEFAULT_DECODO_API_URL).strip(),
            locale=(os.getenv("DECODO_LOCALE") or "es-es").strip() or None,
            geo=(os.getenv("DECODO_GEO") or "Spain").strip() or None,
            proxy_pool=(os.getenv("DECODO_PROXY_POOL") or "premium").strip() or None,
        ),
        sqlite_path=sqlite_path,
    )
