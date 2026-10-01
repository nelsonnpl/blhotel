# Copilot · routing económico (2026-09-10)

Esta entrega deja la selección de modelo bajo control de Atlas. El frontend solo muestra
«Selección automática»; el backend decide después de recuperar el ámbito de la conversación
y sus adjuntos.

## Roles activos

| Rol | Slug | Uso |
| --- | --- | --- |
| Consulta breve | `openai/gpt-5.6-luna` | Lecturas directas y seguimientos sencillos |
| Revenue hotelero | `minimax/minimax-m3` | Herramientas, hoteles y análisis habitual |
| Síntesis | `deepseek/deepseek-v4-pro-0813` | Dependencias entre señales y decisiones condicionadas |
| Revisión/documentos | `google/gemini-3.8-flash` | Imágenes, PDF y contraste independiente |
| Aéreo | `z-ai/glm-5.3-flash` | Conectividad observada |

Sol, Astra, Claude y Terra quedan fuera de selección nueva. Pueden aparecer en trazas
históricas, pero no se reactivan mediante variables de entorno, workers ni fallbacks.

## Controles entregados

- El router considera los últimos turnos del usuario, el dominio y los adjuntos.
- El ámbito de mercado se impone en cada herramienta y se conserva la evidencia por mensaje.
- Se limitan las tareas a seis rondas y doce llamadas de herramientas.
- Los errores 400 no reintentan quitando herramientas; solo se reintentan errores transitorios.
- Cada tarea reserva 0,50 USD (2 USD si es ampliada) y la libera al conciliar el coste real; el
  endpoint de presupuesto incluye reservas en curso y avisa al alcanzar el 80 %.
- Un `requestId` evita duplicar trabajos de Copilot y se mantiene un trabajo activo por sesión.
- La UI conserva borradores en `sessionStorage`, distingue estados de lectura de archivos y
  permite abrir Resultado, Fuentes y Archivos sin comprimir el chat por debajo de 600 px.
- Las llamadas piden `require_parameters`, `data_collection` y `zdr` al endpoint de OpenRouter.
  Cuando `OPENROUTER_DATA_COLLECTION=allow`, `OPENROUTER_ZDR` debe declararse
  explícitamente; el entorno local lo fija en `false` para no descartar los
  endpoints económicos que no ofrecen ZDR. Si una organización exige retención
  cero, debe usar `OPENROUTER_ZDR=true` y un endpoint del modelo que la soporte.

## Validación de esta fase

- 179 pruebas de backend pasan.
- JavaScript y Python compilan sin errores.
- Playwright en Chromium comprobó 1920×1080, 1440×900, 1366×768 y 1024×768: sin
  desbordamiento horizontal, sin selector de modelo, panel dividido solo cuando deja al menos
  600 px para la conversación, y panel superpuesto en tamaños menores.
- No se ha declarado equivalencia de calidad entre modelos. La evaluación real debe ejecutarse
  con el corpus de Revenue antes de cambiar el routing por defecto.
