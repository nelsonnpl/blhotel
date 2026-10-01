"""Creación de un contexto de navegador Playwright con huella coherente y
stealth ligero, para pasar el anti-bot (PerimeterX) de Booking."""

from __future__ import annotations

import platform

_UA_PLATFORM = {
    "Darwin": "Macintosh; Intel Mac OS X 10_15_7",
    "Windows": "Windows NT 10.0; Win64; x64",
    "Linux": "X11; Linux x86_64",
}

# Script de stealth ligero: borra las señales más obvias de automatización
# que PerimeterX (el anti-bot de Booking) comprueba. No es infalible, pero
# elimina los tells triviales (navigator.webdriver, etc.).
_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
"""


async def new_context(browser, lang: str):
    """Crea un contexto de navegador con una huella COHERENTE.

    El bug anterior: el user-agent decía 'Windows Chrome/124' mientras el
    motor real era otra versión y otro SO -> huella inconsistente, fácil de
    detectar. Aquí construimos el UA a partir de la versión REAL de Chromium
    que trae Playwright y del SO REAL en el que corre, y aplicamos headers y
    stealth acordes.
    """
    version = (browser.version or "124.0.0.0").split()[-1]
    plat_token = _UA_PLATFORM.get(platform.system(), _UA_PLATFORM["Windows"])
    user_agent = (
        f"Mozilla/5.0 ({plat_token}) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{version} Safari/537.36"
    )
    accept_language = f"{lang}-{lang.upper()},{lang};q=0.9,en;q=0.8"
    context = await browser.new_context(
        locale=lang,
        user_agent=user_agent,
        extra_http_headers={"accept-language": accept_language},
    )
    await context.add_init_script(_STEALTH_JS)
    return context
