# Fase 0 — Entorno y protección (2026-09-28)

## Versiones registradas
- Python: 3.13.2 (`.venv`), sistema 3.13.2
- SQLite: 3.51.0, journal_mode operative: WAL (tras checkpoint sin shm/wal visibles el 28-09, tamaño 18 558 976)
- Node: v23.10.0
- Flask: 3.1.3, Werkzeug 3.1.8, pytest 9.1.1, httpx 0.28.1, Playwright 1.62.0, pydantic 2.13.5
- OS: darwin; shell: zsh; repo: sin Git (no inicializar)
- Sesión: OpenCode con Muse Spark 1.3 (pin de modelo omitido por decisión usuario 28-09; agentes heredan modelo global)

## Agentes (10)
- `.opencode/agents/`: `a1-direccion.md` (primary), `a2-ux.md`, `a3-backend.md`, `a4-calidad.md`, `a5-integraciones.md`, `e1-visual.md`, `e2-flujos.md`, `e3-backend.md`, `e4-integraciones.md`, `e5-qa.md`.
- Reglas: auditores solo informes (edit denegado salvo `auditoria/**`); un único escritor por archivo; E1/E2 frontend por turnos; E3/E4 Flask/persistencia por turnos; máx. 3 tareas simultáneas + A1.

## Protección
- Backup coherente SQLite vía API `sqlite3.backup()` (no solo cp por WAL):
  `backups/pre-auditoria-20260928/booking-prices-backup.sqlite` — 18 558 976 bytes, sha256 `298c74ae…afb3`, integrity `ok`, 39 tablas.
  Operativa `data/booking-prices.sqlite` mismo tamaño, sha distinto (`d5d992a0…`) por reescritura física; contenido lógico idéntico.
- Código: `backups/pre-auditoria-20260928/codigo-20260928.tar.gz` (600K) excluye `.venv`, `__pycache__`, `.env`, `backups/`, `auditoria/`, `*.sqlite*`. SHA en `SHA256SUMS`.
- Manifiesto código: `auditoria/2026-09-28/manifiestos/manifiesto-inicial.sha256` (114 ficheros).
- Restauración ensayada aislada en `/var/.../T/atlas-restore-20260928/restored.sqlite`: integrity `ok`, `market_snapshots=24`, `hotel_price_observations=923`, `background_jobs=53` — coincide con operativa.
- Secretos: `.env` excluido de tar y de evidencias; en informes solo nombres de claves, nunca valores.

## Chequeo salida Fase 0 (parcial)
- [x] Diez agentes configurados (modelo heredado por omisión acordada)
- [x] Copia y manifiesto verificables
- [x] Restauración inicial ensayada en dir aislado
- [ ] Pruebas incapaces de modificar datos operativos (pendiente: doc aislamiento + verificación)
- [x] Ningún secreto en evidencias
