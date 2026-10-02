#!/usr/bin/env python3
"""Saldos de proveedores. Imprime SOLO cifras, nunca claves ni emails.

- OpenRouter: GET https://openrouter.ai/api/v1/key con Authorization: Bearer <OPENROUTER_API_KEY>
- SerpAPI: https://serpapi.com/account.json?api_key=<SERPAPI_API_KEY> (solo plan/credits).
Uso: OPENROUTER_API_KEY=… SERPAPI_API_KEY=… python3 gasto.py
"""
import json
import os
import urllib.request


def get_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main() -> int:
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    serp_key = os.environ.get("SERPAPI_API_KEY", "")
    if or_key:
        try:
            d = get_json("https://openrouter.ai/api/v1/key",
                         {"Authorization": f"Bearer {or_key}"})["data"]
            print(f"openrouter limite={d.get('limit')} uso={d.get('usage')}")
        except Exception as e:  # noqa: BLE001 - solo clase de error, sin secreto
            print(f"openrouter ERROR {type(e).__name__}")
    else:
        print("openrouter sin clave")
    if serp_key:
        try:
            a = get_json(f"https://serpapi.com/account.json?api_key={serp_key}")
            print(f"serpapi plan={a.get('plan_name')} busquedas_mes={a.get('this_month_usage')}")
        except Exception as e:  # noqa: BLE001
            print(f"serpapi ERROR {type(e).__name__}")
    else:
        print("serpapi sin clave")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
