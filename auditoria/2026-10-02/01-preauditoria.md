# 01-Preauditoría · Pulido Atlas (semillas a confirmar, no hechos)

## Mediciones en vivo (02-10-2026)

- Estáticos sin comprimir: `atlas.js` 427 KB + `atlas.css` 180 KB = 607 KB. gzip → 148 KB (−76 %); brotli → 118 KB (−80 %). API `/api/air-data` 138 KB → 16 KB (ya comprimida).
- Caliente: TTFB 12 ms; 6 llamadas de arranque en paralelo <75 ms. Cambios de vista 26–80 ms, sin tareas largas. Backend <30 ms con datos actuales.
- DOM 1.100 → 5.300 nodos (aceptado 28-09). 1024/768 px: 0 desbordes de página; sidebar a 68 px.

## Semillas por agente

Seguridad (I1+B2, oleada 1): PA-97 fuga SerpAPI en URL (`serpapi_flights.py:91-94`, `str(exc)[:500]` en `flask_app.py` ≈2145 → base/API/UI) · PA-81 worker (`test_request_context` salta rate-limit/auth/mercado; idempotencia sin propietario; herramientas sin mercado; contexto es dato; `history` del cliente; Jev en `/tmp` con env+secretos; `TYPESAFE_API_KEY`) · PA-54 `enforce_market_access` solo mira `targetId` (`/api/photos/<id>`, `/api/hotels/inventory` lo saltan) · PA-98 `:5012` comparte `background_jobs` (`claim_next_job`, `recover_stale_jobs` 900 s).

- I1: PA-80 costes (`usage` sobrescrito, sin `usage.include`, `requestId` liquidado salta reserva, reservas atascadas, `--purge-audit` borra gasto, reseñas/Jev fuera de presupuesto, exceso reseñas descartado, Jev sin gasto real) · PA-82 calidad (`responseQuality` solo avisa, cifras sin verificar, `web_search` con hoy/actual/tiempo, desfase modelos `.env.example`, adjuntos sin OCR en claro) · PA-83 latencia (chat >60 s sin streaming, MoA 12+12 s, `comparable_snapshot` 120 cargas) · PA-84 harness (gratis vs `--live --case` pago; añadir inyección y cifras-vs-evidencia) · PA-85 tests sin cubrir.
- B1: PA-01 compresión salta estáticos (`flask_app.py` ≈127–143, `send_file` streamed; propuesta gzip por `mtime` + `Vary` + `immutable`) · PA-02 terceros bloquean (maplibre unpkg sin SRI + Google Fonts; diferir en `loadMapLibre` o autoalojar 4.7.1) · PA-03 medir 4×CPU+Fast3G, backend 10× en copia aislada · PA-04 sin `AbortController`, `api()` (`atlas.js:52`) sin timeout · PA-05 14 `document.addEventListener` duplicados · PA-06 116 `innerHTML`, `renderWorkspace` repinta · PA-07 N+1 reseñas, `capture_history` 500 fotos, `rate_calendar` sin caché, `hotels/history` sin paginar.
- D1: PA-10 58 `style=""` · PA-11 76 hex fuera de tokens (23 paleta; `#fff` ×32, `#000` ×8) · PA-12 31 fuentes · PA-13 15 radios (tokenizar conservando README) · PA-14 glifos vs 21 SVG · PA-15 Capturas (Registro negro en claro, chips duplican mercado, eje X con índices) · PA-16 9 `!important` · PA-17 ticker vacío deja hueco.
- D2: PA-20 verde/rojo por contexto → guía · PA-21 gráficas sin alternativa, ejes sin unidad/fecha (ADR workspace) · PA-22 pocos datos parecen rotos · PA-23 AMS/LGW solapadas, pines 15–19 px, CDN, oscuro.
- U1: PA-30 `replaceState` (`atlas.js:566`) sin `popstate` · PA-31 foto/captura/extracción/barrido sinónimos · PA-32 «Failed to fetch» en bruto · PA-33 vacíos → Capturar · PA-34 tablas/mapas 768–1024 · PA-35 historial Copilot plegado a 1366, «Resultados» poco visible.
- U2: PA-40 20 duraciones/6 curvas/15 keyframes/4 `reduced-motion` · PA-41 sin salidas · PA-42 sin `aria-busy` · PA-43 roving tabindex en `tablist` · PA-44 pulsación puntos/pines · PA-45 `--faint` ~4,3:1 / `--fainter` 2,35:1 (tokens README: decisión) · PA-46 tooltips `title` · PA-47 0 `forced-colors`/`prefers-contrast`/`print`, zoom 200 %.
- W1: PA-50 `median([])`/`percentileVal([])` → 0 (`atlas.js:65-77`, también en test Node) · PA-51 fórmulas README §3B §5 · PA-52 UTC/local, cambio 25-10-2026 Atlantic/Canary · PA-53 `_build_insights` · PA-55 `nEs` («1234» vs «12.345»), `signPct` sin fino · PA-54 con B2.
- W2: PA-60 carreras al cambiar mercado · PA-61 `invalidateTargetData` vs cachés nuevas · PA-62 `localStorage` sin versión · PA-63 polls · PA-64 pestañas.
- G1: PA-70 matriz completa · PA-71 `AbortError` MapLibre · PA-72 hash no cambia vista · PA-73 30 min WebGL/polls · PA-74 base vacía.
- B2: PA-90 un hilo (Jev 30 min bloquea Copilot), sin backoff, 900 s · PA-91 `/api/scrape/*`, `/api/air-data/capture` (5000) síncronos · PA-92 SerpAPI 2×90 s + recarga `.env` · PA-93 sin logging · PA-94 sin frontera de render · PA-95 Jev `langdetect` + 2 fallos · PA-96 auth solo prod (documentar).

## Catálogo MM/MX (U2+D1+D2 validan; sutil, `transform`/`opacity`, `reduced-motion`)

MM-01 tokens movimiento (conserva 420/260/700 ms + micro 120/180/240, regla global) · MM-02 pestaña deslizante (con PA-43) · MM-03 segmentado deslizante (con PA-43) · MM-04 `scale(.98)` · MM-05 resaltado de valor (conteo solo primer pintado) · MM-06 esqueleto→contenido con altura · MM-07 salidas toast/panel/popover/selbar/paleta · MM-08 ocupado con `aria-busy` · MM-09 filas hover/selección · MM-10 flecha orden gira · MM-11 «Guardado» confirmado · MM-12 trazabilidad/detalles suave · MM-13 pines/rutas MapLibre · MM-14 filas hoja mercado · MM-15 progreso jobs. MX-01 atajos paleta · MX-02 `document.title` por vista · MX-03 scroll por vista · MX-04 `tabular-nums` · MX-05 fecha exacta en hover relativo · MX-06 toasts Esc/clic · MX-07 vacío ticker.

## Decisiones de parada 1 (todas en parada 1)

1. Dividir `atlas.js` en módulos ES (ADR B1: solo si parseo+eval >~150 ms a 4×CPU o largas >200 ms). 2. Desvíos README (contraste, fuentes, radios, duraciones). 3. Worker separado (rápida Copilot vs larga capturas). 4. MapLibre/fuentes: autoalojar o diferir+SRI. 5. `pushState` entre vistas. 6. Glosario. 7. Semántica verde/rojo. 8. Jev: excluido o Maps Servatur ≤1 € tras PA-81.

## Objetivos (vinculantes, confirmar con base F0)

Estáticos fríos 607 KB → ≤160 KB · terceros que bloquean 2→0 · arranque 4×CPU sin larga >200 ms (o justificada) · vista en caliente ≤100 ms · p95 endpoints con 10× ≤150 ms · consola 0 · controles sin nombre 0 · pulsación ≥24 px · `reduced-motion` 100 % · duraciones en tokens · `style=""` 58→0 · fuga de clave y costes corregidos contra saldo del proveedor.
