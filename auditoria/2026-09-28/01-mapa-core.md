# Mapa proyecto y core Atlas (Fase 1, esqueleto A1 — completan A2–A5)

## Vista → interacción → petición → validación → servicio → proveedor/consulta → escritura → resultado
App SPA servida por Flask (`backend/app/flask_app.py`, 3246 líneas; 79 rutas) con shell `templates/index.html` (126 líneas) + `static/atlas.js` (4511 líneas) + `static/atlas.css` (1462). Legado probable: `static/app.js` (8540 líneas) + `static/app.css` (10426) sin referencia en `index.html` — clasificar como heredado pendiente (A2/A3 verifican consumidores).

### 7 vistas (nav `data-view` + `section#view-*`)
1. Dashboard (`dashboard`) — `#view-dashboard`, `#crumbView`, ticker `#ticker`, mapa MapLibre (CSS externo unpkg).
2. Hoteles (`hotels`) — `#view-hotels`, tab `hotelTableTab`.
3. Reputación (`reputation`) — `#view-reputation`, tab `hotelReviewTab`.
4. Vuelos (`flights`) — `#view-flights`, tab `airTableTab`.
5. Copilot (`copilot`) — `#view-copilot`, botón `data-nav=copilot`, `⌘O`.
6. Espacio de trabajo (`workspace`) — `#view-workspace`.
7. Capturas (`captures`) — `#view-captures`, botón `#captureTop`.
Sesión/bloqueo: `#lockBtn`, `#lock` dialog modal, `#unlockBtn`, `/api/auth/session`; `/api/health` público.

### Rutas API (grupos, 79 reglas)
- Auth/sesion, health; Dashboard `/api/dashboard/metrics`, snapshots, fotos, heatmap, targets.
- Hoteles: inventory, history, price-history, rate-details, scrape search/detail, jobs hotel-capture + hotel-detail-capture.
- Reputación: `/api/hotel-reviews/*` (profile, reviews+versiones, analyses, attributes, links, notes, export.tsv, captures, catalog).
- Vuelos: `/api/air-data/*` + `/api/jobs/air-capture` (SerpApi o mock).
- Copilot: `/api/assistant/*` (chat, sessions, attachments, jobs+cancel, budget, evaluations/latest).
- Workspace: `/api/workspaces/*` + revisions.
- Capturas/jobs: `/api/jobs/<id>`+cancel, captures/history.
- Externas: `/api/external/*` (sources, observations, cache, sync dataestur-prices/istac).
- Analítica: `/api/analytics/*` (8 endpoints). Clima: `/api/weather/*`.

### Persistencia (SQLite WAL, 39 tablas, 18.5M)
Núcleo: `market_snapshots(24)` + `market_snapshot_hotels(923)` + `hotel_price_observations(923)` + `hotel_rate_details(8335)`; inventario `hotel_inventory(49)`, `hotel_locations(48)`, `search_targets(2)`.
Aéreo: `air_runs(13)`, `air_route_snapshots(170)`, `air_flights(582)` + `flight_price_observations(582)`.
Reputación: `hotel_reviews(2353)`, `hotel_review_versions(3346)`, runs(41), legacy_imports(1).
Copilot: sessions(16), messages(44), runs(29), attachments(0), budget_reservations(5), evaluations(3).
Operación: `background_jobs(53)`, `hotel_capture_runs(24)`, ingestion_runs(7), `external_observations(539)`, clima 357+91, workspaces(1)+rev(1).

### Proveedores y activación
- Booking GraphQL vía Playwright (defecto `SCRAPER_BACKEND=graphql`); alternativa Decodo proxy pago. Sin evasión/CAPTCHA.
- SerpApi vuelos (sin clave → mock). OpenRouter Copilot (sin clave → aviso; routing/evaluación local sin coste). ISTAC/Dataestur cubos permitidos + Dataestur `CCAA=Canarias`. Clima proveedores propios.
- Costes: solo OpenRouter/SerpApi/Decodo consumen; resto local.

### Scripts, jobs, pruebas
- Scripts: `backend/scripts/capture_all_hotel_details.py`, `migrate_sqlite_to_supabase.py` (A3: incompatible con `Database` actual — reproducir).
- Jobs en SQLite (`background_jobs`, `hotel_capture_runs`, `air_runs`), worker local al proceso Flask.
- Tests: `backend/tests` (17 ficheros, conftest aísla a temp SQLite), `tests/revenue-semantics.test.cjs`, `side_projects/atlas_google_reviews_jev` (fuera de `pytest.ini`).

### Invariantes negocio (A1)
Tarifa observada ≠ reserva/ocupación/pickup/ingresos. Comparación exige hotel+estancia+ocupación+producto+régimen+moneda+condiciones. Cobertura/frescura/comparabilidad distintas. Procedencia y relación captura siempre. Desconocido nunca → cero/equivalencia.

### Auditorías históricas (clasificación inicial, A1 consolida con auditores)
`docs/auditoria-completa…`, fases A–I, ISTAC/Dataestur, vuelos SerpApi, RMS/CRS, fotos/límites: pendientes de clasificar en vigentes/pendientes/superadas/contradichas en Fase 3. Ninguna capacidad futura se presenta como implementada.
