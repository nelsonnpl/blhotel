# Implementación del módulo de vuelos con SerpAPI

## Alcance aplicado

El módulo de vuelos usa únicamente `engine=google_flights` de SerpAPI. La
captura manual trabaja con vuelos de llegada, solo ida, un adulto, turista,
EUR y mercado ES. La cobertura gradual son 14 fechas diarias y, después, una
fecha cada siete días hasta 90 días. La recurrencia automática queda fuera de
esta iteración.

## Contratos públicos

- `POST /api/air-data/capture/estimate`: calcula rutas, fechas, consultas,
  presupuesto y si la clave de SerpAPI está configurada. No realiza consultas
  externas.
- `POST /api/jobs/air-capture`: encola la captura manual. La interfaz exige
  estimar el consumo antes de habilitar el inicio.
- `GET /api/air-data?direction=arrival`: devuelve la lectura principal y solo
  vuelos directos de llegada por defecto. `direct=false` permite inspección de
  conexiones.
- `GET /api/air-data/comparison?direction=arrival`: compara las dos últimas
  fotos por ruta y fecha de salida, sin mezclar perfiles incompatibles.
- `POST /api/air-data/booking-options`: consulta las condiciones de venta de un
  itinerario seleccionado mediante `booking_token`; nunca se ejecuta en bloque.

## Trazabilidad y base de datos

Las migraciones son aditivas. `air_runs` conserva proveedor, perfil, cobertura,
estado, consultas solicitadas/completadas/fallidas y respuestas cacheadas.
`air_flights` conserva fecha y hora completas, moneda, tokens de SerpAPI,
firma estable de segmentos, equipaje, extensiones, emisiones, histórico de
precios y nivel de precio de Google.

Un itinerario sin `price` permanece sin precio. El mínimo de la consulta nunca
se copia en cada fila. El rango típico de Google se conserva como mínimo y
máximo; el punto medio se marca como valor derivado interno. Las comparaciones
solo emparejan la misma ruta, fecha de salida, perfil, moneda y filtro de
conexión.

## Estados de captura

Los estados persistidos son `running`, `completed`, `completed_no_offers`,
`partial`, `failed` y `cached`. Cada consulta admite un reintento acotado con
backoff. Una captura parcial conserva las respuestas válidas y sus errores.

## Validación realizada

- 164 pruebas backend pasan con `pytest`.
- `node --check backend/app/static/atlas.js` pasa.
- Playwright validó Chromium a 1440×900 y 1366×768: sin errores de consola,
  sin peticiones fallidas y sin desbordamiento horizontal.
- La estimación real del catálogo actual devuelve 19 rutas × 25 fechas = 475
  consultas, dentro del presupuesto visible de 500.

Una consulta real a SerpAPI no se ejecuta durante las pruebas automatizadas para
no consumir cuota; se valida con respuestas controladas y el contrato conserva
la misma forma que la respuesta de producción.
