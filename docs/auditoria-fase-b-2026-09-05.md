# Fase B — Perfil de captura y procedencia de las fotos

Fecha: 5 de septiembre de 2026. Esta fase convierte el formulario de capturas en una solicitud explícita y conserva el perfil efectivo con cada foto.

## Cambios

- La captura manual solicita fecha de entrada, noches, adultos, una habitación, régimen y número de entradas semanales.
- La opción por defecto es una foto para una fecha. Se puede pedir una serie de 4, 13 o 26 entradas semanales (hasta 180 días). Cada semana genera una foto independiente y comparte `captureGroupId`.
- El backend normaliza la URL antes de consultar y guarda exactamente esa URL: fechas, salida calculada, adultos, niños, habitaciones, EUR y filtro de régimen.
- Se rechazan URLs que no sean de Booking.com, URLs con credenciales embebidas, fechas pasadas y perfiles fuera del alcance actual (niños, más de una habitación o moneda distinta de EUR).
- Las fotos antiguas sin metadatos se representan como `legacy_url`; sus parámetros desconocidos no se rellenan con valores inventados.
- Las capturas de detalle aceptan `snapshotId`. Se comprueba que el hotel pertenezca a esa foto y que estancia y ocupación coincidan. El detalle queda vinculado mediante `snapshot_id`.
- El desglose histórico que no tiene vínculo se etiqueta como evidencia independiente con fecha propia; no se presenta como el desglose de la foto seleccionada.
- El guardado de una foto y sus filas hoteleras usa una transacción única. Un fallo de una fila revierte la foto completa.
- Los agregados de dashboard, historial, foto, oportunidades y mapa se bloquean si una foto contiene moneda distinta de EUR o moneda desconocida. No se aplica conversión implícita.
- La interfaz muestra la procedencia y el perfil de búsqueda de cada foto. A 993 px, el formulario mantiene su anchura y el selector de 26 fotos sigue siendo utilizable.

## Validación

- 103 pruebas de backend aprobadas.
- 8 pruebas JavaScript de comparabilidad aprobadas.
- `node --check backend/app/static/atlas.js` aprobado.
- `py_compile` del módulo de perfil, modelos, base de datos, servicio y Flask aprobado con `.venv/bin/python`.
- La copia visual contiene 24 fotos, 923 filas hoteleras y 8.335 tarifas de detalle; `PRAGMA quick_check` devuelve `ok` y `foreign_key_check` no devuelve filas.
- Revisión visual de Capturas en 1440×900, 1920×1080, 1366×768 y 993×900. Se comprobó que la fecha es obligatoria, que la serie semanal se puede seleccionar sin lanzar una consulta, y que no hay scroll horizontal del documento.
- No se ejecutaron consultas a Booking ni llamadas de pago durante las pruebas.

## Límites que quedan deliberadamente visibles

- La moneda operativa sigue siendo EUR hasta añadir una tabla de tipos de cambio fechados y una política de conversión auditable.
- El perfil actual no modela edades de niños ni más de una habitación; ampliar esos campos requiere rehacer la firma de producto y el contrato de detalle.
- Las fotos heredadas no pueden recuperar parámetros que nunca se guardaron. Su comparabilidad se mantiene conservadora.
- El barrido semanal se ejecuta en el momento y no crea una programación periódica. El usuario acordó capturas manuales por ahora.
- `hotel_capture_runs` y `market_snapshots` guardan hoy metadatos separados; el grupo semanal se conserva en el perfil JSON. Una migración posterior puede normalizar perfiles y grupos sin reescribir las filas históricas.
- La UI muestra “ADR” por compatibilidad con el producto, pero los valores son tarifas públicas observadas, no ADR realizado, pickup, ocupación ni RevPAR.
- El inspector del mapa representa ahora la serie completa de fotos del hotel, con fecha de entrada y fecha de captura. Cada punto es una extracción y la variación principal compara su precio mediano con la extracción anterior; el detalle de producto se conserva para interpretar cambios de habitación o estancia.

## Copias y siguiente fase

Los archivos existentes editados antes de esta fase están respaldados en `backups/phase-b-20260905/` con manifiesto SHA256. No se tocó la BBDD original.

La siguiente fase revisará el contexto de Copilot: selección de herramientas, trazas de evidencia, compresión de snapshots, control de tokens, evaluación de respuestas y separación entre observación pública y decisión operativa.
