# Atlas Google Reviews + Jev (side project)

Prototipo aislado que navega por la interfaz pública de Google Hotels y exporta reseñas visibles de Servatur Puerto Azul, Servatur Monte Feliz y Servatur Waikiki. No utiliza la API de Google ni sus endpoints internos.

Jev solo navega. El parser de `parser.py` lee el DOM visible y normaliza el resultado a `atlas.google-reviews.v1`. No se escriben las tablas de producción ni se modifican las capturas de Booking.

## Preparación opcional

Jev Ultrafast se mantiene separado del entorno de producción de Atlas. Instálalo en un directorio adyacente o temporal:

```bash
git clone https://github.com/browser-use/jev-ultrafast.git /tmp/atlas-jev-ultrafast
cd /tmp/atlas-jev-ultrafast
uv sync
uv pip install --python .venv/bin/python pydantic beautifulsoup4 langdetect
```

Configura `OPENROUTER_API_KEY` en el `.env` de Atlas. El adaptador usa el endpoint de decisiones de OpenRouter y el modelo `typesafe/jev-1.13`; se puede cambiar con `ATLAS_JEV_OPENROUTER_MODEL`. OpenRouter marca ese endpoint como alpha, así que puede cambiar.

```bash
cd /ruta/a/blhotel-main
set -a; source .env; set +a
```

También puedes usar TypeSafe directamente con `ATLAS_JEV_PROVIDER=typesafe` y `TYPESAFE_API_KEY`. El proveedor de texto de Jev solo se necesita si el navegador debe escribir en un campo; para localizar reseñas no debería hacer falta.

## Uso

### Desde Atlas

Atlas incluye la captura manual desde **Reputación**. El panel trabaja sobre el inventario de Booking ya cargado, las 993 reseñas piloto y los vínculos públicos de Google Maps/Google Hotels. Para Booking, usa su página pública de reseñas. Las claves de cada fuente se pueden corregir desde la ficha del hotel, pestaña **Capturas**; comprueba las coincidencias sugeridas antes de marcarlas como confirmadas.

La captura de Google necesita Chrome abierto con depuración remota en `127.0.0.1:9222`, Jev Ultrafast instalado aparte en `/tmp/atlas-jev-ultrafast` (o `ATLAS_JEV_PATH`) y `OPENROUTER_API_KEY` en el entorno que inicia Atlas. El sidecar usa el Python de `.venv` dentro de ese checkout, salvo que `ATLAS_JEV_PYTHON` lo cambie. La captura de Booking usa Playwright del entorno de Atlas y una sesión Chromium headless. Inicia Atlas con `python run.py`, abre **Reputación**, selecciona hotel o selección y fuentes y define máximo de reseñas, decisiones y tope estimado.

Los trabajos se ejecutan en segundo plano, guardan reseñas por bloques y se pueden volver a lanzar con deduplicación. En «Máx. reseñas» puedes elegir «Hasta agotar recorrido», equivalente a `--max-reviews 0`; no impone un máximo numérico. El trabajo conserva topes operativos: 30 minutos por captura Atlas, 400 desplazamientos de Maps y 500 páginas de Booking. Al alcanzarlos, informa `partial` para permitir otra captura con deduplicación. `exhausted` significa que terminó el recorrido observable, no que Google o Booking hayan entregado todo su historial. Si aparece una barrera, el sistema conserva el bloque recuperado y deja el estado como parcial o bloqueado. El presupuesto Jev es una estimación basada en decisiones y el precio indicado; el endpoint alpha de OpenRouter puede no informar un coste facturado. El análisis de reseñas requiere también un modelo y clave de OpenRouter configurados en Atlas. No se inicia ninguna captura ni análisis automáticamente al abrir la aplicación.

Inicia Chrome con un perfil aislado y el puerto de depuración local. En macOS:

```bash
open -na 'Google Chrome' --args \
  --user-data-dir=/tmp/atlas-google-reviews-chrome \
  --remote-debugging-port=9222 --no-first-run --no-default-browser-check
```

Desde la raíz de Atlas, ejecuta los tres hoteles y genera los CSV:

```bash
set -a; source .env; set +a
ATLAS_JEV_PROVIDER=openrouter PYTHONPATH="$PWD" \
  BU_CDP_URL=http://127.0.0.1:9222 \
  /tmp/atlas-jev-ultrafast/.venv/bin/python \
  -m side_projects.atlas_google_reviews_jev.batch --max-reviews 40
```

Los resultados se escriben en `outputs/google-reviews-results.csv` (una fila por reseña), `outputs/hotel-status.csv` (estado y totales por hotel) y un JSON por hotel, todos dentro de este directorio. Los CSV usan tabulador como separador de columnas, comillas dobles para campos que incluyan tabuladores o saltos de línea y UTF-8 con BOM. El colector combina los filtros temáticos que Google muestra con sus cuatro ordenaciones, y deduplica reseñas por ID. En las columnas `review_es` y `review_original` conserva la traducción al español mostrada por Google y el texto original; `language_original` usa códigos ISO 639-1 en mayúsculas y `UND` si no hay texto o la detección no es fiable. `translation_method` indica cómo se obtuvo el español y `language_confidence` deja visible la confianza de detección. El límite `--max-reviews` es por hotel; `0` recorre hasta agotar las vistas públicas o llegar a 400 desplazamientos de Maps. La ejecución usa llamadas reales a OpenRouter, que pueden generar cargos.

Para un solo hotel, usa su URL pública de Google Hotels:

```bash
ATLAS_JEV_PROVIDER=openrouter PYTHONPATH="$PWD" \
  BU_CDP_URL=http://127.0.0.1:9222 \
  /tmp/atlas-jev-ultrafast/.venv/bin/python \
  -m side_projects.atlas_google_reviews_jev.cli \
  --url 'https://www.google.com/travel/hotels/entity/CgsI5PHLm5bztcX7ARAB/reviews?gl=es&hl=es' \
  --hotel-name 'Servatur Puerto Azul' --max-reviews 1000 \
  --output side_projects/atlas_google_reviews_jev/outputs/servatur-puerto-azul.json
```

Google muestra actualmente Monte Feliz como «Sport Hotel Monte Feliz - powered by Playitas»; `requested_hotel` conserva «Servatur Monte Feliz» y `observed_hotel` guarda el nombre que devuelve la página. El colector elige la fuente Google y recorre las cuatro opciones públicas de ordenación, deduplicando por identificador de reseña. Una reseña de solo puntuación tiene `text` vacío.

Para probar solo el parser sin red ni Jev:

```bash
/tmp/atlas-jev-ultrafast/.venv/bin/python -m side_projects.atlas_google_reviews_jev.cli \
  --url 'https://www.google.com/maps' \
  --fixture path/to/reviews.html
```

El JSON usa `schemaVersion: atlas.google-reviews.v1` y contiene `status`, URL final, valoración agregada, número de reseñas, reseñas normalizadas, pasos de navegación y mensaje. `GoogleReviewsResult.atlas_records()` es el punto de entrada de un futuro adaptador a `database.py`.

## Límites del prototipo

- Jev trabaja con acciones acotadas y valida la página antes de ejecutar; no recibe selectores libres del modelo.
- El proceso se detiene ante CAPTCHA, login, bloqueo o una página que no se pueda verificar.
- El parser admite variantes visibles conocidas y devuelve `empty`/`parse_error` si no puede demostrar que encontró reseñas. Un cambio de DOM puede requerir actualizar selectores.
- La cantidad capturada es una muestra de las reseñas visibles en cuatro ordenaciones, no el historial completo. `reviewCount` es el total que muestra Google en la ficha y no la cantidad descargada.
- No usa endpoints RPC internos de Google, técnicas stealth, evasión de CAPTCHA ni persistencia en las tablas de producción.
- Revisar las condiciones de Google antes de usar resultados fuera de una prueba autorizada. El producto final necesitará una fuente y un uso de datos permitidos.
