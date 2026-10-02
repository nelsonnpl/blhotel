"""B2-09: logging central con redactado (sin secretos).

Punto único para que ningún secreto (SerpAPI, OpenRouter, Decodo,
sesión/auth, DATABASE_URL) salga del proceso en logs, errores
persistidos o respuestas. El placeholder evita a propósito la
subcadena `api_key` para que `rg api_key` no dé positivos en salidas
redactadas.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any

PLACEHOLDER = "[clave oculta]"

# Patrones genéricos (nunca incluyen el secreto en el placeholder).
_PATTERNS: list[re.Pattern[str]] = [
    # ?api_key=SECRETO, api_key: SECRETO, "api_key": "SECRETO", %3D/%253D.
    re.compile(
        r"(?i)[\"']?api[_-]?key[\"']?\s*(?:[:=]|%3D|%253D)\s*[\"']?[^\s&'\"`}\],;]+[\"']?"
    ),
    # Claves nombradas por proveedor.
    re.compile(
        r"(?i)(?:serpapi|serp_api|openrouter|typesafe|decodo)[_-]?(?:api[_-]?key|token)"
        r"\s*[:=]\s*[^\s&'\"`}\],;]+"
    ),
    # Credenciales operativas con nombre explícito.
    re.compile(
        r"(?i)(?:decodo[_-]?(?:password|user)|app[_-]?auth[_-]?password|"
        r"flask[_-]?secret[_-]?key|copilot[_-]?requests)[_-]?\s*[:=]\s*[^\s&'\"`}\],;]+"
    ),
    # Esquemas de autorización.
    re.compile(r"(?i)Basic\s+[A-Za-z0-9+/_-]+=*"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/_-]+=*"),
    # password=... / passwd: ... genérico.
    re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*[^\s&'\"`}\],;]+"),
    # DATABASE_URL con credenciales embebidas: ://user:pass@.
    re.compile(r"(?i)(://[^/:?\s]+:)[^@?\s]+(@)"),
]

# Nombres de entorno cuyos valores literales nunca deben salir en logs.
_LITERAL_ENV_KEYS = (
    "SERPAPI_API_KEY",
    "SERP_API_KEY",
    "OPENROUTER_API_KEY",
    "OPENROUTER_KEY",
    "TYPESAFE_API_KEY",
    "DECODO_PASSWORD",
    "DECODO_TOKEN",
    "DECODO_BASIC_AUTH_TOKEN",
    "DECODO_USERNAME",
    "APP_AUTH_PASSWORD",
    "FLASK_SECRET_KEY",
    "DATABASE_URL",
)


def _literal_secrets(extra: tuple[str, ...] = ()) -> list[str]:
    secrets: list[str] = []
    for key in _LITERAL_ENV_KEYS:
        try:
            value = os.getenv(key) or ""
        except Exception:
            value = ""
        value = value.strip().strip("\"'")
        if len(value) >= 4:
            secrets.append(value)
            # También la forma Basic-decoded "user:pass" si es un token Basic.
            if key in {"DECODO_TOKEN", "DECODO_BASIC_AUTH_TOKEN"}:
                normalized = value.removeprefix("Basic ").strip()
                if normalized and normalized != value and len(normalized) >= 4:
                    secrets.append(normalized)
    for value in extra:
        candidate = str(value or "").strip()
        if len(candidate) >= 4:
            secrets.append(candidate)
    # Los más largos primero para no dejar restos parciales.
    return sorted(set(secrets), key=len, reverse=True)


def redact_text(value: Any, extra_secrets: tuple[str, ...] = ()) -> str:
    """Devuelve `value` como texto sin secretos ni pares `api_key=`."""
    text = "" if value is None else value if isinstance(value, str) else str(value)
    for pattern in _PATTERNS:
        text = pattern.sub(PLACEHOLDER, text)
    for secret in _literal_secrets(extra_secrets):
        if secret in text:
            text = text.replace(secret, PLACEHOLDER)
    return text


class SecretRedactFilter(logging.Filter):
    """Filtro central B2-09: redacta msg/args/exc antes de emitir."""

    def __init__(self, extra_secrets: tuple[str, ...] = ()) -> None:
        super().__init__()
        self.extra_secrets = tuple(extra_secrets)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_text(record.msg, self.extra_secrets)
            if isinstance(record.args, tuple):
                record.args = tuple(
                    redact_text(arg, self.extra_secrets) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    key: redact_text(val, self.extra_secrets) if isinstance(val, str) else val
                    for key, val in record.args.items()
                }
            exc_info = getattr(record, "exc_info", None)
            if exc_info and len(exc_info) == 3 and exc_info[1] is not None:
                exc = exc_info[1]
                try:
                    redacted = redact_text(str(exc), self.extra_secrets)
                    if redacted != str(exc):
                        if getattr(exc, "args", None):
                            exc.args = (redacted,) + tuple(exc.args[1:])  # type: ignore[union-attr]
                        else:
                            exc.args = (redacted,)
                        if hasattr(exc, "_message"):
                            try:
                                exc._message = redacted  # type: ignore[attr-defined]
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass
        return True


_INSTALLED_LOGGERS: set[str] = set()


def install_secret_redact_filter(
    logger_names: tuple[str, ...] = ("", "backend.app.jobs"),
    extra_secrets: tuple[str, ...] = (),
) -> SecretRedactFilter:
    """Instala el filtro una sola vez por logger (idempotente)."""
    filt = SecretRedactFilter(extra_secrets)
    for name in logger_names:
        if name in _INSTALLED_LOGGERS:
            continue
        target = logging.getLogger(name)
        if not any(isinstance(item, SecretRedactFilter) for item in target.filters):
            target.addFilter(filt)
        _INSTALLED_LOGGERS.add(name)
    return filt


def redact_fail_job_error(error: str | None, extra_secrets: tuple[str, ...] = ()) -> str:
    """Redacta el error persistido por `Database.fail_job` (B2-12)."""
    return redact_text(error or "", extra_secrets)
