from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECODO_API_URL = "https://scraper-api.decodo.com/v2/scrape"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-5.6-luna"
DEFAULT_OPENROUTER_FAST_MODEL = "openai/gpt-5.6-luna"
DEFAULT_OPENROUTER_HOTEL_MODEL = "minimax/minimax-m3"
DEFAULT_OPENROUTER_AIR_MODEL = "z-ai/glm-5.3-flash"
DEFAULT_OPENROUTER_CRITIC_MODEL = "google/gemini-3.8-flash"
DEFAULT_OPENROUTER_SYNTHESIS_MODEL = "deepseek/deepseek-v4-pro-0813"

# These were the expensive candidates from the previous pilot. They remain
# accepted by historical telemetry, but may not be selected for new work.
EXCLUDED_COPILOT_MODELS = frozenset({
    "openai/gpt-5.6-sol",
    "openai/gpt-6-astra",
    "anthropic/claude-sonnet-5",
    "openai/gpt-5.6-terra",
})


def _copilot_model_env(name: str, default: str) -> str:
    """Read a model override while preventing retired expensive defaults."""
    value = (os.getenv(name) or default).strip() or default
    return default if value in EXCLUDED_COPILOT_MODELS else value


def safe_copilot_model(value: str | None, fallback: str) -> str:
    """Keep worker-created settings from reactivating a retired model slug."""
    candidate = (value or "").strip()
    return fallback if not candidate or candidate in EXCLUDED_COPILOT_MODELS else candidate


@dataclass(frozen=True)
class DecodoSettings:
    username: str
    password: str
    api_url: str
    locale: str | None = "es-es"
    geo: str | None = "Spain"
    proxy_pool: str | None = "premium"
    # When False, try the cheaper non-JS-render request first (Booking search is server-rendered).
    render_js: bool = True


@dataclass(frozen=True)
class OpenRouterSettings:
    api_key: str
    model: str
    base_url: str
    fast_model: str = DEFAULT_OPENROUTER_FAST_MODEL
    hotel_model: str = DEFAULT_OPENROUTER_HOTEL_MODEL
    air_model: str = DEFAULT_OPENROUTER_AIR_MODEL
    air_fallback_model: str = DEFAULT_OPENROUTER_FAST_MODEL
    critic_model: str = DEFAULT_OPENROUTER_CRITIC_MODEL
    synthesis_model: str = DEFAULT_OPENROUTER_SYNTHESIS_MODEL
    moa_enabled: bool = True
    # Explicit provider privacy policy. ``deny`` requires a compatible
    # zero-retention endpoint; ``allow`` is an intentional deployment choice.
    data_collection: str = "deny"
    # Ask OpenRouter for a zero-data-retention endpoint when available.  The
    # loader below derives a safe default from ``data_collection``: an
    # explicit ``allow`` policy opts into provider retention, so enabling ZDR
    # implicitly would unnecessarily eliminate compatible endpoints.  Set
    # OPENROUTER_ZDR=true when ZDR is required for a deployment.
    zdr: bool = True

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


@dataclass(frozen=True)
class AppSettings:
    decodo: DecodoSettings
    sqlite_path: Path
    database_provider: str
    database_url: str | None
    openrouter: OpenRouterSettings
    scraper_backend: str
    environment: str
    auth_password: str
    auth_user: str
    session_secret: str
    copilot_requests_per_minute: int
    copilot_audit_retention_days: int
    copilot_monthly_budget_usd: float
    copilot_task_budget_usd: float

    @property
    def auth_required(self) -> bool:
        return self.environment == "production"


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


def _bounded_env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser numérico") from exc
    return max(minimum, min(value, maximum))


def _bounded_env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser numérico") from exc
    return max(minimum, min(value, maximum))


def _env_bool(name: str, default: bool) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw not in {"false", "0", "no", "off"}


# B2-10: una sola lectura de `.env` por proceso. `load_settings` se llama
# por petición (`market_service`); con `override=False` y este guardián el
# fichero solo se lee una vez y el entorno real siempre prevalece.
_CONFIG_ENV_LOADED = False


def _ensure_dotenv_once() -> None:
    global _CONFIG_ENV_LOADED
    if _CONFIG_ENV_LOADED:
        return
    try:
        load_dotenv(ROOT / ".env", override=False)
    except Exception:
        pass
    _CONFIG_ENV_LOADED = True


def load_settings(require_decodo: bool = False) -> AppSettings:
    _ensure_dotenv_once()

    # Motor de extracción por defecto: GraphQL interno de Booking (ver
    # backend/app/booking_graphql/), más estable y con mucha más señal que
    # el HTML vía proxy. Decodo se mantiene en el repo como alternativa
    # (backend/app/decodo.py) pero ya no es la vía por defecto.
    scraper_backend = (os.getenv("SCRAPER_BACKEND") or "graphql").strip().lower()
    if scraper_backend not in {"graphql", "decodo"}:
        raise ValueError("SCRAPER_BACKEND debe ser 'graphql' o 'decodo'")

    environment = (os.getenv("APP_ENV") or "development").strip().lower()
    if environment not in {"development", "test", "production"}:
        raise ValueError("APP_ENV debe ser development, test o production")
    auth_password = (os.getenv("APP_AUTH_PASSWORD") or "").strip()
    auth_user = (os.getenv("APP_AUTH_USER") or "revenue-admin").strip()[:80] or "revenue-admin"
    session_secret = (os.getenv("FLASK_SECRET_KEY") or "").strip()
    if environment == "production" and (not auth_password or not session_secret):
        raise ValueError("En producción configura APP_AUTH_PASSWORD y FLASK_SECRET_KEY")

    username = (os.getenv("DECODO_USERNAME") or "").strip()
    password = (os.getenv("DECODO_PASSWORD") or "").strip()
    if not username or not password:
        token_user, token_password = _read_token()
        username = username or token_user
        password = password or token_password

    # Las credenciales de Decodo solo son obligatorias si de verdad se va a
    # usar ese backend; con el backend graphql (por defecto) no hacen falta.
    if require_decodo and scraper_backend == "decodo" and (not username or not password):
        raise ValueError("Faltan credenciales Decodo. Configura DECODO_USERNAME/DECODO_PASSWORD o DECODO_TOKEN en .env")

    sqlite_env = (os.getenv("SQLITE_PATH") or "./data/booking-prices.sqlite").strip()
    sqlite_path = Path(sqlite_env)
    if not sqlite_path.is_absolute():
        sqlite_path = ROOT / sqlite_path
    database_provider = (os.getenv("DATABASE_PROVIDER") or "sqlite").strip().lower()
    database_url = (os.getenv("DATABASE_URL") or "").strip() or None
    if database_provider not in {"sqlite", "postgres"}:
        raise ValueError("DATABASE_PROVIDER debe ser 'sqlite' o 'postgres'")
    if database_provider == "postgres" and not database_url:
        raise ValueError("DATABASE_URL es obligatorio cuando DATABASE_PROVIDER=postgres")

    return AppSettings(
        decodo=DecodoSettings(
            username=username,
            password=password,
            api_url=(os.getenv("DECODO_API_URL") or DEFAULT_DECODO_API_URL).strip(),
            locale=(os.getenv("DECODO_LOCALE") or "es-es").strip() or None,
            geo=(os.getenv("DECODO_GEO") or "Spain").strip() or None,
            proxy_pool=(os.getenv("DECODO_PROXY_POOL") or "premium").strip() or None,
            render_js=(os.getenv("DECODO_RENDER", "true").strip().lower() not in {"false", "0", "no", "off"}),
        ),
        sqlite_path=sqlite_path,
        database_provider=database_provider,
        database_url=database_url,
        scraper_backend=scraper_backend,
        environment=environment,
        auth_password=auth_password,
        auth_user=auth_user,
        session_secret=session_secret,
        copilot_requests_per_minute=_bounded_env_int(
            "COPILOT_REQUESTS_PER_MINUTE", 20, minimum=1, maximum=120
        ),
        copilot_audit_retention_days=_bounded_env_int(
            "COPILOT_AUDIT_RETENTION_DAYS", 90, minimum=1, maximum=3650
        ),
        copilot_monthly_budget_usd=_bounded_env_float("COPILOT_MONTHLY_BUDGET_USD", 50.0, minimum=0.0, maximum=100000.0),
        copilot_task_budget_usd=_bounded_env_float("COPILOT_TASK_BUDGET_USD", 2.0, minimum=0.0, maximum=1000.0),
        openrouter=OpenRouterSettings(
            api_key=(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY") or "").strip(),
            model=_copilot_model_env("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
            base_url=(os.getenv("OPENROUTER_BASE_URL") or DEFAULT_OPENROUTER_BASE_URL).strip().rstrip("/") or DEFAULT_OPENROUTER_BASE_URL,
            fast_model=_copilot_model_env("OPENROUTER_FAST_MODEL", DEFAULT_OPENROUTER_FAST_MODEL),
            hotel_model=_copilot_model_env("OPENROUTER_HOTEL_MODEL", DEFAULT_OPENROUTER_HOTEL_MODEL),
            air_model=_copilot_model_env("OPENROUTER_AIR_MODEL", DEFAULT_OPENROUTER_AIR_MODEL),
            air_fallback_model=_copilot_model_env("OPENROUTER_AIR_FALLBACK_MODEL", DEFAULT_OPENROUTER_FAST_MODEL),
            critic_model=_copilot_model_env("OPENROUTER_CRITIC_MODEL", DEFAULT_OPENROUTER_CRITIC_MODEL),
            synthesis_model=_copilot_model_env("OPENROUTER_SYNTHESIS_MODEL", DEFAULT_OPENROUTER_SYNTHESIS_MODEL),
            moa_enabled=(os.getenv("COPILOT_MOA_ENABLED", "true").strip().lower() not in {"false", "0", "no", "off"}),
            data_collection=(os.getenv("OPENROUTER_DATA_COLLECTION") or "deny").strip().lower() if (os.getenv("OPENROUTER_DATA_COLLECTION") or "deny").strip().lower() in {"deny", "allow"} else "deny",
            # Keep the privacy choice explicit.  With ``allow`` the default
            # is no ZDR restriction; with ``deny`` we keep the stricter
            # zero-retention routing unless the deployment overrides it.
            zdr=_env_bool(
                "OPENROUTER_ZDR",
                ((os.getenv("OPENROUTER_DATA_COLLECTION") or "deny").strip().lower() != "allow"),
            ),
        ),
    )
