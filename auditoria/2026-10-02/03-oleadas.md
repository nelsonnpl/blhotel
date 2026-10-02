# 03-Oleadas · Pulido Atlas (paquetes PKG-xx)

Reglas F3: lote ≤3 (uno por carril FE/BE/QA), árbol quieto, BE verifica en :5061, revisor ≠ implementador, un commit por paquete `tipo(alcance): … [PKG-xx]`, regresión al cerrar oleada. Rama por oleada desde `pulido/auditoria`.

## Oleada 1 · Seguridad y base (primero P0)

| PKG | Contenido (hallazgos) | Impl | Rev | Carril | Reserva |
| --- | --- | --- | --- | --- | --- |
| PKG-01 | Redactado `api_key` SerpAPI (P0-1; punto único + `fail_job` B2-12 + logging B2-11) | B2 | I1 | BE | `backend/app/serpapi_flights.py`, `flask_app.py` (zona 2145 + `fail_job` + logging) |
| PKG-02 | 403 por mercado en `photos/<id>`, `inventory`, `price-history` (P0-2) | B2 | I1, W1 | BE | `backend/app/flask_app.py` (zonas 185-202, 891-908, 1141-46, 1182-09) + tests BE |
| PKG-03 | Worker con guardas + idempotencia por owner + `settled` no reutiliza (P0-3/4/5, I1-14 tools exigen mercado) | B2 | I1 | BE | `backend/app/flask_app.py` (worker), `database.py`, `assistant.py` (tools) + tests |
| PKG-04 | Contabilidad: `usage.include` chat + suma por rondas + purga conserva mes + reaper + exceso reseñas imputado (P0-6, I1-07/08/09) | I1 | B2 | BE | `backend/app/assistant.py`, `database.py`, `flask_app.py` (reseñas) + tests |
| PKG-05 | PKG-00 versión por `mtime` + gzip estáticos con `Vary` (B1-01) | B1 | W2 | BE | `backend/app/flask_app.py` (zona 124-143) + test |
| PKG-06 | Terceros: diferir CSS o autoalojar MapLibre 4.7.1 + fuentes con SRI (B1-03, D2-04; según decisión nº4) | B1 | W2 | FE/BE | `backend/app/templates/index.html`, `atlas.js` (`loadMapLibre`) |
| PKG-07 | `api()` timeout/cancel/reintento solo GET + `onerror`/`unhandledrejection` (B1-04, B2-13, W2-04) | W2 | G1 | FE | `backend/app/static/atlas.js` (zona `api()`, sin tocar 12-80) |
| PKG-08 | Desconocido≠0: `median`/`percentileVal`→null + ramas BE a `None` + tests Node (W1-01/02) | W1 | B2 | FE/BE | `atlas.js` (65-77 + llamantes), `database.py`, `flask_app.py`, `tests/*.cjs` |

Cierre oleada 1: regresión + captura aérea SerpAPI real (≤1 €, tras PKG-01) + Jev Maps Servatur (≤1 € colchón, tras PKG-03 y solo si se aprueba decisión nº8).

## Oleada 2 · Flujos y coherencia

| PKG | Contenido | Impl | Rev | Carril |
| --- | --- | --- | --- | --- |
| PKG-09 | Historial por vista + título + scroll (U1-01/02, MX-02/03; según decisión nº5) | W2 | G1 | FE |
| PKG-10 | Glosario + copy + vacíos→Capturar + errores homogéneos (U1-03/04/05/06/07/13-18) | U1 | D2 | FE |
| PKG-11 | Aspecto Capturas/bloqueo/paleta/diálogos/toasts (D1-07/08/09/12/14, U1-11/12) | D1 | U2 | FE |
| PKG-12 | Semántica color + leyendas/ejes/fecha + pocos-datos (D2-06/07/10/11/12/13/14/15/16/17/18) | D2 | U1 | FE |
| PKG-13 | 768–1024 + topbar + breakpoint (U1-08/09/10, D1-11, G1-13) | U1 | D2 | FE |
| PKG-14 | es-ES + fechas/DST + insights (W1-05/06/07/08/09) | W1 | B2 | FE/BE |

## Oleada 3 · Sistema visual y micro-interacciones

| PKG | Contenido | Impl | Rev | Carril |
| --- | --- | --- | --- | --- |
| PKG-15 | Tokens (conservando README) + 58 `style`→clases + hex→tokens (D1-01/02/03/04/06) | D1 | U2 | FE |
| PKG-16 | Movimiento: tokens + `reduced-motion` + salidas + `aria-busy` + MM/MX aceptadas (U2-01/02/03/11/12, MM-01/03/04/06/07/08/09/10/11/12/14/15, MX-01/04/06/07) | U2 | D1 | FE |
| PKG-17 | PA-43 roving + MM-02 + segmentado + iconos SVG + `tabular-nums` (D1-05/13, U2-08/09/10) | D1 | U2 | FE |
| PKG-18 | Mapas: pines/dianas + etiquetas + `fl-dot` + `title`→accesibles (D2-01/02/03, U2-04/05/13, PA-44) | D2 | U1 | FE |
| PKG-19 | Contraste + forced-colors/print + calendario teclado + `role=img` alternativas (U2-06/07/15, D2-08/09, G1-08/09; según decisión nº2) | U2 | D1 | FE |

## Oleada 4 · IA

| PKG | Contenido | Impl | Rev | Carril |
| --- | --- | --- | --- | --- |
| PKG-20 | Verificación cifras vs evidencia + `responseQuality` accionable (I1-16) | I1 | B2 | BE |
| PKG-21 | Trigger `web_search` + desfase modelos + adjuntos (I1-17/18/22, I1-15 permisos) | I1 | B2 | BE |
| PKG-22 | Progreso/streaming MoA + `comparable` sin N+1 (I1-19, B1) | I1 | B2 | BE |
| PKG-23 | `history` forjado + Jev `/tmp`/env/`TYPESAFE` + Jev gasto visible (I1-11/12/13/10) | I1 | B2 | BE |

## Oleada 5 · Robustez y escala

| PKG | Contenido | Impl | Rev | Carril |
| --- | --- | --- | --- | --- |
| PKG-24 | N+1 + `capture_history` + caché `comparable` + paginar `history` + índices + `rate_calendar` caché (B1-07/08/09/10, I1-19) | B1 | W2 | BE |
| PKG-25 | Logging redactado + dotenv SerpAPI + endpoints síncronos + reintentos/cancel (B2-09/10/11/16/17, W2-11/12/13) | B2 | I1 | BE |
| PKG-26 | Worker separado (rápida Copilot vs larga capturas) + `recover_stale` 900 s (B2-07/08; según decisión nº3) | B2 | I1 | BE |
| PKG-27 | Tests P0/P1 + `qa_flights` con bloqueos esperados + matriz G1 (I1-21, B2-19, G1-14/21) | G1 | W2 | QA |
