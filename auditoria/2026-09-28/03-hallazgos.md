# Registro de hallazgos (Fase 3 — consolidado A1, evidencia 28-09)

Fuentes: inspección directa + 3 subagentes lectura + capturas 28 vistas + APIs medidas. Sin secretos. Datos artificiales no usados como reales.

## P0 — corrupción / pérdida / exposición crítica / gasto fuera de control
- H-01 Borrado adjunto rompe referencias compartidas. `flask_app.py:709-711` dedup por sha256 (misma ruta), `flask_app.py:740-742` `unlink` sin contar referencias. Repro estático: hecho. Estado: pendiente fix (PKG-02).
- H-02 Lote `GET /api/jobs/hotel-detail-capture/<batch>` sin owner. `flask_app.py:2650-2652` + `database.py:3599` sin filtro. Cualquiera con batch_id lista hotel_key/name/url. Hecho. PKG-01.
- H-03 Jobs con `ownerKey=None` legibles/cancelables por cualquiera. `flask_app.py:2658,2666` condición `not in {None, me}`. Hecho. PKG-01.
- H-04 1MB global vs contrato 20MB adjuntos. `flask_app.py:85` vs `:637,704-705`. Subidas >1MB mueren en Werkzeug antes del 20MB. Hecho. PKG-02.

## P1 — flujo bloqueado / contexto incorrecto / cálculo erróneo / pérdida trabajo
- H-05 Workspace: guardado sin `isSaving`, sobreescritura cross-mercado, payload por referencia. `atlas.js:3689-3711,3719-3739,4256-4258`. Hecho. PKG-04.
- H-06 `renderWorkspace` sin guardia post-await (pinta B con datos A). `atlas.js:3753-3754` vs dashboard `990-1003` que sí la tiene. Hecho. PKG-04.
- H-07 `selectMarket` sin abort; no re-renderiza flights/reputation. `atlas.js:3992-4003`; cero `AbortController`. Hecho. PKG-04.
- H-08 Copilot: respuesta sin guardia mercado + poll huérfano 9min + adjuntos push sin guardia sesión + `loadSession` catch sin guardia. `atlas.js:3417-3453,3493,3504-3515,3258-3273`. Hecho. PKG-04.
- H-09 PDF siempre `visual_required`: `flask_app.py:657-663` importa `pypdf` ausente en `requirements.txt`. Hecho. PKG-02 (añade dep demostrada).
- H-10 CSV inyección fórmulas en `export.tsv`. `flask_app.py:1325-1347` crudo. Hecho. PKG-03.
- H-11 Enqueue detail rama `snapshotId None` sin `can_access_*`, contrato `models.py:273-275` débil (`dict`, `str` sin `HttpUrl/date`). `flask_app.py:2634-2642`. Hecho. PKG-01.
- H-12 Copilot overflow horizontal a 1440 (panel derecho recortado; evidencia `copilot-1440x900.png`). Hecho visual. PKG-05.

## P2 — fricción / lentitud demostrada / inconsistencia / deuda
- H-13 DOM 1759→7132 y tablas 4→11 al navegar (vistas ocultas conservan DOM; cachés por `targetId` acotadas a mercados existentes). Medido 5 ciclos: estable 7132/11/10MB. ACEPTADO sin cambio (sin fuga).
- H-21 (P3) Solape de cabecera Copilot sobre 1 línea de contenido a zoom 200% (`zoom-1920z200-hotels.png`). Controles utilizables, sin overflow. Documentado; sin fix.
- H-14 Polls sin limpieza (assistant 9min, reseñas sin tope, capturas ~2h). `atlas.js:3493,2684-2692,3964-3966`. Hecho. PKG-04 parcial (guardias) o documenta.
- H-15 Lock sin trap/`inert`/`Escape`. `index.html:108`, `atlas.js` (foco inicial/retorno sí; trap no en auditoría). Hecho. RESUELTO en PKG-09: `lockFocusable`+`trapLockTab`+`inert` en `.atlas-root`, cableado único vía `dataset.trapWired`; verificado con teclado (Tab/Shift-Tab ciclan `lockPass`↔`unlockBtn`, fondo inerte, retorno a `lockBtn`, sin pageerrors). Escape no desbloquea por diseño (exige contraseña).
- H-16 Migración postgres incompatible total (kwargs, tablas, dialectos, TRUNCATE). `migrate_sqlite_to_supabase.py:16-27,51-52,71-123` vs `database.py:47`. Hecho. PKG-07 (fail-fast).
- H-17 Coste desconocido si proveedor no informa (`database.py:1990` → 0), MoA 3-4 llamadas (`copilot_moa.py:193-228,302-310`), `ask_openrouter` hasta 4×6×12 (`assistant.py:226-236,1126-1356`), Decodo 12 POSTs/90s (`decodo.py:40-82`), SerpAPI bulk sin retry (`serpapi_flights.py:78-87` vs helper `143-163`), weather/external sin retry. Hecho código; impacto € hipótesis (gasto 0). PKG-06 mínimo + registro 5€.
- H-18 JEV: `langdetect` ausente (colección) + 2 fallos (`test_stalled_next_control`, `test_unverified_filters`). Línea base. PKG-08.
- H-19 CDN externo (fonts/maplibre unpkg) sin fallback: `dashboard-1366` mostró "No se pudo cargar el mapa base" por `ERR_NETWORK_CHANGED` transitorio; hay botón Reintentar. Hecho ejecución. Documenta.
- H-20 Secret fallback dev (`flask_app.py:83`) + `current_owner_key` sin `authenticated` (`798-803`) + login otorga admin todos los mercados (`766-771`). Diseño monousuario local; riesgo solo si despliegue erróneo. Documenta; sin cambio (no tocar auth en uso individual).

Defensas verificadas (no hallazgo): XSS mitigado (jsonify + CSP `103-111` + allowlist `1199-1200` + `esc`); SQLi parametrizado; writes con RLock+WAL; `require_decodo` y evaluación Copilot local sin coste.
