# Manifiestos, restauración y manual operativo (28-09)

## Manifiestos
- `manifiestos/manifiesto-inicial.sha256` (114 ficheros, pre-cambios).
- `manifiestos/SHA256SUMS-backup.txt` (backup SQLite + tar código).
- `manifiestos/SHA256SUMS-pkg01-prev.txt`, `-pkg02-prev.txt`, `-pkg0405-prev.txt` (copias previas por paquete).
- `manifiestos/SHA256SUMS-pkg01-post.txt`, `-pkg0203-post.txt`, `SHA256SUMS-post.txt` (post-cambios).
- `backups/pre-auditoria-20260928/`: `booking-prices-backup.sqlite` (API backup, integrity ok, 39 tablas) + `codigo-20260928.tar.gz` (sin `.env`/venv/sqlite).
- `backups/pkg-01…pkg-07/`: copias previas por paquete.

## Restauración
1. Código: `tar -xzf backups/pre-auditoria-20260928/codigo-20260928.tar.gz` o copia puntual desde `backups/pkg-NN/`.
2. Datos: `sqlite3 <dest> ".restore backups/pre-auditoria-20260928/booking-prices-backup.sqlite"` o API `backup`; verificar `PRAGMA integrity_check` + conteos (24/923/53).
3. Ensayo 28-09 en `/var/.../T/atlas-restore-20260928/restored.sqlite`: ok.
4. Operativa 28-09 intacta en contenido (24/923/53/3/44, integrity ok); solo mtime por checkpoint de lectura.

## Manual operativo mínimo
- Arranque: `.venv/bin/python run.py` (`FLASK_PORT`, `SQLITE_PATH`, `APP_ENV=development` sin auth; producción exige `APP_AUTH_PASSWORD`+`FLASK_SECRET_KEY` tras HTTPS).
- Backup coherente: API `sqlite3.backup()` (no `cp` con WAL) + `tar` código sin secretos + sha256.
- Tests: `pytest backend/tests -q` (aísla a temp), `node --test tests/revenue-semantics.test.cjs`, Copilot local `python -m backend.app.copilot_evaluation` (sin `--live`).
- JEV: entorno propio según `side_projects/.../README.md` (`langdetect` fuera de prod).
- Muestras reales: solo E4, secuencial, con reserva y tope 5 € (`07-registro-gasto.md`).
- Reversión por paquete: copiar `backups/pkg-NN/` sobre el árbol + re-ejecutar suites.
