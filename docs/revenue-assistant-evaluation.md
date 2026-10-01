# Evaluación operativa de Revenue Copilot

Este documento fija la siguiente fase de observabilidad y aceptación. Los objetivos son
propuestos para el entorno local/primer despliegue y deben recalibrarse con una semana de
tráfico real.

## Instrumentación disponible

Cada respuesta de `POST /api/assistant/chat` conserva un `requestId` y registra, sin guardar
el prompt ni los datos de hoteles, estos campos:

| Señal | Uso |
| --- | --- |
| `model`, `outcome` | comparar calidad y fallos por modelo |
| `latencyMs`, `endpointLatencyMs` | separar proveedor de preparación local |
| `attempts`, `retryCount`, `providerStatusCodes`, `attemptLatenciesMs` | medir saturación y reintentos |
| `toolRounds`, `toolCalls`, `toolErrors`, `toolLatencyMs` | evaluar selección y coste de herramientas |
| `contextChars`, `historyTurns`, `messageCount` | detectar payloads sobredimensionados |
| `usage` | contrastar tokens previstos y consumidos |

El cliente recibe una versión no sensible de estas señales en `dataMeta`; los errores devuelven
el `requestId` para correlacionar soporte y logs.

## Matriz de evaluación

| Dimensión | Prueba | Criterio inicial |
| --- | --- | --- |
| Grounding | 20 preguntas con cifras presentes/ausentes | ≥95% de cifras verificables; nunca inventar |
| Tool calling | 10 hoteles fuera del resumen + 10 rutas | ≥90% selecciona la herramienta correcta |
| Vigencia | datos frescos, caducados y sin fecha | advertencia antes de recomendar |
| Histórico | consultas con 0, 4 y 8 turnos | no superar 8 turnos ni perder la zona activa |
| Resiliencia | 400, 401, 404, 429 y 5xx simulados | error accionable; reintento solo en transitorios |
| Latencia | consulta rápida, análisis y decisión | cumplir los SLO propuestos |
| UX | espera, cancelación, error y reintento | estado visible y sin bloqueo permanente |

## SLO inicial propuesto

- p50 ≤ 4 s y p95 ≤ 12 s para respuestas exitosas.
- Error de proveedor ≤ 5% semanal; `429` separado de errores de credencial/configuración.
- 98% de llamadas de herramienta sin error y ninguna herramienta fuera de la allowlist.
- Contexto ≤ 12.000 caracteres en p95; histórico limitado a 8 turnos.
- 100% de respuestas con `requestId`, estado de vigencia y fuente de datos.

## Estrategia automática de modelos

El usuario no selecciona el modelo. El router local inspecciona la intención, los turnos
previos, los adjuntos y los dominios necesarios antes de ejecutar la consulta:

| Señal | Modelo por defecto |
| --- | --- |
| Pregunta acotada | `openai/gpt-5.6-luna` |
| Revenue hotelero y herramientas | `minimax/minimax-m3` |
| Síntesis compleja o decisión | `deepseek/deepseek-v4-pro-0813` |
| PDF, imagen o revisión independiente | `google/gemini-3.8-flash` |
| Conectividad aérea | `z-ai/glm-5.3-flash` |

`openai/gpt-5.6-sol`, `openai/gpt-6-astra`, `anthropic/claude-sonnet-5` y el antiguo
`openai/gpt-5.6-terra` están excluidos del enrutado nuevo. Los overrides del entorno y los
workers se sanitizan para que una configuración antigua no los reactive. Si un endpoint no
está disponible se registra el fallback económico y no se eliminan las herramientas que
aportan evidencia.

La promoción de un candidato exige repetir esta matriz con contexto congelado y comparar
grounding, exactitud numérica, herramientas, español, latencia y coste de la tarea completa;
el precio por token aislado no demuestra equivalencia.

## Rollout y rollback

1. Ejecutar la matriz con datos congelados y guardar resultados junto al `requestId`.
2. Activar el modelo de calidad solo para un porcentaje pequeño del equipo de revenue.
3. Volver a la versión anterior mediante el backup de fase si p95, error o grounding empeoran.
