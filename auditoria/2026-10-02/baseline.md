# Línea base · 2026-10-02 · rama pulido/auditoria · commit 4105fb1 (+2 fix mocks/puertos sin commitear)

Datos: copia `artifacts/pulido/db/trabajo.sqlite` (run 26, captura F0.5). Servidor :5060 (claves en blanco), prototipo :8001.

## Versiones

pytest 9.1.1 · node v23.10.0 · playwright (chromium bundled) · nota: Chromium bloquea el puerto 5060 (SIP, `ERR_UNSAFE_PORT`); los 9 scripts e2e usan `--explicitly-allowed-ports=5050,5060,5061,5070,8001`.

## Tests

- pytest: **242/242** en verde (2,4 s; base temporal propia).
- node: **31/31** en verde, 0 fallos.

## e2e (10 vistas × 6 anchos × 2 temas, densidad equilibrada)

- 120 capturas en `artifacts/visual-qa/pulido/baseline/`.
- Desbordes a 768 px (hallazgo U1): dashboard 42 px, resto de vistas y workspace 105 px (detallar en informe u1).
- Workspace no pintaba: `POST /api/analytics/query` (solo lectura) bloqueado por mocks → añadido a la lista blanca (mocks.py). Verificado OK salvo 768.
- `qa_*`: bi 32/32 · copilot 20/20 · dashboard 38/38 · reputation 29/29 (el 404 era `GET /api/jobs/qa-rev` llegando al backend; los mocks ya responden canned a rutas conocidas) · workspace 17/17 · a11y (`qa_a11y.txt`): 0 controles sin nombre en las 10 vistas; objetivos <24 px: 96 = 34 puntos del enjambre (16×16) + 61 pines de mapa BI (13–19 px) + 1 buscador de hoteles (alto 16); resto de vistas 0 · flights: aborta en sitios que tocan endpoints de pago bloqueados por diseño (`air-data/capture`, `booking-options`) → G1 adapta la QA a mocks estrictos en F1.

## perf.py (4× CPU + Fast 3G, mediana de 5)

| Vista | FCP | LCP | Bytes | Recursos |
| --- | --- | --- | --- | --- |
| dashboard | 3040 | 0 | 675231 | 15 |
| hotels | 3044 | 0 | 681571 | 14 |
| reputation | 3040 | 0 | 675132 | 12 |
| flights | 3048 | 0 | 685498 | 14 |
| copilot | 3048 | 0 | 672666 | 16 |
| workspace | 3044 | 0 | 669530 | 14 |
| captures | 3044 | 0 | 678918 | 14 |

Raro: LCP 0 en todas (B1 revisa la medición en F1). FCP ~3 s bajo throttling.

## Recursos

- `atlas.js` 426753 B (gzip 117721) · `atlas.css` 179950 B (gzip 29183) · total 606703 B.
- Terceros que bloquean el pintado: 2 (maplibre-gl.css unpkg + Google Fonts).
