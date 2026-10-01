# Registro único presupuesto externo — tope 5 € agregado

Gestiona E4, revisa A5. Red externa bloqueada por defecto en pruebas. Muestras reales solo tras pruebas aisladas, casos mínimos secuenciales, con reserva de coste máximo acotable por llamada.

| Fecha | Agente | Concepto | Estimado € | Comprometido € | Facturado € | Estado |
|---|---|---|---|---|---|---|
| 2026-09-28 | A1 | Inicialización registro | 0 | 0 | 0 | abierto |

Totales: estimado 0 / comprometido 0 / facturado 0 / disponible 5.00.

Reglas:
- Reservar antes de cada llamada su coste máximo (incluidos reintentos).
- Si coste final se desconoce, conservar reserva.
- Si no puede acotarse, no ejecutar y documentar como bloqueada.
- No lanzar evaluaciones completas ni capturas masivas indiscriminadas.
- No extrapolar percentiles ni equivalencia entre modelos desde muestra pequeña.
