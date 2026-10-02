# Restaurar base (rollback)

1. Parar la instancia que usa la base (`servidor.sh stop <puerto>`). Verificar 0 jobs con `estado_jobs.sh`.
2. `cp <backup.sqlite> <destino.sqlite>` (nunca mover el backup).
3. `sqlite3 -readonly <destino> "PRAGMA integrity_check;"` → `ok`.
4. Recuentos por tabla y comparar con el log del `backup_db.py`.
5. Arrancar y humo: una vista por pestaña.
