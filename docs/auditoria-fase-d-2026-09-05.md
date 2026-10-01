# Auditoría fase D · fuentes externas e integraciones

Fecha de corte: 5 de septiembre de 2026  
Objetivo: seleccionar señales públicas y privadas que mejoren la decisión de revenue sin convertir Market Desk en un agregador indiscriminado.

## Criterio de selección

Una fuente entra en el producto sólo si tiene una fecha de observación clara, una cobertura geográfica útil, una licencia compatible y una relación explícita con una decisión. Cada dato debe conservar proveedor, timestamp, zona horaria, unidad, moneda, granularidad y método de actualización. Las señales externas sirven para contextualizar o priorizar; no deben presentarse como pickup, ocupación o demanda propia del hotel cuando no lo son.

## Fuentes públicas prioritarias

| Prioridad | Fuente | Señal aprovechable | Uso en Market Desk | Riesgo o límite |
| --- | --- | --- | --- | --- |
| P0 | [ISTAC · encuesta de alojamientos](https://www3.gobiernodecanarias.org/istac/statistical-visualizer/visualizer/collection.html?agencyId=ISTAC&resourceId=C00065A_000001&resourceType=collection) | Viajeros, pernoctaciones, capacidad, ocupación, tarifas, ingresos y empleo por isla/segmento | Benchmark mensual de destino, calibración de estacionalidad y detección de cambios de mercado | Publicación agregada y con revisiones; no sustituye al dato diario del hotel |
| P0 | [Dataestur / SEGITTUR API](https://www.dataestur.es/apidata/) | Indicadores turísticos nacionales, demanda, gasto y conectividad en formatos reutilizables | Capa nacional comparable y catálogo de datasets con provenance | Hay que revisar cada endpoint, periodicidad y condiciones de reutilización |
| P0 | [AEMET OpenData](https://opendata.aemet.es/dist/index.html) | Observaciones, predicción, avisos, playa y variables meteorológicas | Explicar shocks de demanda, avisos operativos y contexto de destino | Requiere API key, límites de uso y normalización de estaciones/municipios |
| P1 | [Aena · estadísticas](https://www.aena.es/es/estadisticas/inicio.html) y [aeropuerto de Gran Canaria](https://www.aena.es/es/aerolineas/aeropuertos-y-destinos/nuestros-aeropuertos/gran-canaria.html) | Pasajeros, operaciones y carga por aeropuerto/mes; rutas y destinos publicados | Indicador de accesibilidad y capacidad aérea por mercado emisor | Pasajeros no equivalen a búsquedas, reservas ni ocupación hotelera |
| P1 | [Eurostat · tourism data](https://ec.europa.eu/eurostat/web/tourism/information-data) | Llegadas, noches y ocupación comparables en Europa | Benchmark de islas/destinos y control de coherencia | Revisiones, distinta definición estadística y menor granularidad operativa |
| P1 | [Catálogo abierto de ISTAC](https://datos.canarias.es/catalogos/estadisticas/group/turismo?groups=turismo&organization=istac&res_format=JSON) | Descubrimiento de datasets en JSON/CSV/XLSX | Registro automático de fuentes y monitor de nuevas series | El catálogo no garantiza que todos los recursos tengan la misma frecuencia |
| P2 | Calendarios oficiales de eventos y datos municipales | Eventos, festivos, cierres, obras y capacidad pública | Variable explicativa y agenda de alertas por fecha | Cobertura irregular; guardar URL, fecha de consulta y estado de verificación |

La [API pública de AEMET](https://www.aemet.es/es/datos_abiertos/AEMET_OpenData) está pensada para reutilización programada. [ISTAC](https://www.gobiernodecanarias.org/istac/temas_estadisticos/sectorservicios/hosteleriayturismo/oferta/) publica series de oferta y demanda de alojamiento con histórico largo. [SEGITTUR](https://pia.segittur.es/es/espacio-de-datos) describe además un espacio para compartir datos públicos y privados, útil como referencia de gobierno y no como permiso automático para reutilizar datos de terceros.

## Fuentes privadas con mayor retorno

### P0: datos del propio hotel

La primera integración debe ser PMS/CRS/booking engine. El mínimo útil es: inventario físico y vendible por tipo de habitación, reservas on-the-books, pickup diario, cancelaciones y no-shows, room nights, ADR neto y bruto, segmento, canal, tarifa, estancia, restricciones y grupos. El conector debe importar cambios idempotentes y guardar el `sourceSystem`, el instante de extracción y la versión del registro.

Con esto se puede separar tres conceptos que hoy no deben inferirse de una foto competitiva: demanda observada, demanda no restringida y disponibilidad propia. También permite medir si una recomendación produjo pickup, ADR, RevPAR, margen o desplazamiento.

### P1: distribución y mercado contratado

- Channel manager y CRS: ARI, paridad, restricciones, reservas y coste de distribución del hotel propio.
- Benchmark competitivo contratado (por ejemplo STR/CoStar, Lighthouse o proveedor equivalente): ocupación, ADR y RevPAR de un comp set con definición y derechos de uso explícitos.
- Señales de vuelos contratadas (Amadeus, OAG, Cirium u otra fuente con licencia): capacidad futura, schedules y mercados emisores. Deben entrar como capacidad/accesibilidad, nunca como conversiones hoteleras.
- Eventos y demanda (por ejemplo PredictHQ u operador local): calendario normalizado, tamaño, probabilidad y zona de influencia.

Los nombres anteriores son categorías de integración y ejemplos de mercado. No se debe activar una compra ni almacenar datos privados hasta disponer de contrato, límites de redistribución, retención, SLA y responsable de credenciales.

## Diseño de incorporación

1. **Registro de fuente.** Crear `external_sources` con proveedor, dataset, licencia, endpoint, zona horaria, frecuencia declarada, última ejecución, estado y contacto.
2. **Observación inmutable.** Crear `external_observations` con `source_id`, `observed_at`, `valid_from`, `valid_to`, dimensión geográfica, métrica, valor, unidad, moneda, versión y hash del payload.
3. **Calidad.** Validar esquema, rango, duplicados, retraso, revisión y cobertura. No mezclar revisiones en una misma serie sin conservar versión.
4. **Alineación.** Resolver siempre fecha de estancia, fecha de observación y zona horaria por separado. La demanda aérea mensual no debe aparecer en una tarjeta diaria sin indicar el cambio de granularidad.
5. **Evidencia.** Cada insight debe devolver fuente, timestamp, consulta o dataset, ventana temporal y advertencias. La IA sólo recibe el subconjunto que corresponde a la pregunta.
6. **Backfill controlado.** Importar primero 24 meses de ISTAC/Dataestur y 12 meses de AEMET/Aena; comparar con una muestra manual antes de activar alertas.

## Orden recomendado

1. PMS/CRS del hotel propio y modelo de pickup.
2. ISTAC + Dataestur como benchmark regional/nacional.
3. AEMET y Aena como contexto diario/semanal de destino.
4. Eventos oficiales y calendario local.
5. Benchmark privado de comp set y vuelos contratados.
6. Señales de búsqueda, eventos privados y datos alternativos sólo después de medir precisión y coste.

La regla de producto es que una fuente nueva debe responder a una decisión concreta: **qué fecha priorizar, qué producto comparar, qué restricción revisar o qué explicación añadir**. Si no cambia una decisión ni mejora su confianza, debe permanecer fuera del panel operativo.

