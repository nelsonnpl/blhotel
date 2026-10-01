# Auditoría fase I · corpus reproducible de Revenue Copilot

Fecha de corte: 6 de septiembre de 2026.

Esta fase convierte el siguiente bloque de evaluación del Copilot en un corpus
versionado de siete preguntas representativas. No hace llamadas a OpenRouter ni
guarda respuestas generadas: sólo declara los criterios que una evaluación live
debe comprobar.

## Cobertura del corpus

| Caso | Dimensiones que debe conservar la respuesta |
| --- | --- |
| `corpus_product_comparability` | Producto equivalente, habitación, régimen y cancelación |
| `corpus_profile_change` | Fechas, noches, adultos/pax y moneda |
| `corpus_ambiguous_hotel` | Identidad del hotel, zona y petición de aclaración |
| `corpus_stale_or_unmatched` | Vigencia, comparabilidad y bloqueo de inferencia temporal |
| `corpus_missing_pms` | Ausencia de PMS y rechazo de métricas no disponibles |
| `corpus_decision_gate` | Data gate, aprobación y validación previa |
| `corpus_evidence_citation` | `evidenceId`, procedencia y unidades |

Los casos se ejecutan dentro del perfil `strict` de
`backend.app.copilot_live_evaluation`. Cada resultado conserva el identificador
del caso y sus dimensiones, además de la validación de los cuatro bloques
editoriales y de las afirmaciones numéricas de pickup, ocupación o RevPAR.

## Corrección adicional

La revisión del manifiesto detectó que cuatro casos estrictos no declaraban el
modo (`analysis`). Se corrigió el contrato para que nunca se envíe una pregunta
con el texto interpretado como modo de Copilot. Se añadió una prueba que impide
que vuelva a ocurrir.

## Validación

- 7 casos de corpus con identificadores únicos y dimensiones explícitas.
- Perfil estricto ampliado sin cambiar el perfil básico ni activar llamadas de red.
- 10 pruebas específicas de evaluación aprobadas.
- Suite completa posterior: 117 pruebas backend aprobadas.
- `py_compile` aprobado.

## Primera ejecución live

Se ejecutó el perfil estricto con 17 casos y sin herramientas del modelo. 15
respuestas completaron los cuatro bloques editoriales y sus comprobaciones
semánticas. Los dos casos asignados a `z-ai/glm-5.3-flash` terminaron con
errores de disponibilidad: primero agotaron el presupuesto de tiempo y una
repetición focalizada llegó vacía tras dos intentos. No se clasifican como
fallos de contenido. El resultado técnico quedó registrado como ejecución 2,
con 15 aprobados, 0 advertencias y 2 errores.

Las latencias de los casos completados quedaron entre 3,2 y 17,3 segundos. El
coste reportado por OpenRouter se conserva sólo dentro del resumen técnico de
la ejecución, junto con uso y modelo; no se persiste el texto de ninguna
respuesta.

## Siguiente paso

Cuando el equipo autorice una evaluación con proveedor, ejecutar el perfil
estricto sobre una muestra controlada, guardar sólo latencia, uso, estado y
fallos de contrato, y revisar manualmente los casos que fallen. Los hechos
esperados por fecha, moneda, tarifa y `evidenceId` deben añadirse desde
conversaciones anonimizadas antes de usar una puntuación como criterio de
producción.
