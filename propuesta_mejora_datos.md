# Propuesta de mejora de datos

Fecha: 23 de agosto de 2026  
Proyecto: RIU Market Desk

## Objetivo

Ampliar el SaaS desde una herramienta de observación de precios hacia una superficie de decisión de Revenue que combine:

- Datos propios del hotel: reservas, inventario, pickup, pace, cancelaciones y rentabilidad.
- Datos competitivos: precios, disponibilidad, producto y condiciones tarifarias.
- Demanda externa: búsquedas, reservas aéreas, capacidad, eventos y meteorología.
- Contexto de destino: ocupación, gasto, estancia, conectividad y variables macroeconómicas.

La prioridad es mejorar primero la integridad, comparabilidad y trazabilidad. Añadir más campos sin saber si una captura está completa puede producir recomendaciones incorrectas.

## Fuentes externas recomendadas

### Fuentes públicas o gratuitas

| Fuente | Datos disponibles | Aplicación en Revenue | Periodicidad orientativa |
| --- | --- | --- | --- |
| [Dataestur / SEGITTUR](https://www.dataestur.es/apidata/) | Búsquedas aéreas, reservas, pasajeros, capacidad en asientos, rutas y tráfico portuario | Anticipar demanda por mercado emisor y fecha de viaje | Según conjunto de datos |
| [ISTAC](https://www.gobiernodecanarias.org/istac/datos-abiertos/documentacion-api/index.html) | Ocupación, tarifas, ingresos, capacidad, pernoctaciones, estancia, nacionalidad y gasto | Comparar RIU con isla, municipio y microdestino | Mensual o trimestral |
| [AENA](https://www.aena.es/es/estadisticas/informes-detallados.html) | Pasajeros, operaciones, aeropuertos, aerolíneas y destinos | Validar conectividad y demanda realizada | Mensual; consultas detalladas con registro |
| [AEMET OpenData](https://opendata.aemet.es/dist/index.html) | Previsión, observaciones, climatología, playas y alertas | Relacionar meteorología con pickup y cancelación | Horaria, diaria e histórica |
| [Datos Abiertos de Canarias](https://datos.canarias.es/catalogos/estadisticas/group/turismo) | Alojamientos, vivienda vacacional, turismo y agenda pública | Medir oferta alternativa y enriquecer el calendario | Depende del conjunto |
| [INE](https://www.ine.es/datosabiertos/) | Turismo, IPC, viajeros, ocupación, empleo y gasto | Contexto español y comparación nacional | Mensual o trimestral |
| [Eurostat](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/) | Turismo y economía europea | Contexto de los mercados emisores | Mensual o trimestral |
| [Banco Central Europeo](https://data.ecb.europa.eu/help/api/overview) | Divisas, inflación y tipos | Poder adquisitivo y normalización monetaria | Diaria o mensual |
| BOE y BOC | Festivos nacionales, autonómicos e insulares | Construcción del calendario de demanda | Anual y revisiones |

### Dataestur como primera integración externa

Dataestur es la fuente pública con mayor utilidad inmediata para el SaaS. Sus conjuntos permiten obtener:

- Búsquedas por fecha de inicio del viaje.
- Búsquedas por momento de búsqueda.
- Reservas por fecha de viaje.
- Reservas por momento de compra.
- Capacidad aérea medida en asientos.
- Tráfico de pasajeros.
- Destinos AENA.
- Tráfico portuario.

Señales que se pueden construir:

- Variación de búsquedas hacia Gran Canaria por mercado emisor.
- Reservas aéreas y asientos programados para la estancia observada.
- Conversión aproximada entre búsquedas y reservas.
- Mercados que aceleran o pierden demanda.
- Diferencia entre capacidad programada y tráfico realizado.

### ISTAC como referencia del destino

ISTAC ofrece datos específicos de Canarias con granularidad de isla, municipio y, en algunos conjuntos, microdestino:

- Ocupación por habitaciones y plazas.
- Tarifas, ingresos y rentabilidad.
- Capacidad alojativa.
- Pernoctaciones y estancia media.
- Viajeros por procedencia.
- Perfil y gasto del turista.
- Oferta de vivienda vacacional.

Estos datos sirven como contexto mensual. No deben mezclarse con una captura diaria de Booking como si representaran el mismo instante.

### Meteorología

AEMET puede proporcionar:

- Previsión diaria y horaria por municipio.
- Predicción para playas.
- Alertas meteorológicas.
- Observaciones de estaciones.
- Climatología histórica.
- Viento, radiación y datos marítimos.

Para medir el efecto de la meteorología conviene almacenar tanto la previsión conocida en cada momento como el tiempo finalmente observado. También puede resultar útil incorporar meteorología de los principales mercados emisores.

### Eventos y calendarios

Fuentes posibles:

- [Agenda Cultural de Canarias](https://datos.canarias.es/catalogos/general/dataset/agenda-cultural).
- Ayuntamientos, cabildos, palacios de congresos, estadios y promotores.
- [Ticketmaster Discovery API](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/).
- Festivos publicados en BOE y BOC.
- Calendarios escolares oficiales de cada mercado emisor.

La agenda pública de Canarias no debe ser la única fuente porque su actualización puede ser irregular. Cada evento debería guardar:

- Nombre y categoría.
- Fecha de inicio y fin.
- Recinto, coordenadas y distancia al hotel.
- Aforo estimado sólo cuando la fuente lo proporcione.
- Mercados potencialmente afectados.
- Fuente, fecha de actualización y nivel de confianza.

### Demanda de búsqueda

[Google Ads Historical Metrics](https://developers.google.com/google-ads/api/docs/keyword-planning/generate-historical-metrics) ofrece volumen mensual aproximado, competencia y rangos de puja por término, geografía e idioma.

Puede utilizarse para términos como:

- `hoteles Gran Canaria todo incluido`.
- `vacaciones Gran Canaria octubre`.
- Búsquedas de la marca RIU y de competidores.

Es un indicador mensual de interés y no sustituye las búsquedas aéreas por fecha de viaje de Dataestur.

## Proveedores comerciales

### Aviación

| Proveedor | Datos principales | Uso recomendado |
| --- | --- | --- |
| SerpApi | Precios, itinerarios y señales de Google Flights | Mantener para precio visible y evolución |
| [OAG](https://www.oag.com/flight-info-api) | Horarios, frecuencias, asientos por clase, cambios y estado | Capacidad y conectividad fiables |
| [Cirium](https://developer.cirium.com/apis/cirium-sky-api/schedules) | Horarios por ruta, vuelo y aeropuerto | Alternativa empresarial para programación aérea |
| [Skyscanner](https://developers.skyscanner.net/docs/flights-live-prices/quick-start) | Precios en vivo | Segunda fuente o validación de precios |
| [Amadeus](https://admin.developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/) | Ofertas, reglas tarifarias y precios | Producto aéreo reservable y validación |

Combinación recomendada:

- SerpApi para precios visibles.
- Dataestur para búsquedas, reservas y capacidad agregada.
- OAG sólo si el negocio necesita horarios y asientos diarios con mayor precisión.

El número de opciones encontradas no equivale a plazas disponibles. La capacidad no debe inferirse únicamente a partir del modelo del avión.

### Hoteles y OTA

- Booking Demand API: búsqueda, disponibilidad, productos, cargos y políticas mediante acuerdo de partner.
- [Expedia Rapid Lodging](https://developers.expediagroup.com/rapid/lodging?locale=es_ES): habitaciones, disponibilidad, impuestos, promociones y cancelación.
- Proveedores de rate shopping y market intelligence.
- Integraciones directas con channel managers o mayoristas autorizados.

Estas fuentes pueden ser más estables que una API interna no documentada, pero su inventario y precio no tienen por qué coincidir exactamente con el frontend público de una OTA.

### Benchmarking hotelero

[STR / CoStar](https://www.costargroup.com/about-us/brands/str) puede aportar benchmarking agregado de:

- Ocupación.
- ADR.
- RevPAR.
- Rendimiento del comp-set.
- Cuota de mercado y tendencias.

Es una fuente comercial de alto valor cuando el SaaS ya dispone de datos propios fiables de PMS o CRS.

### Reputación

Fuentes posibles:

- Booking Demand Reviews, si el acuerdo del partner lo permite.
- Expedia Guest Reviews.
- [Google Places API](https://developers.google.com/maps/documentation/places/web-service/op-overview).
- Encuestas y reputación propias de RIU.

Google Places tiene límites de contenido y restricciones de almacenamiento, visualización y atribución. Antes de construir un histórico de reseñas se debe revisar la licencia de cada proveedor.

## Datos propios que deben cruzarse con los externos

El mayor valor aparecerá al combinar las fuentes anteriores con:

- Reservas y cancelaciones.
- Inventario por hotel y tipología.
- Pickup y pace por horizonte.
- ADR, ocupación y RevPAR propios.
- Canal, segmento y mercado emisor.
- Coste de distribución y comisión.
- Restricciones MLOS, CTA, CTD y stop-sell.
- Tráfico y conversión del motor de reservas.

Ejemplo de una señal explicable:

```text
Suben las búsquedas aéreas
+ acelera el pickup propio
+ aumenta la capacidad programada
+ el comp-set reduce disponibilidad
+ queda poco inventario propio
= recomendación de subida con confianza alta
```

## Contrato mínimo para datos externos

Cada observación debe conservar:

```text
source
source_record_id
observed_at
period_start
period_end
published_at
retrieved_at
granularity
geography
currency
license
quality_status
raw_hash
```

También se debe guardar la versión de transformación aplicada. De este modo se puede reproducir una recomendación y evitar sesgo retrospectivo usando información que todavía no estaba publicada en la fecha analizada.

## Revisión del scraper de Booking

### Arquitectura actual

`booking.py` es principalmente un CLI, exportador y orquestador independiente. La aplicación web usa directamente:

- `backend/app/services.py`
- `backend/app/graphql_scraper.py`
- `backend/app/booking_graphql/client.py`
- `backend/app/booking_graphql/detail.py`

Además, `booking.py` guarda por defecto en `output/booking_master.db`, mientras la aplicación trabaja con `data/booking-prices.sqlite`. Mantener dos rutas de persistencia crea riesgo de esquemas y series temporales divergentes.

### Mejoras P0: integridad y trazabilidad

1. **Persistir el total real de resultados.** Booking devuelve `nbResultsTotal`, pero el adaptador utiliza `len(hotels)` como `available_results`. Esto hace que una captura limitada o parcial pueda parecer completa.
2. **Registrar captura parcial.** Guardar páginas esperadas, recibidas, fallidas, reintentos y offsets descartados.
3. **Estados explícitos.** Distinguir `available`, `unavailable`, `closed`, `not_returned`, `blocked`, `parser_error` y `unknown`.
4. **Hash del payload real.** El hash actual se genera sobre objetos ya aplanados; para auditoría debe calcularse sobre la respuesta recibida o un fragmento canónico conservado.
5. **No alimentar decisiones con capturas parciales.** Los indicadores de demanda, altas/bajas del comp-set y oportunidades deben comprobar primero la calidad de la captura.

### Mejoras P1: aprovechar información ya solicitada

La query ya solicita campos que después se descartan:

- Ciudad y UFI.
- Descripción.
- Etiqueta textual de puntuación.
- Distancia principal y playas cercanas.
- Política sin prepago.
- `roomId` y `mealPlanId`.
- Precio redondeado.
- Todos los bloques tarifarios.

El modelo interno también dispone de estrellas, cancelación hasta una fecha, ubicación, cuna y foto, pero el adaptador web no los persiste todos.

Estas son mejoras de bajo coste de red. Antes de ampliar el esquema se debe guardar una muestra controlada de respuestas y medir la cobertura real de cada campo.

### Mejoras P1: producto y tarifa comparables

El parser de búsqueda utiliza sólo el primer bloque de tarifa. Debería separar:

- Hotel.
- Habitación o producto.
- Régimen.
- Política de cancelación y pago.
- Promoción.
- Observación de precio.

Una clave de comparabilidad debería incluir, como mínimo:

```text
hotel_id
room_id o habitación normalizada
meal_plan_id o régimen normalizado
ocupación
cancelación
prepago
inventario propio o tercero
```

Esto evita comparar una habitación flexible con desayuno contra otra no reembolsable y sin desayuno.

### Datos hoteleros adicionales

En orden de utilidad:

1. Precio base, impuestos, cargos y precio total.
2. Todas las tarifas disponibles, no sólo la primera.
3. Cancelación estructurada: fecha límite, importe o noches de penalización.
4. Prepago y momento del cobro.
5. Ocupación de adultos y niños por producto.
6. Identificadores estables de habitación y régimen.
7. Promoción Genius, móvil, país u oferta anticipada.
8. Tipo de cama, vista, tamaño y amenities para comparabilidad.
9. Posición original y condición de resultado patrocinado, cuando pueda observarse de forma fiable.

### Disponibilidad y sold-out

La búsqueda actual devuelve en la práctica alojamientos con precio. La ausencia de un hotel en resultados no demuestra por sí sola que esté agotado.

Para medir compresión se necesita:

- Un universo estable de hoteles del comp-set.
- Consultar explícitamente cada hotel o una fuente de disponibilidad por IDs.
- Guardar los hoteles no encontrados con un motivo verificable.
- No convertir errores de selector o bloqueo en `sold_out`.

### Detalle hotelero

La extracción de detalle obtiene muchas tarifas, pero depende de selectores del DOM y se ejecuta hotel por hotel.

Mejoras recomendadas:

- Mantenerla para RIU y un comp-set seleccionado, no para todo el mercado.
- Concurrencia limitada de dos o tres hoteles con semáforo.
- Capturar diagnóstico de selectores en la base, no sólo en logs.
- No crear una fila vacía sin clasificar el motivo de ausencia de la tabla.
- Normalizar cancelación, régimen, ocupación y promoción.
- Añadir fixtures reales anonimizadas y pruebas de regresión de selectores.

### Rendimiento y reintentos

- El scraping GraphQL ya pagina con concurrencia limitada; se debe conservar un límite prudente.
- Los vuelos y algunos trabajos se consultan secuencialmente; conviene concurrencia acotada por proveedor.
- Un fallo aéreo tardío vuelve a ejecutar el lote completo. Debe reintentarse por ruta y continuar desde checkpoints.
- La cola reintenta trabajos sin backoff programado. Añadir backoff exponencial con jitter y clasificación entre errores recuperables y permanentes.
- Las inserciones de hoteles y vuelos realizan commits frecuentes. Para capturas grandes conviene una transacción por snapshot o lotes controlados.
- Mantener todas las capturas largas en la cola de trabajos, no en endpoints síncronos.

### Pruebas necesarias

- Parsing GraphQL con respuestas guardadas.
- Paginación completa y `nbResultsTotal`.
- Página intermedia fallida y captura parcial.
- Duplicados patrocinados sin perder la posición original.
- Varias tarifas por hotel.
- Ausencia real de disponibilidad frente a selector roto.
- Reintentos, backoff y reanudación.
- Contrato de esquema y cobertura mínima por campo.

## Plan recomendado

### Fase 1 — Fiabilidad

- Unificar la ruta de ejecución y persistencia de `booking.py` con la aplicación.
- Añadir `capture_runs` y `capture_items`.
- Corregir el total disponible y el estado parcial.
- Registrar métricas de proveedor, página, tiempo y reintentos.

### Fase 2 — Más información sin más peticiones

- Persistir los campos ya solicitados y descartados.
- Guardar todos los bloques tarifarios.
- Separar hotel, producto, tarifa y observación.

### Fase 3 — Integraciones públicas

- Dataestur.
- ISTAC.
- AEMET.
- AENA.
- Calendario de eventos y festivos.

### Fase 4 — Inteligencia avanzada

- Cruce con PMS/CRS, pickup e inventario.
- Net ADR y coste de canal.
- Evaluación de OAG para capacidad aérea.
- Evaluación de STR para benchmarking.
- Recomendaciones explicables con nivel de confianza.

## SLO iniciales

- Al menos 98% de ejecuciones sin error técnico.
- 100% de las unidades solicitadas con estado terminal.
- Cero capturas parciales etiquetadas como completas.
- Al menos 99% de filas con clave estable y contexto de búsqueda.
- Menos de 1% de duplicados tarifarios.
- Ninguna alerta de Revenue basada en información caducada, parcial o no comparable.

## Implementación aplicada — inventario estable

La captura GraphQL ahora conserva en `hotel_inventory` los atributos que no
dependen de las fechas: `hotel_id`, nombre, URL, descripción, estrellas, tipo
de alojamiento, ciudad, país, dirección, coordenadas, foto, valoración,
distancia a playa, playas cercanas, distancia principal, zona destacada y
referencia de actualización.

El inventario se identifica por `hotel_key` (slug de la ficha) y mantiene
`first_seen_at`, `last_seen_at`, `updated_at` y un porcentaje de completitud.
Cada nueva observación hace un merge que conserva los valores conocidos y sólo
rellena huecos; precio, descuento, cupos, cancelación y sold-out siguen siendo
datos de la captura dinámica.

`booking.py` conserva su dataset maestro offline y añade `--sync-web` para
publicar una captura en `data/booking-prices.sqlite`, reutilizando el mismo
adaptador que la web. La consola mezcla el inventario con la hoja de mercado y
muestra una ficha estable compacta al expandir un hotel. También queda
disponible `GET /api/hotels/inventory?hotelKey=...` para consultas puntuales.
