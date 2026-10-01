# Auditoría completa de Atlas · 5 de septiembre de 2026

## Diagnóstico ejecutivo

Atlas es una herramienta de inteligencia de tarifas públicas para equipos de Revenue. Su unidad de verdad es una **foto de mercado**: una búsqueda con un perfil de estancia y ocupación, observada en un instante, con filas de hoteles y productos tarifarios. El histórico permite comparar el precio de una extracción con la anterior y, cuando el perfil coincide, aislar también la variación del mismo producto.

La base es adecuada para una mesa de decisión comercial y tiene una ventaja clara: comparabilidad conservadora, procedencia y control local de calidad. Todavía no es un RMS porque no conoce de forma nativa reservas propias, pickup, demanda no restringida, inventario vendible, costes de canal, forecast, restricciones ni publicación de decisiones al CRS/PMS.

La evolución correcta es añadir una capa de decisión conectada y medible antes de automatizar precios. El producto debe seguir siendo la superficie donde el revenue manager entiende qué cambió, qué evidencia lo demuestra, qué falta y qué acción propone.

## Alcance actual y límites

| Área | Estado actual | Límite operativo |
| --- | --- | --- |
| Captura | Booking GraphQL/Playwright y backend Decodo opcional; perfiles explícitos, EUR, estancia y ocupación | Cobertura dependiente de Booking, cambios de parser, límites y términos del proveedor |
| Comparación | Firma estricta por hotel, estancia, ocupación, habitación, régimen, moneda y cancelación; duplicados excluidos | No acredita impuestos, membresías, móvil, residente, pago ni todas las reglas de paridad |
| Base de datos | SQLite con fotos, filas de hoteles, detalles y metadatos de perfil; detalle enlazable por `snapshotId` | Worker local de un proceso; concurrencia y crecimiento multiusuario limitados |
| Dashboard | Mercado, ranking, movimiento, estabilidad, curva observada, mapa y oportunidades | Una foto pública no prueba ocupación, pickup, sold-out ni willingness to pay |
| Copilot | Routing local, modos rápido/análisis/decisión, control de calidad, panel MoA acotado, historial compacto y trazas | No tiene todavía evaluación de negocio, citas de evidencia estructuradas ni acciones con confirmación |
| Fuentes externas | Diseño preparado para AEMET, ISTAC, Dataestur, Aena, Eurostat y fuentes privadas contratadas | No se activan servicios de pago ni se infiere demanda hotelera desde señales indirectas |

## Correcciones realizadas por fases

- **Fase A:** semántica de comparación, mapa e inspector alineados con fotos reales; terminología y divisas más honestas.
- **Fase B:** perfil de captura explícito, barrido semanal opcional, URL normalizada, transacción atómica por foto, procedencia de detalle y política EUR.
- **Fase C:** modos del Copilot, historial compacto, ambigüedad por zona, trazas de herramientas sin argumentos y presupuesto global de contexto.
- **Fase D:** catálogo priorizado de fuentes públicas/privadas, licencias y modelo de incorporación con provenance.
- **Fase E:** inventario de código; se identifican cuatro hojas de estilo/scripts heredados sin consumidores internos y se propone retirarlos sólo después de observar tráfico.
- **Fase F:** validación en ejecución del Copilot y Capturas; se mantiene visible el selector de modo en responsive y se verifica teclado, nombres accesibles, foco y ausencia de desbordamiento.
- **Fase G:** evidencia citable para resultados de herramientas y agregación segura de sus identificadores en Copilot y MoA.
- **Fase H:** catálogo tipado de fuentes públicas y endpoint de sólo metadatos, sin llamadas externas ni credenciales.
- **Fase I:** corpus reproducible de siete preguntas de Revenue para evaluar equivalencia, perfiles, ambigüedad, vigencia, ausencia de PMS, data gate y `evidenceId`.

## UX/UI

La dirección visual actual encaja con software corporativo denso: tablas como superficie principal, jerarquía clara, controles de captura agrupados y mapas derivados de la foto que está visible. Las mejoras más valiosas son de confianza y velocidad de lectura: declarar siempre foto, fecha, perfil, moneda y cobertura; mostrar estados vacíos honestos; conservar foco y teclado; y evitar que una tarjeta decorativa desplace la tabla.

En la revisión visual se validaron dashboard, inspector, hoteles y capturas en 1440, 1920, 1366 y 993 px usando copias temporales. Queda una mejora menor: en 993 px el selector de barrido puede truncar su etiqueta aunque sigue siendo operable. La última validación visual de los controles del Copilot no pudo repetirse porque el arranque local fue rechazado por el límite de uso del entorno.

## Modelo de datos recomendado para la siguiente etapa

Conservar la foto como hecho inmutable y añadir una capa temporal de señales:

```text
capture_profile ──< market_snapshot ──< hotel_rate_detail
external_source ──< external_observation
hotel_property ──< own_inventory / booking / pickup
recommendation ──< approval ──< publication_event
```

Toda observación debe incluir fuente, instante, ventana de validez, zona horaria, dimensión geográfica, métrica, unidad, moneda, versión y hash del payload. Las reservas y el inventario propio deben tener una clave idempotente del sistema origen para poder reimportarse sin duplicar noches.

## Hoja de ruta priorizada

### 0–30 días · fiabilidad de la mesa

1. Medir tráfico de los assets heredados y retirarlos del artefacto si no tienen consumidores.
2. Añadir índices y métricas de consulta para histórico, detalle y filtros; perfilar con una copia representativa.
3. Persistir `evidenceId` por resultado de herramienta y mostrar citas estructuradas en el Copilot.
4. Crear un conjunto de evaluación reproducible para fechas, monedas, productos no equivalentes, ambigüedad y ausencia de PMS.
5. Resolver el truncado del selector estrecho y repetir QA visual del Copilot cuando el entorno permita levantar la app.

### 30–90 días · decisión conectada

1. Integrar PMS/CRS propio: inventario, OTB, pickup, cancelaciones, segmentos, canales y ADR neto.
2. Incorporar ISTAC/Dataestur como benchmark mensual y AEMET/Aena como contexto etiquetado por granularidad.
3. Crear calendario de fechas prioritarias y alertas explicables, con umbral, evidencia y responsable.
4. Versionar recomendaciones, overrides y resultado posterior; no publicar cambios automáticamente todavía.
5. Sustituir el worker local por cola y worker dedicados cuando haya más de una réplica o portfolio concurrente.

### 90–180 días · núcleo RMS acotado

1. Forecast por fecha, segmento y tipo de habitación con baseline explicable y bandas de incertidumbre.
2. Recomendación de BAR, restricciones y mix con mínimos/máximos, reglas de exclusión y aprobación.
3. Simulación de escenarios y medición de error por horizonte, hotel y temporada.
4. Publicación idempotente al CRS/channel manager sólo en ámbitos aprobados y con rollback.

### Después · automatización selectiva

Automatizar únicamente decisiones con datos propios suficientes, calidad vigente, backtesting estable y guardrails. Overbooking, grupos, displacement y optimización de beneficio deben llegar después del pricing básico y requieren contratos de datos más ricos.

## Fuentes externas de referencia

Las fuentes públicas prioritarias son [AEMET OpenData](https://opendata.aemet.es/dist/index.html), [ISTAC](https://www3.gobiernodecanarias.org/istac/statistical-visualizer/visualizer/collection.html?agencyId=ISTAC&resourceId=C00065A_000001&resourceType=collection), [Dataestur](https://www.dataestur.es/apidata/), [Aena](https://www.aena.es/es/estadisticas/inicio.html) y [Eurostat Tourism](https://ec.europa.eu/eurostat/web/tourism/information-data). Para fuentes privadas, priorizar PMS/CRS propio, benchmark competitivo contratado, schedules aéreos licenciados y eventos con derechos de redistribución.

## Validación y reversibilidad

La batería actual queda en **106 pruebas de backend y 8 de JavaScript**, con sintaxis JS y compilación Python verificadas. Las migraciones se prueban sobre SQLite temporal; la base original no se modifica. Las copias de los archivos existentes editados están en `backups/phase-a-20260905/`, `backups/phase-b-20260905/` y `backups/phase-c-20260905/`.
