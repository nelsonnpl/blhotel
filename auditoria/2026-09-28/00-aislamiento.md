# Aislamiento pruebas (E5, revisa A4)

- Base temporal exclusiva: `SQLITE_PATH=/tmp/atlas-test-*.sqlite` (o dir temporal por run); nunca `data/booking-prices.sqlite`.
- Dirs temporales para adjuntos/exports; limpiar tras cada suite.
- Red externa bloqueada por defecto: no `OPENROUTER_API_KEY`, no `SERPAPI_API_KEY`, no `DECODO_*` en entorno de tests. Verificar con `env | cut -d= -f1` que no se cargan credenciales.
- `backend/tests/conftest.py` debe aislar (revisar en Fase 2); proyecto reseñas `side_projects/atlas_google_reviews_jev` fuera de colección默认 (`pytest.ini testpaths=backend/tests`) — ejecutar explícito con fixtures locales.
- Copilot local sin proveedores: `python -m backend.app.copilot_evaluation` (sin `--live`).
- Datos artificiales solo en fixtures aisladas identificadas; nunca como información real.
