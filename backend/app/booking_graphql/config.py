"""Constantes del motor de scraping GraphQL, compartidas por el CLI
(`booking.py`, en la raíz del proyecto) y por el backend web.

Cambiar aquí afecta a ambos consumidores: es la única fuente de verdad.
"""

from __future__ import annotations

# Divisa en la que se piden TODOS los precios. Clavarla es imprescindible para
# revenue: si no, Booking la elige por geo/IP/sesión y las series no son
# comparables entre ejecuciones. Se fuerza vía `selected_currency` al cargar
# la página inicial (queda en cookie de sesión y la hereda el GraphQL).
MONEDA = "EUR"

RESULTS_PER_PAGE = 25          # Booking siempre pagina de 25 en 25
MAX_CONCURRENT_REQUESTS = 3    # no subir mucho: cuantas más peticiones en
                                # paralelo, más fácil que te bloqueen
DELAY_BETWEEN_REQUESTS = (0.8, 2.2)  # segundos, rango aleatorio (min, max)
MAX_RETRIES = 3
