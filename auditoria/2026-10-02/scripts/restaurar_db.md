# Restaurar base (rollback)

1. Parar la instancia que usa la base (`servidor.sh stop <puerto>`). Verificar 0 jobs con `estado_jobs.sh`.
2. `cp <backup.sqlite> <destino.sqlite>` (nunca mover el backup).
3. `sqlite3 <destino> "PRAGMA integrity_check;"` → `ok`.
4. Recuentos por tabla y comparar con el log del `backup_db.py`.
5. Arrancar y humo: una vista por pestaña.

## Regla F4-INC (2026-10-02)

Jamás copiar/sustituir el `.sqlite` (ni su `-wal`/`-shm`) de un servidor EN MARCHA,
ni siquiera con un backup limpio como fuente: el `-wal` viejo y los handles abiertos
corrompen el fichero nuevo (doble referencia de página). Orden: parar → sustituir →
`integrity_check` → arrancar. Vale para copias de trabajo, no solo para la operativa.
