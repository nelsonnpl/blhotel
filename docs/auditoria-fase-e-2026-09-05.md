# Auditoría fase E · limpieza y rendimiento

Fecha de corte: 5 de septiembre de 2026.

## Resultado del inventario

La aplicación que se entrega desde `backend/app/templates/index.html` carga únicamente `atlas.css` y `atlas.js`. La búsqueda de consumidores no encontró referencias internas a `app.css` ni `app.js`; ambos son una implementación anterior de la interfaz y suman aproximadamente 18.900 líneas. `copilot-render.css` y `rate-detail.css` tampoco aparecen enlazados por la plantilla actual. Se conservan por ahora porque una URL estática pública puede tener consumidores externos, pero no deben seguir formando parte del artefacto de producción sin una decisión de compatibilidad.

No se han encontrado módulos Python claramente huérfanos: los extractores, parser, jobs, contratos del Copilot y scripts de migración aparecen importados por la aplicación o invocados como comandos documentados. Los directorios `__pycache__`, `.pytest_cache` y las previsualizaciones de `.codex_work` son artefactos de desarrollo y deben quedar fuera del paquete de despliegue.

## Acciones aplicadas

- El contexto de expertos tiene un presupuesto global de 24.000 caracteres; se recortan listas secundarias de forma determinista y se conserva la evidencia.
- El trazado MoA agrega nombres de herramientas sin copiar argumentos ni prompts.
- Se eliminaron tres imports Python sin uso comprobado (`datetime`, `timezone` y `CompetitiveStabilityEntry`) detectados por revisión AST y confirmados con búsqueda de referencias.
- Se mantiene una única proyección `atlas-61` para invalidar caché de la interfaz tras los cambios de Copilot.
- Las pruebas se ejecutan contra SQLite temporal; no se modifica la base original.

## Medición disponible

- 106 pruebas de backend aprobadas.
- 8 pruebas JavaScript de semántica aprobadas.
- `node --check backend/app/static/atlas.js` aprobado.
- `py_compile` de los módulos modificados aprobado.
- La copia de auditoría de SQLite mantiene `quick_check=ok` y `foreign_key_check` sin incidencias.

## Recomendación de retirada segura

1. Buscar durante una semana logs de `GET /static/app.js`, `app.css`, `copilot-render.css` y `rate-detail.css`.
2. Si no hay accesos, moverlos a un paquete de legado versionado y excluirlo del contenedor o del zip de producción.
3. Mantener una respuesta 410 o redirección documentada sólo si existe un consumidor conocido.
4. Repetir la auditoría de tamaño del artefacto y tiempo de primera carga después de retirar los archivos.

No conviene borrar esos cuatro ficheros sin observar primero el tráfico estático: el código no tiene consumidores dentro de la aplicación, pero una referencia externa no sería visible con `rg`.

## Próxima optimización con retorno alto

La mayor ganancia futura no está en microoptimizar JavaScript. Está en separar el worker de capturas del proceso web, añadir índices SQLite para `(target_id, check_in, captured_at)` y `(snapshot_id, hotel_key)`, y medir consultas y tamaño de payload antes de cambiar el almacenamiento. Esa migración debe hacerse con un perfil de carga representativo y una copia de la base.
