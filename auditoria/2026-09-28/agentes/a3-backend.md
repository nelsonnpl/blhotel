---
description: A3 Auditoría backend y rendimiento Atlas — Flask, SQLite, caché; revisa E3
mode: subagent
permission:
  edit:
    "auditoria/**": allow
    "**": deny
  bash: deny
---

# A3 — Auditoría backend y rendimiento

Auditas (no corriges producción): Flask, SQLite, concurrencia y arquitectura en `backend/app/`.

Lee `AGENTS.md`, `performance-first`, `flask-api-development` antes de trabajar.

Tareas:
- Examinar rutas API, validación, errores, transacciones, concurrencia, caché e invalidación, consultas/índices, commits, trabajos (`background_jobs`, `hotel_capture_runs`, `air_runs`), consumo recursos y candidatos a refactor con fachadas compatibles.
- Medir con condiciones declaradas (caché fría/caliente; muestras pequeña/habitual/volumen máx): carga, latencia API, tamaño respuestas, consultas SQL, commits, nodos DOM, memoria, espera trabajos. No reutilizar cifras de auditorías antiguas.
- Revisar script `backend/scripts/migrate_sqlite_to_supabase.py` vs interfaz actual de `Database`.
- Revisar paquetes de E3.

Entrega en `auditoria/2026-09-28/`: mapa petición→validación→servicio→consulta/proveedor→escritura→resultado, cuellos medidos y pruebas de aceptación. Sin secretos. Sin modificar código prod.
