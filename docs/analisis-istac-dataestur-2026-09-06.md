# Análisis de ISTAC y Dataestur para Market Desk

Fecha de corte: 6 de septiembre de 2026.

## Estado de la primera entrega

La Fase 1 ya está implementada en SQLite. `external_observations` guarda sólo
valores normalizados y su procedencia; no guarda los CSV, XLSX ni JSON
originales. Las claves idempotentes evitan duplicados y
`external_ingestion_runs` conserva únicamente el estado técnico de cada
descarga. La API expone:

- `GET /api/external/sources` para el catálogo gobernado;
- `GET /api/external/observations` para consultas acotadas;
- `GET /api/external/cache` para cobertura y caducidad;
- `POST /api/external/sync/dataestur-prices` para el endpoint P0 de precios;
- `POST /api/external/sync/istac` para cubos ISTAC permitidos.

La primera sincronización de Dataestur filtra a Canarias y conserva sólo las
dos tarifas de cada combinación de provincia, categoría y antelación. El
servidor no coloca estos valores en `market_snapshots`: siguen siendo contexto
estadístico separado de las fotos de Booking. Cuando hay una zona activa, el
Copilot recibe una proyección de hasta 24 observaciones relevantes con
`evidenceId`, periodo, unidad, geografía y estado de calidad; los payloads
originales nunca entran en la conversación.

## Qué aportan

ISTAC y Dataestur son señales externas de contexto y benchmark. No deben
convertirse en una nueva “foto” de precios del hotel: una foto representa una
observación de compra para un perfil y una fecha de estancia, mientras que
estas fuentes suelen ser agregados mensuales de destino, mercado o transporte.

| Fuente | Señal utilizable | Escala y latencia | Decisiones que soporta | Riesgo de interpretación |
|---|---|---|---|---|
| [ISTAC C00065A](https://datos.canarias.es/api/estadisticas/operations/v1.0/operations/C00065A) | Capacidad, viajeros, pernoctaciones, estancia media, ocupación, tarifas/ingresos y empleo del alojamiento turístico | Canarias; mensual y anual. La operación declara difusión en eDatos y actualización estadística periódica | Estacionalidad, benchmark de ocupación/ADR, lectura por isla y mercado emisor | Es un agregado; no representa el hotel, el canal ni el pickup diario |
| [ISTAC microdestinos C00065A_000038](https://datos.canarias.es/catalogos/general/dataset/establecimientos-abiertos-plazas-y-habitaciones-ofertadas-tasas-de-ocupacion-tarifa-media-ingre1/resource/065d36ba-2afa-48a5-9f55-848d1a8dff6c) | Las mismas familias con mayor detalle territorial y por residencia/nacionalidad | Islas y microdestinos; ADR/RevPAR anual en este recurso y series mensuales en recursos específicos | Comparar el destino real del hotel y detectar cambios de mix | La granularidad y el periodo disponible cambian por serie; hay que conservar la revisión |
| [Dataestur API-SEGITTUR](https://www.dataestur.es/apidata/) · `PRECIOS_ALOJAMIENTOS_HOTELEROS_DL` | Precio medio de alojamiento hotelero por antelación y momento del check-in | Mensual; disponible desde 2019-01 según el catálogo del endpoint | Calibrar curva de lead time y comparar el nivel de precio del destino | Precio medio de mercado, no una recomendación de tarifa ni un precio de una reserva individual |
| [Dataestur API-SEGITTUR](https://www.dataestur.es/apidata/) · `IND_RENTABILIDAD_PUNT_TUR_DL` | Indicadores de rentabilidad hotelera por punto turístico | Mensual; disponible desde 2021-01 según el endpoint | Contrastar ADR/RevPAR y rentabilidad del destino, por ejemplo Mogán, Pájara o Las Palmas de Gran Canaria | El punto turístico tiene cobertura distinta a la del hotel; no mezclar unidades sin homogeneizar |
| Dataestur · `CONECTIVIDAD_AEREA_BUSQUEDAS_INICIO_VIAJE_DL` | Búsquedas de vuelos según fecha de inicio del viaje, origen y destino | Mensual; la serie excluye meses incompletos y mantiene retardo de publicación | Señal temprana de intención de viaje y explicación de pickup | Búsqueda aérea no equivale a reserva hotelera ni a llegada efectiva |
| Dataestur · `CONECTIVIDAD_AEREA_RESERVAS_INICIO_VIAJE_DL` | Reservas aéreas por fecha de inicio, origen y destino | Mensual; agregada por mercado | Validar si la intención se convierte en transporte reservado | No identifica el hotel ni necesariamente al viajero final |
| Dataestur · `CONECTIVIDAD_AEREA_CAPACIDAD_DL` / `TRAFICO_PASAJEROS_DL` | Capacidad programada, operaciones y pasajeros | Mensual | Explicar shocks de conectividad y anticipar presión de demanda | Capacidad y tráfico son oferta/flujo de transporte, no demanda alojativa |
| Dataestur · `GASTO_TPV_DESTINO_PROV_MES_ACTUAL_DL` | Gasto y transacciones TPV por provincia de destino y tipo de viaje | Desde 2024-01 en el endpoint consultado | Contextualizar poder de gasto y composición del destino | Cobertura de TPV y gasto no es ocupación; la publicación puede revisar periodos |

El catálogo general de Dataestur explica que la API se consulta con parámetros,
devuelve ficheros descargables y se actualiza automáticamente; su OpenAPI
publica el servidor `/API-SEGITTUR-v2` y define los filtros de cada indicador.
Conviene respetar sus [buenas prácticas de uso](https://www.dataestur.es/wp-content/uploads/Buenas-practicas-uso-API-Dataestur.pdf),
en especial las reglas de fecha, frecuencia y descarga.

## Cómo encaja con el modelo de fotos

La aplicación debe conservar dos hechos distintos:

1. **Foto interna:** precio y disponibilidad observados para un `stayDate`,
   `capturedAt`, perfil de ocupación, canal y hotel.
2. **Observación externa:** valor publicado por una fuente para un periodo de
   validez, ubicación, mercado, métrica y unidad.

La relación se hace mediante dimensiones explícitas, nunca por una suma directa:

```text
capture_snapshot ──┐
                    ├─ analysis_context (misma fecha de estancia o mes derivado)
external_observation┘
```

Cada observación externa debe guardar al menos:

```text
sourceId, datasetId, observedAt, validFrom, validTo,
geographyType, geographyCode, originMarket, metric, unit,
value, revision, payloadHash, fetchedAt, qualityStatus
```

`validFrom/validTo` expresa el periodo estadístico; `observedAt` expresa cuándo
se publicó o se descargó. Así se evita comparar una foto diaria con un dato
mensual que todavía no existía en la fecha de la captura. `revision` y
`payloadHash` permiten reproducir una decisión cuando la estadística se revisa.

## Alcance recomendado

### P0: integración mínima con valor operativo

- Mantener el catálogo actual de fuentes (`GET /api/external/sources`).
- Mantener `external_observations` con claves idempotentes:
  `(sourceId, datasetId, period, geography, metric, revision)`; la tabla ya
  está creada y no contiene payloads originales.
- Implementar un conector de sólo lectura para **ISTAC microdestinos** y para
  **Dataestur `PRECIOS_ALOJAMIENTOS_HOTELEROS_DL`**.
- Mostrar en la vista de comparativas: valor externo, periodo, unidad, fecha de
  publicación y enlace de origen. El valor no altera el precio capturado.
- Calcular únicamente deltas y percentiles con la misma geografía y unidad;
  si falta cobertura, mostrar “sin benchmark” y no interpolar silenciosamente.

### P1: señales de explicación y demanda

- Añadir `IND_RENTABILIDAD_PUNT_TUR_DL` para benchmark de rentabilidad.
- Añadir búsquedas y reservas aéreas como series separadas de intención y
  conversión, con `signalType=air_search` o `air_booking`.
- Añadir capacidad/tráfico y TPV como contexto en una línea temporal, sin
  incorporarlos al cálculo de ocupación o ADR.

### P2: preparación RMS

- Incorporar PMS/CRS propio, cancelaciones, restricciones, inventario,
  segmentos y costes.
- Versionar features, modelo y decisión recomendada; introducir backtesting
  por fecha de estancia y controles de deriva.
- Permitir reglas de override del revenue manager y registrar el motivo.

El conector P0 de precios de Dataestur ya está activado mediante su respuesta
CSV; los endpoints de rentabilidad que entregan XLSX se dejan para P1.
`openpyxl` ya está en `requirements.txt`, por lo que no se necesita otra
dependencia para ese lector posterior.

## Flujo técnico de ingesta

1. **Planificador:** ejecuta cada fuente según su frecuencia y ventana de
   publicación; no consulta diariamente una serie mensual.
2. **Fetch con límites:** timeout, reintentos con backoff, `User-Agent`, caché
   por URL+parámetros y registro de status HTTP.
3. **Normalizador:** convierte XLSX/CSV a un contrato común, normaliza fechas,
   decimales, códigos territoriales, residencia y unidades.
4. **Validación:** rechaza filas sin periodo, unidad o geografía; marca
   `qualityStatus=partial` cuando la fuente declara cobertura incompleta.
5. **Upsert idempotente:** conserva la revisión anterior y registra el hash del
   payload; nunca sobrescribe una observación histórica sin dejar versión.
6. **Proyección para la app:** expone sólo agregados pequeños y trazables; la
   descarga original queda fuera de la conversación del Copilot.

## Uso con los modelos de IA

La IA debe recibir un contexto ya normalizado y con evidencia, no consultar
XLSX ni construir métricas desde texto libre.

- **Código determinista (Python):** ingesta, validación, joins temporales,
  percentiles, lead-time curves y cálculos de ADR/RevPAR. Estas cifras no se
  delegan al LLM.
- **Modelo rápido:** responde preguntas de lectura (“¿qué cambió esta semana?”)
  usando una proyección compacta de fotos y observaciones externas.
- **Modelo hotelero:** analiza pickup, comp set, calendario, ISTAC/Dataestur y
  propone hipótesis; debe separar hechos, inferencias y recomendación.
- **MoA Sol:** sintetiza una decisión para el revenue manager cuando hay varias
  señales, exige que cada afirmación importante incluya `evidenceId`, periodo y
  fuente, y devuelve confianza y datos faltantes.
- **Modelo Air:** interpreta búsquedas, reservas, capacidad y tráfico como
  señales de conectividad, nunca como ocupación; puede explicar un shock de
  demanda que ya aparece en las fotos.

La consulta debe construir un `context projection` con: hotel y destino,
ventana de estancia, última foto, fotos comparables, benchmark externo compatible,
calidad/latencia y enlaces de evidencia. El Copilot debe poder contestar
“no hay dato comparable” y pedir una captura o filtro adicional. Las
observaciones y respuestas se auditan con `evidenceId`, pero no se persisten
secretos ni argumentos de herramientas.

## Criterios de aceptación del primer conector

- Dos ejecuciones con el mismo payload no crean duplicados.
- Una revisión nueva conserva la anterior y muestra ambas fechas.
- Una observación mensual no se presenta como dato diario.
- Las unidades y geografías incompatibles bloquean el delta.
- El Copilot cita fuente, periodo y `evidenceId` en una respuesta con benchmark.
- Si el proveedor no responde, la UI conserva la última observación válida y
  muestra su antigüedad.

## Siguiente decisión

La infraestructura y el conector P0 de Dataestur están listos. La siguiente
entrega debe conectar las observaciones al contexto del Copilot y a la UI. Para
ISTAC se debe validar primero la estructura del cubo elegido y su cobertura en
la red de despliegue; el recurso territorial de ADR/RevPAR es
`C00065A_000038`, mientras que `C00065A_000002` es la colección que agrupa
series mensuales y anuales, no el cubo que debe insertarse directamente.
