from __future__ import annotations

import asyncio
import base64
from typing import Any

import httpx

from .config import DecodoSettings

# Target HTTP statuses we consider a successful Booking fetch.
_SUCCESS_STATUS = [200]
# Extra attempts (per payload variant) on transient failures before moving on.
_MAX_RETRIES = 2
# Markers that betray a block / CAPTCHA / "are you human" interstitial.
_BLOCK_MARKERS = ("captcha", "are you a robot", "/sorry/", "access denied", "px-captcha", "unusual traffic")


class TransientDecodoError(Exception):
    """Retryable failure: rate limit, 5xx, or a soft block from the target."""


class DecodoClient:
    def __init__(self, settings: DecodoSettings) -> None:
        self.settings = settings

    async def scrape_html(self, url: str, *, session_id: str | None = None) -> str:
        base: dict[str, Any] = {
            "locale": self.settings.locale,
            "geo": self.settings.geo,
            "device_type": "desktop",
            "proxy_pool": self.settings.proxy_pool,
            "successful_status_codes": _SUCCESS_STATUS,
            "session_id": session_id,
        }
        render = {"target": "universal", "url": url, "headless": "html", **base}
        render_no_target = {"url": url, "headless": "html", **base}
        plain = {"target": "universal", "url": url, **base}
        plain_no_target = {"url": url, **base}
        if self.settings.render_js:
            payloads: list[dict[str, Any]] = [render, plain, render_no_target, plain_no_target]
        else:
            # Cheaper/faster: try without JS rendering first, escalate to headless only if needed.
            payloads = [plain, plain_no_target, render, render_no_target]
        payloads = [{k: v for k, v in payload.items() if v not in (None, "")} for payload in payloads]

        last_error: Exception | None = None
        for index, payload in enumerate(payloads):
            for attempt in range(_MAX_RETRIES + 1):
                try:
                    return await self._execute(payload)
                except TransientDecodoError as exc:
                    last_error = exc
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(0.4 * (attempt + 1))  # linear backoff
                        continue
                    break
                except Exception as exc:  # noqa: BLE001 - preserve upstream context for operators
                    last_error = exc
                    break
            if index == 0:
                print(f"[decodo] Variante alternativa para {url}. Motivo: {last_error}")
                await asyncio.sleep(0.25)

        raise RuntimeError(f"No se pudo obtener HTML de Decodo. Ultimo error: {last_error}")

    async def _execute(self, payload: dict[str, Any]) -> str:
        token = base64.b64encode(f"{self.settings.username}:{self.settings.password}".encode()).decode()
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                self.settings.api_url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Basic {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        # Decodo-level transport errors: rate limit / server errors are retryable.
        if response.status_code == 429 or response.status_code >= 500:
            raise TransientDecodoError(f"HTTP {response.status_code}: {response.text[:200]}")
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")

        data = response.json()
        result = (data.get("results") or [None])[0]
        if not result:
            raise RuntimeError("La respuesta de Decodo no incluye results[0]")

        # Target-level status: Booking may serve a block/CAPTCHA page while Decodo itself returns 200.
        target_status = result.get("status_code")
        if isinstance(target_status, int) and target_status >= 400:
            raise TransientDecodoError(f"Booking devolvio HTTP {target_status} (posible bloqueo)")

        content = result.get("content")
        if isinstance(content, dict):
            content = str(content)
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("La respuesta de Decodo no incluye contenido HTML usable")

        # A genuine results page is large; a short page containing block markers is an interstitial.
        if len(content) < 1500 and any(marker in content[:4000].lower() for marker in _BLOCK_MARKERS):
            raise TransientDecodoError("Pagina de bloqueo/CAPTCHA detectada")

        return content
