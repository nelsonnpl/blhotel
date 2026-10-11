# Validación de Atlas UI

Revisión final: 12 de octubre de 2026, Atlantic/Canary. Rama `v2`; referencia anterior `fcfd08a`. Se mantiene Atlas azul, Archivo y Space Mono, Flask/Jinja/JavaScript, dos temas y tres densidades. No se añaden dependencias ni se modifican APIs, esquemas o cálculos.

## Backup y restauración

Backup local previo a los cambios: `backups/ui-before-20261011-230313/`.

Contiene código y configuración local en `source.tar.gz`, historial completo en `repository.bundle`, copia consistente de SQLite y `.env` local. El archivo de código se verificó contra sus 668 archivos originales; `git bundle verify`, `PRAGMA integrity_check` y todas las sumas SHA-256 pasaron. Directorio con permisos 700 y archivos 600. Las instrucciones completas están en [RESTORE.md](../../backups/ui-before-20261011-230313/RESTORE.md). No subir el backup a Git.

## Pruebas

| Comprobación | Resultado |
| --- | --- |
| Backend: `.venv/bin/python -m pytest backend/tests -q` | 319 pasan |
| JavaScript: `node --test tests/` | 37 pasan |
| Dashboard | 37/37 |
| BI | 32/32 |
| Vuelos | 39/39 |
| Reputación | 29/29 |
| Copilot | 20/20 |
| Workspace | 17/17 |
| Navegación y conservación del contexto | 17/17 |
| Regresión Atlas añadida | 13/13 |
| Nombres y objetivos interactivos, 10 vistas | 0 incidencias detectadas |
| Matriz visual de escritorio | 180/180 |
| Acceso a 1024×768 en ambos temas | 20/20 |

Las pruebas funcionales cubren búsqueda, filtros, agrupación, ordenación, CSV filtrado, detalle con Enter, paneles, mapas, paginación, historial, selección enlazada, guardado simulado, modelos/adjuntos, navegación Atrás/Adelante y contexto. La prueba nueva verifica Tab/Shift+Tab, Escape y devolución de foco en el diálogo, fechas BI de al menos 24 px, estados vacío/carga/error/trabajo con respuestas controladas y contraste de texto y botón principal de al menos 4.5:1 en ambos temas. El calendario conserva el nombre del hotel al desplazarse horizontalmente y admite foco en su región desplazable.

Se ajustaron expectativas e2e antiguas de ancho y controles retirados antes de esta implementación. El test de historial de backend ahora usa una base controlada y comprueba siempre la clave del hotel, sin depender de permisos ni datos locales. El mock GET de conversaciones se corrigió para leer el historial existente.

## Evidencia visual

Carpeta local: [atlas-ui-20261011](../../artifacts/visual-qa/atlas-ui-20261011/).

- `before/`: referencia capturada antes de editar, ocho vistas a 1440×900.
- `matrix/` y `contacts/`: diez vistas, 1920×1080, 1440×900 y 1366×768, temas claro/oscuro y densidades compacta/equilibrada/espaciosa. Incluye las tres pestañas de Vuelos.
- `narrow/`: diez vistas a 1024×768 en ambos temas; tablas anchas mantienen desplazamiento horizontal.
- `states/`: vacío, carga, error, diálogo con foco, trabajo simulado, ficha BI e inspector de mapa.
- `baseline-repeat/` y `after/`: comparación equivalente con datos respaldados y mocks corregidos.
- `atlas-review-final.jpg`: aplicación final abierta en el navegador integrado.
- `qa_*.log`, `backend-tests.log`, `javascript-tests.log`: resultados completos.

Se inspeccionaron las composiciones visuales, envoltura, columnas, scroll y controles. No se detectaron solapamientos ni desbordes de página en la matriz. Los textos extensos siguen disponibles en detalles; se mantiene la elipsis donde ya existía. Las teselas cartográficas externas tienen carga variable: no forman parte de la medición de disponibilidad de la vista. Esta revisión no constituye una certificación WCAG ni prueba de servicios externos.

A 1440×900, la tabla de Hoteles comienza a 361.14 px frente a 416 px: altura visible 538.86 frente a 484 px (+11.3 %). Reputación comienza a 287.14 frente a 324 px: altura visible 612.86 frente a 576 px (+6.4 %). Se conservan filas, columnas y densidades.

## Recursos y tiempos

Compresión gzip nivel 6, igual que Flask. CSS anterior: 38.407 B; nuevo: 38.870 B. JavaScript anterior: 134.961 B; nuevo: 134.800 B. Total: **173.368 → 173.670 B (+0.17 %)**, por debajo del límite de +5 %.

Cinco navegaciones por vista, Chromium, contexto nuevo sin caché de navegador, 1440×900, tema claro, densidad equilibrada, movimiento reducido, misma copia de datos y mismas respuestas controladas. La referencia sirve CSS/JS extraídos del backup, verificados también con gzip. Se mide desde navegación hasta selector de vista disponible y fuentes cargadas; no se esperan teselas externas. Ejecuciones secuenciales, sin otra batería simultánea. Son tiempos locales, no un benchmark de producción.

| Vista | Mediana anterior (ms) | Mediana nueva (ms) | Cambio |
| --- | ---: | ---: | ---: |
| Dashboard | 109.8 | 115.2 | +4.9 % |
| Hoteles | 90.1 | 91.6 | +1.7 % |
| BI | 173.6 | 157.0 | -9.6 % |
| Reputación | 84.8 | 88.9 | +4.8 % |
| Vuelos | 118.1 | 122.7 | +3.9 % |
| Copilot | 82.2 | 76.5 | -6.9 % |
| Workspace | 129.9 | 127.7 | -1.7 % |
| Capturas | 62.4 | 59.0 | -5.4 % |

No hay regresiones superiores al 10 %. Las cinco observaciones de cada vista están en los archivos `measure.json` de `baseline-repeat/` y `after/`.

## Revisión local e incidencia de aislamiento

La aplicación queda en [127.0.0.1:5063](http://127.0.0.1:5063/#dashboard), usando SQLite temporal. El lanzador local ignorado `artifacts/visual-qa/atlas-ui-20261011/preview.py` no carga `.env` y bloquea escrituras/capturas/IA en el servidor; sólo permite el POST de analítica de lectura. Los tests interceptan además sus operaciones de escritura. El archivo `preview-db.txt` identifica la copia temporal. El bloqueo es exclusivo de la revisión, no modifica el comportamiento del proyecto.

Durante la revisión inicial se detectaron trabajos reales de captura en la primera copia temporal. Se detuvo ese servidor, se conservó esa copia fuera del proyecto y se creó una nueva desde el backup con bloqueo de escrituras. Se repitieron las pruebas afectadas y toda la matriz visual. La base original, el backup y la copia final mantienen 48 fotos, última ID 48; la original y la copia final no contienen trabajos creados el 11 de octubre. No se verifican servicios externos ni se afirma que la primera revisión estuviera completamente aislada.

La implementación se guarda en commits por fase en `v2`. `main` y producción permanecen sin cambios. Los cambios de Booking GraphQL presentes simultáneamente en el directorio de trabajo quedan fuera de estos commits de UI.
