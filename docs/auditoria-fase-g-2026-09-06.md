# Auditoría fase G · evaluación y evidencia del Copilot

Fecha de corte: 6 de septiembre de 2026.

## Corrección aplicada

Las herramientas de lectura (`buscar_hotel`, `historial_precio_hotel`, `buscar_vuelos` y `listar_competidores`) devuelven ahora un bloque `_evidence` cuando la consulta es correcta:

```json
{
  "evidenceId": "tool-listar_competidores-…",
  "tool": "listar_competidores",
  "observedAt": "…"
}
```

El identificador se añade a `dataMeta.toolEvidenceIds` y se muestra en la sección Trazabilidad de la interfaz. Los argumentos de la herramienta siguen fuera de la respuesta visible y de la telemetría persistida. El prompt del Copilot exige citar el identificador cuando una cifra procede de una herramienta.

En paneles MoA los nombres e identificadores se agregan sin duplicados entre expertos y síntesis. La evidencia es de lectura y no permite modificar reservas, tarifas ni inventario.

## Evaluación actual

- Routing local: 5 casos aprobados.
- Data gate: casos vigente, caducado y sin comparativa aprobados.
- Pruebas adversariales de comparabilidad, moneda, pax, habitación y cancelación aprobadas.
- Backend: 106 pruebas aprobadas.
- JavaScript: 8 pruebas aprobadas.

## Siguiente bloque de evaluación

Construir un corpus anonimizado de preguntas reales de Revenue con respuesta esperada estructurada:

1. Comparación de productos equivalentes y no equivalentes.
2. Cambio de fecha de entrada, noches, adultos y moneda.
3. Hotel ambiguo entre zonas.
4. Foto caducada o sin antecedente emparejado.
5. Petición de pickup/ocupación sin PMS.
6. Decisión de pricing que debe quedar bloqueada por el data gate.
7. Uso correcto de una herramienta y cita de su `evidenceId`.

Cada caso debe puntuar hechos, unidades, fecha, moneda, cobertura, advertencias y acción. La métrica de éxito no es sólo que el texto suene bien: la respuesta debe conservar la semántica de la foto y reconocer los datos que faltan.

