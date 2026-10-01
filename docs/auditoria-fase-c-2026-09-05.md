# Fase C — Copilot, contexto y consultas verificables

Fecha: 5 de septiembre de 2026.

## Hallazgos y correcciones

- La interfaz enviaba siempre `mode: analysis`, aunque el contrato del backend soportaba rápido, análisis y decisión. Ahora el usuario elige el modo explícitamente; se inicia en Rápido para una consulta cotidiana y se puede cambiar antes de enviar.
- Las respuestas guardadas ya mostraban modelo, ruta y calidad, pero no las herramientas concretas. Se conserva una lista de nombres de herramientas, número de llamadas y errores en `dataMeta`; nunca se guardan los argumentos de la herramienta en la trazabilidad visible.
- `historial_precio_hotel` devolvía filas con campos de inventario y parser repetidos. Ahora envía como máximo 36 observaciones compactas, conservando foto, fechas de estancia, noches, adultos, habitación, régimen, moneda, cancelación y tarifa por noche. Incluye `capturasRecortadas` cuando se supera el límite.
- La herramienta de historial devuelve candidatos y exige la zona si el nombre parcial es ambiguo. La consulta queda acotada al mercado resuelto.
- Se eliminó una invocación duplicada de la herramienta de competidores detectada en la auditoría estática.

## Qué ya estaba protegido y se mantiene

El contexto separa datos de hoteles y vuelos, conserva un paquete `revenue-evidence.v1`, limita el historial conversacional a ocho turnos, ejecuta el control de calidad antes de una decisión y bloquea pricing concluyente si la foto está caducada o sin comparativa suficiente. El modelo no puede emitir SVG/Mermaid para sustituir una visualización calculada por el servidor.

## Validación

- 105 pruebas de backend aprobadas después de las correcciones de compactación y trazabilidad.
- 8 pruebas JavaScript de comparabilidad aprobadas.
- Sintaxis JavaScript aprobada con `node --check`.
- No se hicieron llamadas al proveedor LLM durante esta fase.

## Pendientes de IA

1. Persistir un `evidenceId` por observación de herramienta y permitir que la respuesta cite esa evidencia de forma estructurada, sin confiar únicamente en texto libre; ahora cada resultado correcto incluye `_evidence.evidenceId`, el backend lo conserva en `dataMeta` y la traza del frontend lo muestra.
2. Aplicar un presupuesto explícito de caracteres/tokens al contexto proyectado y medirlo antes de cada llamada; la proyección de expertos ya tiene un techo global de 24.000 caracteres y marca las secciones omitidas.
3. Añadir evaluaciones con respuestas esperadas para fechas, monedas, productos no equivalentes, ambigüedad y ausencia de PMS.
4. Separar una propuesta de acción de su confirmación. Las mutaciones futuras deben ser herramientas con previsualización, autorización y registro de auditoría; las herramientas de lectura siguen siendo gratuitas.
5. Revisar el modo Decisión cuando los datos estén caducados: actualmente el control local bloquea la llamada al proveedor, aunque Rápido y Análisis pueden explicar la limitación.
6. Vincular el detalle de tarifas al `snapshotId` en la UI de captura; los detalles antiguos ya se etiquetan como independientes y no se muestran como evidencia de la foto seleccionada.

La siguiente fase puede concentrarse en evaluación reproducible y evidencia citable, antes de conectar nuevas fuentes privadas o automatizar decisiones.
