# 02-Backlog · Pulido Atlas (consolidado F2 desde los 10 índices)

Duplicados eliminados. Reproducido en vivo = W1/G1 (FE/mercados) y B2 (BE/seguridad). F1B: Copilot real ≈0,0065 € (quick 0,00043, análisis 0,0036–0,0040, GLM agota tiempo a coste 0); reseñas Servatur FAILED («sin JSON estructurado») con coste real 0,0076 €. Total ≈0,014 €.

## P0 (datos, seguridad, gasto) → oleada 1

| ID | Hallazgo | Esf | Carril | Evidencia |
| --- | --- | --- | --- | --- |
| P0-1 | PA-97 fuga SerpAPI en URL + `str(exc)` a base/API/UI/logs (I1-02/B2-01, repro B2 en copia, gasto 0) | S | BE | `serpapi_flights.py:91-94`, `flask_app.py:2145`, `atlas.js:3346-47` |
| P0-2 | PA-54 bypass mercado `photos/<id>`+`inventory` (+`price-history`) (I1-01/B2-02/W1-11/G1-01, repro W1+G1 vivo) | M | BE | `flask_app.py:185-202` vs `:1141-46`, `:1182-09` |
| P0-3 | PA-81 worker salta rate-limit/auth/mercado (I1-03/B2-03) | M | BE | `flask_app.py:2586-606` vs `:159-202` |
| P0-4 | Idempotencia sin propietario (I1-04/B2-05) | S | BE | `database.py:4734-39` |
| P0-5 | `requestId` liquidado salta reserva (I1-05/B2-06) | S | BE | `database.py:2030-36` |
| P0-6 | Chat sin `usage.include` (coste 0) + reseñas/Jev fuera de presupuesto (I1-06) | M | BE | `assistant.py:1268-86` vs `flask_app.py:2504` |
| P0-7 | PA-98 `:5012` compartía jobs → **resuelto** (parada y matada con autorización F0.4B) | S | — | registro F0.4–F0.5 |

## P1 (flujo bloqueado, dato erróneo, regresión)

FE: historial sin `pushState` (U1-01/G1-02/W2-14, S) · `median([])`→0 + 3 convenciones de vacío (W1-01/02/G1-03, S) · carreras captures/reputation/dataPromises (W2-01/02/05/G1-04/05/06, S) · doble pestaña sin lock (W2-10/G1-07, M) · 7 `role=img` sin alternativa (D2-08/G1-08, M) · calendario sin teclado (D2-09/G1-09, S) · 96 objetivos <24px (U2-04/G1-10, M) · contraste `--faint/--fainter` (U2-06/G1-11, S, decisión) · unpkg sin SRI (D2-04/G1-12, M) · `hotels/history` 449 KB sin paginar (B1-08, M).
BE: `usage` sobrescrito por ronda (I1-07, S) · purga borra mes + reservas sin reaper (I1-08/B2-06, S) · exceso reseñas sin imputar (I1-09, S) · Jev sin liquidar (I1-10, S) · `history` forjable (I1-11, S) · Jev `/tmp`+env (I1-12, M) · `TYPESAFE_API_KEY` global (I1-13, S) · tools sin mercado (I1-14, S) · adjuntos en claro (I1-15, M) · un hilo FIFO (B2-07, M) · `recover_stale` 900 s (B2-08, S) · endpoints síncronos 5000 (B2-09, M) · logging sin redactar (B2-11, S) · `fail_job` sin redactar (B2-12, S).

## P2 (fricción, lentitud medida, inconsistencia)

FE: 58 `style` estáticos (D1-01, M) · 76 hex (D1-02, M) · iconos mixtos (D1-05, S) · Capturas (D1-07/08/09) · ticker hueco (D1-10/MX-07) · topbar 768 (D1-11) · bloqueo (D1-12) · `tabular-nums` (D1-13/MX-04) · 768 sistémico 28–105 px (U1-08/09/10/G1-13, M) · glosario (U1-03, M) · `Failed to fetch` (U1-05/06/G1-18, S) · vacíos sin CTA (U1-07, M) · Copilot plegado/`Resultados` (U1-11/12) · semántica color (D2-14/15/16) · ejes/leyendas (D2-06/07/10/11/17/18) · pocos-datos (D2-12/13) · etiquetas rutas (D2-20) · tokens movimiento (U2-01, M) · keyframes/atShimmer (U2-02) · sin salidas (U2-03) · roving Vuelos/calendario (U2-08/09) · paleta Tab (U2-10) · toasts Esc (U2-11/D1-14) · `aria-busy` (U2-12) · `title` 45 (U2-13) · forced-colors/print (U2-15, M) · fechas UTC/local + DST (W1-05/06/G1-19) · `_build_insights` (W1-07/08) · espacios `%` (W1-09) · `localStorage` sin versión (W2-08/09) · polls sin ciclo (W2-11/12/G1-15/16) · gzip estáticos (B1-01, S) · terceros bloquean (B1-03, M) · `api()` sin timeout (B1-04/W2-04, S) · listeners ×14 (B1-05) · `innerHTML` ×121 (B1-06, M) · `capture_history` 500 (B1-07, M) · `rate_calendar` sin caché (B1-09) · N+1 reseñas (B1-10) · perf LCP 0 (B1-11, S QA).
BE/IA: `responseQuality` (I1-16, M) · `web_search` «tiempo» (I1-17, S) · desfase modelos (I1-18, S) · MoA/streaming/comparable (I1-19, M) · harness `--strict` (I1-20, S QA, mitigado en `ia/casos-live.md`) · SerpAPI 2×90 s + dotenv (B2-10) · sin `onerror` FE (B2-13) · Jev sidecar (B2-14) · cancel/max_attempts (B2-16/17).

## P3 (cosmético, micro)

Fuentes 33→roles (D1-03) · radios 24→8 (D1-04) · `!important` ×13 (D1-06) · fórmulas conformes (W1-03, positivo) · alfa calor (W1-04) · `nEs` ok (W1-10) · dashboard guards ok (W2-07) · API gzip ok (B1-02) · mapas `setStyle` ok (D2-05) · `loadMapLibre` JS ok (B1-14) · 10× aislada p95 <30 ms (B1-13) · WAL ok (B2-18) · auth-solo-prod documentar (B2-15) · tests IA/BE huecos (I1-21/B2-19, M QA) · adjuntos OCR (I1-22) · foco/zoom OK (U2-16/17/18) · paleta/toasts micro (U2-10/11/14, D1-13/14) · copy menor (U1-13/14/16/17/18, U1-04) · `Reputación Error de lectura` (U1-15) · `estimate` por tecla (W2-13) · `State.air` workspace (W2-16) · `renderCopilot` token (W2-15).

## Micro-mejoras (validación U2+D1+D2, G1/B2/W1/W2/I1 sin objeción salvo nota)

Aceptar: MM-01 (tokens conservando 420/260/700) · MM-03 · MM-04 · MM-06 · MM-07 · MM-08 · MM-09 · MM-10 · MM-11 · MM-12 · MM-14 · MM-15 · MX-01 · MX-02 · MX-03 · MX-04 · MX-05 (con `title`) · MX-06 · MX-07. Aceptar con ajuste: MM-02 (con PA-43) · MM-13 (solo transform/opacity). Rechazar: MM-05 (reanima cada render, D2).
