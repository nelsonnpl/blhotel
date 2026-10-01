# Plan de correcciones (Fase 4 — A1, reversible, sin aprobación rutinaria adicional)

Orden: P0 → P1 → P2. Un ejecutor + un auditor distintos por paquete. Un único escritor por archivo; E1/E2 frontend por turnos; E3/E4 backend por turnos. Copia+manifiesto previos y reversión comprobable por paquete.

| Paquete | Problema | Ejecutor→Auditor | Archivos | Cambio mínimo | Regresión | Reversión |
|---|---|---|---|---|---|---|
| PKG-01 P0 | H-02/H-03/H-11 permisos jobs/detail | E3→A4 | `flask_app.py`, `database.py`, `models.py`(solo tipos) | owner obligatorio en batch (filtro por owner), `None` denegado, validar `detailUrl` https Booking + `hotelKey`, fechas | `pytest backend/tests/test_flask_app.py backend/tests/test_jobs.py` + repro owner | cp previos en `backups/pkg-01/` + `git diff` n/a (sin git: tar) |
| PKG-02 P0/P1 | H-01/H-04/H-09 adjuntos | E3→A4 | `flask_app.py`, `requirements.txt` | contar referencias antes `unlink`; `MAX_CONTENT_LENGTH=20MB`; añadir `pypdf` | upload/delete con misma sha en tmp DB; PDF extrae texto | idem `backups/pkg-02/` |
| PKG-03 P1 | H-10 fórmulas TSV | E3→A4 | `flask_app.py` | sanitizar celdas `=+-@|\t\r` con prefijo `'` | export con `=HYPERLINK` queda inerte | `backups/pkg-03/` |
| PKG-04 P1 | H-05–H-08/H-14 flujos | E2→A2 | `atlas.js` (turno exclusivo) | `isSaving`+copia payload+`expectedVersion`; guardias `targetId`/`sessionId` post-await; `selectMarket` re-render flights+reputation; guardias copilot/adjuntos/catch; tope+limpieza polls | `node --test tests/` + visual 2 vistas | `backups/pkg-04/` |
| PKG-05 P2 | H-12 overflow Copilot | E1→A2 | `atlas.css` (turno exclusivo) | `min-width:0; overflow-x:auto/clip` en panel resultados | captura 1440 antes/después | `backups/pkg-05/` |
| PKG-06 P2 | H-17 proveedores | E4→A5 | `serpapi_flights.py` (+doc) | bulk usa `fetch_google_flights_with_retry`; documenta cancel/coste; gasto sigue 0 | tests air + evaluación local | `backups/pkg-06/` |
| PKG-07 P2 | H-16 migración | E3→A3 | `backend/scripts/migrate_sqlite_to_supabase.py` | fail-fast claro (incompatible con `Database(path)`); sin TRUNCATE accidental | `--help` + run guarded en tmp | `backups/pkg-07/` |
| PKG-08 P3 | H-18 JEV | E5→A4 | `side_projects/...` solo si trivial | `langdetect` en `requirements-jev.txt` o skip documentado; 2 tests | pytest jev parcial | `backups/pkg-08/` |

No incluye: reescritura general, PMS/RMS nuevo, frameworks, cambios auth monousuario, desmontaje vistas (H-13 solo documentado), lock trap (H-15 documentado).
