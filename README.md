# Hotel Revenue Intelligence

Aplicacion corporativa 100% servida desde Python/Flask para equipos de Revenue, Direccion Comercial y analisis hotelero. Captura precios de Booking.com mediante Decodo, guarda snapshots historicos en SQLite y convierte los datos en indicadores accionables de mercado.

## Stack actual

- Servidor: Python 3.12 + Flask.
- UI: plantillas HTML/Jinja + CSS + JavaScript estatico servidos por Flask.
- Base de datos: SQLite local en `data/booking-prices.sqlite`.
- Extraccion: Decodo Web Scraping API con autenticacion Basic Auth.
- Tests: pytest.

No hay Next.js, Vite, Express ni runtime Node en la aplicacion.

## Instalacion

```bash
python -m pip install -r requirements.txt
```

## Configuracion

Crea `.env` a partir de `.env.example` y configura Decodo:

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

## Adaptar scraping si Booking cambia

El parser esta en `backend/app/booking_parser.py`. Prioriza atributos `data-testid`, normaliza precio, moneda, rating, pax y estancia, y devuelve `null` cuando un dato no aparece para no romper la captura.

Uso responsable: no se implementan evasiones, bypass de CAPTCHA ni scraping agresivo. Las peticiones pasan por Decodo y deben respetar terminos, limites y legislacion aplicable.

## Frontend moderno (Next.js + Tailwind + MapLibre + ECharts)

Se incluye un nuevo frontend en `web-next/` con:

- Framework: Next.js + TypeScript + Tailwind.
- Mapas: MapLibre GL JS.
- Charts: Apache ECharts.
- Consumo API: proxy interno de Next hacia Flask (`/api/revenue/*`).

### Arranque

1. Inicia backend Flask:

```bash
python run.py
```

2. En otra terminal inicia frontend Next:

```bash
cd web-next
pnpm install
pnpm dev
```

3. Abre:

```text
http://127.0.0.1:3000
```

### Build frontend

```bash
cd web-next
pnpm build
pnpm start
```
# blhotel
