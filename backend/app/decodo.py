from __future__ import annotations

import asyncio
import base64
from typing import Any

import httpx

from .config import DecodoSettings


class DecodoClient:
    def __init__(self, settings: DecodoSettings) -> None:
        self.settings = settings

    async def scrape_html(self, url: str) -> str:
        payloads: list[dict[str, Any]] = [
            {"target": "universal", "url": url, "headless": "html", "locale": self.settings.locale, "geo": self.settings.geo, "device_type": "desktop", "proxy_pool": self.settings.proxy_pool},
            {"target": "universal", "url": url, "locale": self.settings.locale, "geo": self.settings.geo, "device_type": "desktop", "proxy_pool": self.settings.proxy_pool},
            {"url": url, "headless": "html", "locale": self.settings.locale, "geo": self.settings.geo, "device_type": "desktop", "proxy_pool": self.settings.proxy_pool},
            {"url": url, "locale": self.settings.locale, "geo": self.settings.geo, "device_type": "desktop", "proxy_pool": self.settings.proxy_pool},
        ]
        payloads = [{k: v for k, v in payload.items() if v not in (None, "")} for payload in payloads]

        last_error: Exception | None = None
        for index, payload in enumerate(payloads):
            try:
                return await self._execute(payload)
            except Exception as exc:  # noqa: BLE001 - preserve upstream context for operators
                last_error = exc
                if index == 0:
                    print(f"[decodo] Fallback sin render JS para {url}. Motivo: {exc}")
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

        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")

        data = response.json()
        result = (data.get("results") or [None])[0]
        if not result:
            raise RuntimeError("La respuesta de Decodo no incluye results[0]")

        content = result.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            return str(content)
        raise RuntimeError("La respuesta de Decodo no incluye contenido HTML usable")
