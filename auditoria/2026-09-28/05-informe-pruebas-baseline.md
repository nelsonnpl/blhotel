# Informe pruebas línea base (Fase 2, E5 ejecuta; verifican A2–A4)

Fecha 2026-09-28. Red externa bloqueada (`env -u OPENROUTER_API_KEY SERPAPI_API_KEY DECODO_* DATABASE_URL`). Base operativa intacta (`data/booking-prices.sqlite` 18 558 976, mtime inalterado).

## Comandos y resultados
1. `env -u ... .venv/bin/python -m pytest backend/tests -q` → **185 passed en 1.98s**. EXIT 0.
2. `node --test tests/revenue-semantics.test.cjs` → **8 passed** (unknown board/roomType/currency/pax/freeCancellation no comparables; movimiento no inflado; duplicados excluidos; monedas mixtas sin promedio). EXIT 0.
3. `pytest side_projects/atlas_google_reviews_jev/test_parser.py` → **3 passed**.
   `pytest .../test_parser.py .../test_operations.py` → **7 passed, 2 failed**:
   - `BookingPaginationTests::test_stalled_next_control_stays_partial_and_does_not_repeat_pages`: `'empty' != 'partial'`.
   - `GoogleCoverageTests::test_unverified_filters_cannot_be_reported_as_exhausted`.
   Fallos previos (no regresiones nuestras); A4 los adopta para reproducción.
4. `pytest side_projects/.../test_dataset_export.py` → **error colección**: `ModuleNotFoundError: langdetect` (dependencia ausente en `.venv`; `requirements-jev.txt` no instalado). Limitación entorno.
5. `env -u ... .venv/bin/python -m backend.app.copilot_evaluation` → `{"passed": true, ...}` routing 5/5 + dataGate; EXIT 0; sin `--record` no crea SQLite (esperado). Sin proveedores.

## Fallos previos vs regresiones
- JEV 2 fallos + 1 dependencia ausente = línea base, no regresión Fase 5 (aún sin cambios prod).
- Backend/JS/Copilot local en verde.

## Limitaciones
- Sin capturas visuales aún (Fase 2 visual pendiente: 7 vistas × 4 viewports + consola/teclado/tablas).
- Sin medición rendimiento aún (carga, latencia, SQL, DOM, memoria, jobs fría/caliente).
- `conftest.py` aísla bien (temp SQLite); `test_operations` usa fakes locales.
- Cobertura código no medida; se medirá comportamiento/riesgo, no % artificial.
