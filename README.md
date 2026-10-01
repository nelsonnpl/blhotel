# Hotel Revenue Intelligence

Aplicacion corporativa 100% servida desde Python/Flask para equipos de Revenue, Direccion Comercial y analisis hotelero. Captura precios de Booking.com, guarda snapshots historicos y convierte los datos en indicadores accionables de mercado.

## Auditoría del producto

La revisión por fases y la hoja de ruta hacia una capa RMS están en [auditoría completa 2026-09-05](docs/auditoria-completa-y-hoja-de-ruta-2026-09-05.md). Incluye el modelo de fotos, límites de interpretación, Copilot, UX/UI, limpieza de código y fuentes externas. Los detalles técnicos de cada entrega están en [fase A](docs/auditoria-fase-a-2026-09-05.md), [fase B](docs/auditoria-fase-b-2026-09-05.md), [fase C](docs/auditoria-fase-c-2026-09-05.md), [fase D](docs/auditoria-fase-d-2026-09-05.md), [fase E](docs/auditoria-fase-e-2026-09-05.md), [fase F](docs/auditoria-fase-f-2026-09-06.md), [fase G](docs/auditoria-fase-g-2026-09-06.md) y [fase H](docs/auditoria-fase-h-2026-09-06.md). El análisis específico de ISTAC y Dataestur está en [análisis ISTAC/Dataestur 2026-09-06](docs/analisis-istac-dataestur-2026-09-06.md).

## Stack actual

- Servidor: Python + Flask.
- UI: plantillas HTML/Jinja + CSS + JavaScript estatico servidos por Flask.
- Base de datos: SQLite local en `data/booking-prices.sqlite`.
- Extracción: GraphQL de Booking mediante Playwright por defecto; Decodo es alternativa con proxy.
- Tests: pytest.

No hay Next.js, Vite, Express ni runtime Node en la aplicacion.

## Instalacion

```bash
python -m pip install -r requirements.txt
```

## Configuración

Crea `.env` a partir de `.env.example`. El motor por defecto es `graphql`; configura Decodo únicamente si estableces `SCRAPER_BACKEND=decodo`:

```env
DECODO_USERNAME=tu_usuario_decodo
DECODO_PASSWORD=tu_password_decodo
DECODO_API_URL=https://scraper-api.decodo.com/v2/scrape
DECODO_LOCALE=es-es
DECODO_GEO=Spain
DECODO_PROXY_POOL=premium
SQLITE_PATH=./data/booking-prices.sqlite
```

Tambien puedes usar `DECODO_TOKEN` con el valor Base64 de `usuario:password`.

### Acceso en producción

El desarrollo local no requiere acceso. En producción la API operativa exige una sesión y la interfaz muestra la pantalla de acceso. Configura secretos distintos, largos y aleatorios:

```env
APP_ENV=production
APP_AUTH_PASSWORD=un_secreto_largo_y_unico
FLASK_SECRET_KEY=otro_secreto_largo_y_unico
```

`/api/health` permanece público y no revela rutas ni configuración interna. Despliega siempre tras HTTPS; la cookie de sesión se marca `Secure` en producción.

## Iniciar la app

```bash
python run.py
```

Abre:

```text
http://127.0.0.1:5000
```

Healthcheck:

```text
http://127.0.0.1:5000/api/health
```

## Uso operativo

1. Selecciona una o varias zonas en el selector lateral y en el modal de captura.
2. Define check-in inicial, numero de noches, semanas y limite de hoteles.
3. Pulsa `Capturar`.
4. Flask ejecuta las capturas semana a semana, avanzando 7 dias cada iteracion para cada zona seleccionada.
5. Revisa Dashboard, Area de trabajo, Capturas, Mapa y Explorador.

Las capturas hoteleras y aéreas se encolan y la interfaz muestra su progreso sin mantener abiertas las peticiones a Booking o SerpApi. Los trabajos se guardan en SQLite y se pueden consultar en `GET /api/jobs/<id>`; se crean con `POST /api/jobs/hotel-capture` y `POST /api/jobs/air-capture`. En este despliegue el worker es local al proceso Flask. Para escalar a varias réplicas conviene sustituirlo por una cola gestionada y un worker dedicado.

### Control continuo del Revenue Copilot

El contrato de routing y el data gate se evalúan localmente sin proveedores ni credenciales. Se puede guardar el resultado técnico (sin prompts ni respuestas) para consultar el último control desde `GET /api/assistant/evaluations/latest`:

```bash
python -m backend.app.copilot_evaluation --record
```

Las pruebas contra modelos reales se activan únicamente de forma explícita y pueden registrar solo métricas técnicas:

```bash
python -m backend.app.copilot_live_evaluation --live --strict --record
```

Las llamadas del Copilot se limitan por cliente con `COPILOT_REQUESTS_PER_MINUTE`. La auditoría de ejecuciones no contiene el texto de las conversaciones y se purga de forma explícita según `COPILOT_AUDIT_RETENTION_DAYS`:

```bash
python -m backend.app.copilot_maintenance --purge-audit
```

### Caché de datos públicos

Atlas conserva los precios capturados en `market_snapshots` y los indicadores
de ISTAC/Dataestur en `external_observations`, sin mezclar ambos hechos ni
guardar los ficheros originales. La caché externa se consulta y controla con:

```text
GET  /api/external/sources
GET  /api/external/observations?source=dataestur-segittur&limit=100
GET  /api/external/cache
POST /api/external/sync/dataestur-prices
POST /api/external/sync/istac
```

El endpoint de Dataestur acepta `startYear`, `startMonth`, `endYear`,
`endMonth` y `province`; siempre solicita `CCAA=Canarias`. El sincronizador
normaliza y deduplica las filas antes de escribirlas. Los cubos ISTAC
permitidos son `C00065A_000001`, `C00065A_000038`, `C00065A_000059` y
`C00065A_000060`.

## Funcionalidad revenue incluida

- ADR competitivo por noche.
- Minimo, maximo y mediana por noche.
- Ranking competitivo por hotel.
- Gap porcentual frente a la media del set.
- Movimiento de mercado frente al snapshot anterior.
- Senales accionables para Revenue Manager.
- Control de calidad y comparabilidad de datos.
- Mapa operativo con pins de precio si hay coordenadas.
- Exportacion CSV del explorador.
- Workspace personalizable por navegador.

## Zonas incluidas

- Gran Canaria (Sur): todo incluido, hoteles, piscina.
- Gran Canaria (General): todo incluido, hoteles, piscina.
- Tenerife (Sur): todo incluido, hoteles, piscina.
- Lanzarote: todo incluido, hoteles, piscina.
- Fuerteventura: todo incluido, hoteles, piscina.

Notas de viabilidad actuales:

- El flujo soporta hasta `500` hoteles solicitados por scrapeo.
- Booking puede devolver menos resultados reales por URL/filtros (ejemplo: 25-31 en varias zonas).
- En la URL actual de Fuerteventura, Booking esta devolviendo `0` cards parseables.
- En la URL enviada para Lanzarote, el parametro `ss` apunta a `Tenerife Sur`; conviene validar URL final de negocio.

## Tests

```bash
python -m pytest backend/tests -q
```

Para validar el routing de Copilot, los modelos y el control de calidad sin
consumir llamadas de OpenRouter:

```bash
python -m backend.app.copilot_evaluation
```

Para ejecutar una muestra real y limitada —una consulta por modelo configurado,
sin herramientas ni escrituras— usa explícitamente:

```bash
python -m backend.app.copilot_live_evaluation --live
```

Para añadir las cinco pruebas adversariales de precisión, atribución y límites
de confianza:

```bash
python -m backend.app.copilot_live_evaluation --live --strict
```

## Adaptar scraping si Booking cambia

El parser esta en `backend/app/booking_parser.py`. Prioriza atributos `data-testid`, normaliza precio, moneda, rating, pax y estancia, y devuelve `null` cuando un dato no aparece para no romper la captura.

Uso responsable: no se implementan evasiones, bypass de CAPTCHA ni scraping agresivo. Las peticiones pasan por Decodo y deben respetar terminos, limites y legislacion aplicable.
