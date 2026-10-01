# Proyectos open source y evolución de RIU Market Desk

Fecha de consulta: 22 de septiembre de 2026. Investigación realizada con tres agentes especializados y revisión de integración sobre el código local. Alcance: referencias de producto, funcionalidades, tecnologías, licencias declaradas, encaje y secuencia de implementación. Las propuestas no se han instalado ni implementado.

La recomendación principal es evolucionar la aplicación hacia una mesa de decisiones de revenue conectada al PMS. Conservar Flask, Jinja, JavaScript y los contratos de datos existentes. El siguiente salto de valor consiste en relacionar mercado, reservas propias y decisiones trazables. En la selección revisada no se ha verificado un RMS abierto maduro que sustituya directamente toda la aplicación.

## 1. Qué existe realmente y qué falta

La lectura del código tiene prioridad sobre descripciones antiguas del README. PMS significa sistema operativo de gestión del hotel; RMS, sistema de gestión y optimización de ingresos; CRS, sistema central de reservas y distribución.

| Área | Evidencia local | Implicación para la propuesta |
|---|---|---|
| Captura e histórico | Booking mediante Playwright/GraphQL, Decodo alternativo, perfiles, fotos y detalle tarifario. | Ampliar programación, cobertura y comparabilidad; aprovechar los adaptadores actuales. |
| Comparabilidad | [revenue_semantics.py](/Users/nel/Downloads/blhotel-main/backend/app/revenue_semantics.py:6) exige hotel, estancia, ocupación, habitación, régimen, divisa y cancelación. Excluye productos ambiguos. | El incremento pendiente incluye impuestos, condiciones de pago y elegibilidad; no volver a implementar los campos existentes. |
| Datos propios | No se encontró un modelo operativo conectado de reservas, habitaciones vendibles y noches materializadas. `hotel_inventory` es un catálogo de hoteles capturados. | Los precios publicados no permiten calcular ocupación, pickup o RevPAR propios. Importación PMS es el principal habilitador funcional. |
| Fuentes externas | ISTAC/Dataestur con normalización y caché; vuelos y módulos meteorológicos. | Añadir programación y controles de vigencia. Las sincronizaciones ISTAC/Dataestur aún se ejecutan dentro de sus peticiones HTTP. |
| Trabajos | [jobs.py](/Users/nel/Downloads/blhotel-main/backend/app/jobs.py:18) usa un hilo local y cola persistente; ya hay reintentos, progreso, cancelación e idempotencia. | Primero extender este mecanismo. Separar ejecución cuando haya operación continua o múltiples procesos. |
| Almacenamiento | [database.py](/Users/nel/Downloads/blhotel-main/backend/app/database.py:29) recibe un Path y usa SQLite con WAL; [Flask](/Users/nel/Downloads/blhotel-main/backend/app/flask_app.py:67) instancia SQLite. | PostgreSQL está pendiente de implementación real. Configuración y dependencia `psycopg` no acreditan soporte operativo. |
| Migración preparada parcialmente | El [script existente](/Users/nel/Downloads/blhotel-main/backend/scripts/migrate_sqlite_to_supabase.py:51) llama a Database con argumentos incompatibles con la firma actual y contiene nombres de tablas que requieren reconciliación. | No ejecutar como migración lista ni recomendar cambiar solamente una variable de entorno. |
| Espacios de trabajo | [API de workspaces](/Users/nel/Downloads/blhotel-main/backend/app/flask_app.py:850), propietario, revisión y control de versión. | Añadir compartición, comentarios y decisiones; el guardado en servidor ya existe. |
| Acceso | Identidades y permisos por mercado; el [login](/Users/nel/Downloads/blhotel-main/backend/app/flask_app.py:737) asigna el mismo usuario configurado tras comprobar una contraseña. | SSO individual para atribuir decisiones y aplicar permisos por persona. Revisar autorizaciones de escritura al evolucionar a equipo. |
| Analítica y Copilot | Catálogo semántico, consultas acotadas, evidencias, presupuestos, trazas y evaluaciones locales. | Extender pruebas y métricas; herramientas de observabilidad serían complementarias. |
| Interfaz | La plantilla activa usa `atlas.js`/`atlas.css`, gráficos SVG y MapLibre. Existen filtros, ordenación y paginación aérea. | Trabajar sobre Atlas. Una librería de tablas o gráficos debe resolver una necesidad concreta y medirse. |

La inspección fue estática y documental: no se ejecutaron capturas, pruebas con proveedores, benchmarks ni migraciones. No se atribuyen aumentos de ingresos o rendimiento a componentes que no se han probado aquí.

## 2. Proyectos comparables y qué aprovechar

Se distingue entre integrar un sistema externo, incorporar una biblioteca y tomar un patrón como referencia. Un PMS no es un sustituto funcional de nuestro análisis competitivo.

| Proyecto y licencia declarada | Qué ofrece y semejanza | Cómo aprovecharlo | Encaje y límites |
|---|---|---|---|
| [QloApps](https://github.com/Qloapps/QloApps), núcleo [OSL-3.0](https://github.com/Qloapps/QloApps/blob/develop/LICENSE.md) | PMS, reservas y operación hotelera. Complementa los datos que hoy faltan. | Adaptador Python de lectura mediante su [webservice REST/XML](https://devdocs.qloapps.com/webservice/basic-topics.html); normalizar reservas, estados y disponibilidad para series diarias propias. | Prioritario como referencia y posible entorno de prueba. Conectar el PMS real del hotel; no implantar QloApps únicamente para alimentar métricas. No asumir que todos los complementos comerciales pertenecen al núcleo abierto. |
| [HAIP](https://github.com/TelivityAI/haip), [Apache-2.0](https://github.com/TelivityAI/haip/blob/main/LICENSE) | PMS con agentes y funciones de revenue. Su [pricing](https://github.com/TelivityAI/haip/blob/main/apps/api/src/modules/agent/pricing/pricing.models.ts) contiene suelo/techo y ajustes por demanda, ritmo y antelación. | Diseñar un servicio Python de recomendaciones deterministas, con parámetros versionados, explicación y revisión humana; validar con datos propios. | Referencia experimental relevante; proyecto reciente. Las reglas observadas no prueban elasticidad ni optimización de ingresos. `inPMS` deriva de HAIP: no contarlos como dos validaciones independientes. |
| [OCA / vertical-hotel](https://github.com/OCA/vertical-hotel), AGPL-3.0 a nivel de repositorio; comprobar manifiesto de cada módulo | Gestión hotelera modular sobre Odoo: reservas, folios y operación. | Adaptador de lectura si el hotel ya usa Odoo; diferenciar inventario físico, habitaciones bloqueadas y noches vendidas. | Condicionado al sistema operativo del hotel. Introducir un ERP completo solo para la analítica aumentaría complejidad. [Detalle de módulos y licencias](https://github.com/OCA/vertical-hotel/blob/18.0/README.md). |
| [HotelDruid](https://www.hoteldruid.com/), núcleo AGPL | PMS con tarifas, reglas de asignación y estadísticas operativas. | Referencia para restricciones y disponibilidad vendible. Si existe instalado, acordar exportación o adaptador específico. | Usar la [distribución oficial](https://www.hoteldruid.com/es/download.html), no inferir abandono desde un espejo GitHub antiguo. El fabricante distingue módulos propietarios de booking engine/channel manager. |
| [Flight Finder](https://github.com/affromero/flight-finder), [MIT](https://github.com/affromero/flight-finder/blob/main/LICENSE) | Seguimiento de vuelos y hoteles, históricos y alertas sobre búsquedas guardadas. Es cercano a nuestra capa de observación de precios. | Añadir listas de seguimiento de hotel/ruta/estancia, umbrales y estado de cada comprobación sobre nuestros conectores y firmas comparables. | Alto valor como patrón de producto. Su orientación es al viajero; no acredita demanda hotelera. Conservar las fuentes y condiciones de acceso de nuestro proyecto. |
| [AWS Sample AI Hotel Revenue Management](https://github.com/aws-samples/sample-ai-hotel-revenue-management-system), MIT-0 | Ejemplo Flask/CrewAI/Bedrock de herramientas especializadas de mercado, demanda y pricing. | Estudiar la separación de herramientas; mantener nuestro routing, contratos y evidencias. | Demostrador, no motor productivo verificado: [market_tools](https://github.com/aws-samples/sample-ai-hotel-revenue-management-system/blob/main/hotel_revenue_optimization/src/hotel_revenue_optimization/tools/market_tools.py) usa datos simulados y [demand_tools](https://github.com/aws-samples/sample-ai-hotel-revenue-management-system/blob/main/hotel_revenue_optimization/src/hotel_revenue_optimization/tools/demand_tools.py) contiene resultados estáticos. No justifica migrar a CrewAI ni contratar AWS. |

Referencias condicionadas o excluidas: [Solidres](https://www.solidres.com/) aporta patrones de calendario y conciliación, pero hay que comprobar el paquete y módulos concretos antes de incorporarlo. [edubu2/hotel-revman-system](https://github.com/edubu2/hotel-revman-system) es académico y no se verificó licencia explícita reutilizable. [Channex](https://channex.io/policy) ofrece conectividad comercial: una API denominada abierta no convierte el servicio en open source.

## 3. Tabla de funcionalidades propuestas

Prioridades: **P1**, siguiente incremento; **P2**, después de la base de datos y operación necesarias; **P3**, evolución avanzada. Esfuerzo relativo de implementación y validación: bajo, medio o alto. No son estimaciones de calendario; acceso al PMS, despliegue y número de usuarios siguen sin concretarse.

| Aspecto a incluir o ampliar | Cómo implementarlo en este proyecto | Cómo ayuda | Prioridad / esfuerzo |
|---|---|---|---|
| Reservas e inventario propios | Importador CSV/XLSX primero o API del PMS. Nuevas entidades de propiedad, habitación, reserva, estado y disponibilidad diaria. Clave de origen idempotente; reconciliación y tratamiento de cancelaciones/modificaciones. Reutilizar Pydantic y openpyxl. | Habilita ocupación, reservas confirmadas, pickup, ritmo de ventas y revenue propios. | P1 / alto |
| Capturas recurrentes | Configuración por mercado, perfil, frecuencia, zona horaria y presupuesto. Planificador único que encole trabajos existentes; historial de ejecución y prevención de solapamientos. | Reduce intervención manual y huecos en el histórico. | P1 / medio |
| Centro de calidad | Registrar regla fallida, fuente, lote, cobertura, antigüedad y registros afectados; mostrar incidencias desde Capturas. Ampliar validaciones existentes. | Explica por qué falta un dato o una comparación y evita decisiones sobre información inválida. | P1 / medio |
| Seguimiento y alertas persistentes | Listas de hoteles/rutas/fechas; reglas sobre variación comparable, caducidad, captura fallida y cobertura. Guardar evento, evidencia, responsable, deduplicación y resolución. | Transforma señales temporales del dashboard en trabajo que se puede atender y cerrar. | P1 / medio |
| Navegación adaptativa con Jev | Integrar [Jev Ultrafast](https://github.com/browser-use/jev-ultrafast) en el trabajo de captura para decidir acciones acotadas como `CLICK`, `SCROLL_DOWN`, `WAIT`, `DONE` o `BLOCKED`. Después de cada acción, comprobar que la página sigue fresca y que el control pertenece al conjunto observado. | Reduce la fragilidad cuando cambia la posición del botón de reseñas, el diálogo o la paginación de Google. El contenido se extrae con un parser determinista, no con el modelo. | P1 para el prototipo / medio |
| Sets competitivos editables | Persistir miembros, vigencia y criterios del set por hotel/mercado. Reutilizar catálogo hotelero y filtros; comparar series bajo la misma versión del set. | Mejora pertinencia del benchmark y permite explicar cambios debidos a composición. | P1 / medio |
| Comparabilidad tarifaria ampliada | Añadir impuestos, precio total verificable, pago, elegibilidad y restricciones cuando la fuente los aporte. Versionar firma de producto y conservar desconocidos. | Reduce diferencias falsas por condiciones distintas. No convierte campos desconocidos en equivalentes. | P1 / medio-alto |
| Calendario comercial unificado | Matriz hotel × fecha de estancia con captura, precio, cobertura, eventos documentados y reservas propias cuando existan. Registrar fuente y ventana de vigencia de eventos. | Permite priorizar fechas concretas y ver evidencias juntas. Un evento no implica por sí solo demanda adicional. | P1–P2 / medio |
| Registro de decisiones | Entidades de recomendación, revisión, comentario y resultado, vinculadas a workspace/revisión/foto/evidencia; estados propuesta, revisada, aprobada, rechazada y expirada. | Permite saber qué se decidió, con qué datos, quién lo revisó y qué ocurrió después. | P1 / medio |
| Colaboración e identidad individual | SSO, ACL de workspace, responsable, comentarios y revisión prevista sobre las revisiones existentes. Mantener control de concurrencia. | El equipo comparte análisis sin perder autoría ni sobrescribir decisiones. | P1 si hay equipo / medio-alto |
| Pickup y pace reales | Snapshots de reservas a igual fecha de estancia y antelación. Separar nuevas reservas, cancelaciones y cambios. Definir bruto y neto; no llamarlo variación de precios OTA. | Detecta adelanto o retraso del negocio propio frente a históricos comparables. | P2, depende de PMS / medio |
| Ingreso neto por canal | Importar ingresos, comisiones y costes disponibles; separar reservas previstas de estancias materializadas y explicar costes ausentes. | Compara aportación económica de los canales, más allá de su tarifa bruta. | P2, depende de PMS/costes / medio-alto |
| Forecast y recomendaciones | Baseline estacional y modelos evaluados temporalmente; reglas con suelo/techo, horizonte y límite de cambio; guardar versión y aprobación. | Anticipa evolución y permite evaluar recomendaciones con incertidumbre explícita. | P2–P3, depende de histórico / alto |
| Publicación y conciliación CRS | Adaptador específico, simulación previa, permiso de aprobación, clave idempotente, lectura de confirmación y registro de errores. Reversión solo si la API y estado del destino la permiten. | Cierra el circuito entre decisión y tarifa realmente publicada. | P3, depende de contrato/API / alto |

## 4. Tabla de tecnologías incorporables

Las licencias se refieren a los repositorios o núcleos indicados, no a todos los servicios comerciales asociados. Las integraciones siguientes son propuestas de diseño para nuestro código.

| Tecnología / licencia | Cómo implementarla | Mejora específica y condición de adopción | Prioridad / esfuerzo |
|---|---|---|---|
| [Pydantic](https://github.com/pydantic/pydantic), MIT, **ya incluido** | Extender modelos de ingesta y reglas de moneda, unidad, fecha, duplicados y procedencia; registrar rechazos por lote. | Calidad verificable sin nueva dependencia. Empezar aquí antes de añadir motores de calidad. | P1 / bajo-medio |
| [APScheduler](https://github.com/agronholm/apscheduler), MIT | Usar rama estable 3.x en proceso único para encolar capturas; configurar zona horaria, ejecución perdida y prevención de solapamientos. Timer del sistema como alternativa mínima. | Históricos regulares. [No compartir un job store entre varios schedulers 3.x](https://apscheduler.readthedocs.io/en/3.x/faq.html); no iniciar uno por worker web. | P1 / medio |
| [Apprise](https://github.com/caronc/apprise), BSD-2-Clause | Adaptador de entrega desde trabajos, con reglas/eventos propios en DB, destinos configurados, deduplicación y reintentos. | Notificaciones multicanal con menos código por proveedor. Para un único webhook puede bastar HTTPX existente. | P1 / medio |
| [Authlib](https://github.com/authlib/authlib), BSD-3-Clause; [Keycloak](https://github.com/keycloak/keycloak), Apache-2.0 | Cliente OIDC Flask; mapear emisor/identificador estable a identidad y permisos. Conectar IdP corporativo existente; desplegar Keycloak solo si hace falta uno. | SSO individual, bajas y MFA desde el proveedor; autoría fiable de decisiones. | P1 si hay equipo / medio-alto |
| [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz), MIT | Sugerir correspondencias de nombres entre PMS, Booking y otras fuentes, junto con ubicación/identificadores. Guardar mapeos aprobados y excepciones. | Reduce conciliación manual. Similitud textual no demuestra identidad ni equivalencia tarifaria; revisión humana en ambiguos. | P2 con nuevas fuentes / medio |
| [Prometheus Python Client](https://github.com/prometheus/client_python), Apache-2.0 | Instrumentar latencia, espera, fallos, reintentos y última captura válida. Endpoint interno y etiquetas acotadas; excluir IDs por hotel/job. | Hace visibles caídas y obsolescencia, y permite medir mejoras. Reutilizar monitorización existente si la hay. | P1–P2 / bajo-medio |
| [RQ](https://github.com/rq/rq), BSD-2-Clause + [Valkey](https://github.com/valkey-io/valkey), BSD-3-Clause | Extraer handlers de Flask; adaptador de cola que preserve API y estados; workers separados y concurrencia por proveedor. Conservar cancelación y deduplicación explícitas. | Independencia respecto al servidor web. RQ declara compatibilidad Valkey y dispone de cron; si se elige, evitar otro planificador redundante. | P2 para operación continua / medio-alto |
| [PostgreSQL](https://www.postgresql.org/about/licence/), PostgreSQL License | Implementar repositorio real, dialecto SQL/migraciones y pruebas de integridad. Rehacer y verificar el script actual; mantener ruta de restauración. | Almacenamiento compartido y escrituras concurrentes entre servicios. Adoptar por necesidad de despliegue, no por una expectativa genérica de velocidad. | P2 al escalar / alto |
| [OpenTelemetry Python](https://github.com/open-telemetry/opentelemetry-python), Apache-2.0 | Instrumentación Flask/HTTP y spans en captura, parser, DB y Copilot; propagar traza al worker. Metadatos técnicos sin cuerpos de conversación o huéspedes. | Localiza la causa de latencia o fallo. Complementa métricas agregadas; especialmente útil con workers separados. | P2 / medio |
| [Tabulator](https://github.com/tabulator-tables/tabulator), MIT | Piloto en Explorador sobre APIs actuales; assets fijados y servidos localmente; persistir configuración de columnas en workspace. Probar teclado y lector de pantalla. | Selección/copia de celdas y manejo de tablas complejas. Medir antes/después; filtros y ordenación básicos ya existen. | P2, necesidad medida / medio |
| [DuckDB](https://github.com/duckdb/duckdb), MIT | Exportaciones incrementales a Parquet y módulo analítico separado; servir agregados mediante Flask. Mantener DB operativa como fuente de verdad. | Análisis histórico y cruces extensos cuando las consultas actuales sean insuficientes. Primero índices y consultas SQL existentes. | P2, volumen medido / medio |
| [StatsForecast](https://github.com/Nixtla/statsforecast), Apache-2.0 | SeasonalNaive frente a AutoETS/AutoARIMA, evaluación temporal, intervalos y resultados versionados; ejecución en worker. | Forecast contrastable de variables observadas del hotel. Forecast de ventas realizadas no equivale automáticamente a demanda no restringida. | P2–P3, PMS e histórico / alto |
| [Promptfoo](https://github.com/promptfoo/promptfoo), MIT | [Adaptador Python](https://www.promptfoo.dev/docs/providers/python/) al Copilot real con fixtures; ejecutar comparaciones en CI, presupuesto explícito para modelos remotos. | Matriz reproducible de modelos/configuraciones y regresiones semánticas. Ampliar primero pytest existente; Node solo en herramienta CI si se adopta. | P2 / bajo-medio |
| [Langfuse Community](https://github.com/langfuse/langfuse), MIT salvo componentes `ee` | Instrumentación manual de router/expertos/síntesis; inicialmente solo tokens, latencia, coste, evidencia y resultado. Preservar auditoría sin texto y [enmascarado](https://langfuse.com/docs/observability/features/masking). | Consola de diagnóstico y evaluación del Copilot; coste operativo adicional de autohospedaje. El proyecto ya registra parte de esas métricas. | P2, volumen/equipo / medio-alto |
| [Apache ECharts](https://github.com/apache/echarts), Apache-2.0 | Carga bajo demanda en una vista con zoom, series y heatmap; datos del contrato semántico y tabla accesible equivalente. | Interacción temporal avanzada. Mantener SVG sencillos existentes y huecos donde no haya observaciones. | P3, necesidad demostrada / medio |
| [dlt](https://github.com/dlt-hub/dlt), núcleo Apache-2.0 | Conectores con cursor incremental hacia staging; normalización y conciliación propias; confirmar cursores tras carga válida. | Reduce trabajo repetido con varias APIs. No contiene un conector universal de PMS; para el primero, importador específico. | P2–P3, varias fuentes / medio-alto |
| [Jev Ultrafast](https://github.com/browser-use/jev-ultrafast), MIT | Ejecutar un proceso separado que reciba una URL de Google Hotels/Maps y un objetivo limitado: localizar el hotel, abrir reseñas, desplazarse y finalizar cuando el contenido visible esté listo. Requiere `TYPESAFE_API_KEY` y, para texto, un proveedor separado; su interfaz Python usa `Agent`. | Hace la navegación más resistente a cambios de interfaz. La aplicación debe validar cada acción, imponer límite de pasos/tiempo, detenerse ante `BLOCKED` o CAPTCHA y verificar el resultado antes de persistir. No usarlo para saltarse controles, hacer login automatizado o generar el contenido extraído. | P1 para prototipo / medio |
| [Google OR-Tools](https://github.com/google/or-tools), Apache-2.0 | Servicio Python de escenarios con función objetivo, costes, capacidades y restricciones explícitas; comenzar por un problema acotado y contrastable. | Puede ayudar en asignación de inventario/mix y evaluación de grupos. No aprende elasticidad ni produce tarifa óptima por instalarlo. | P3, modelo de negocio validado / alto |

## 5. Integración gradual

Mantener separadas tres familias de hechos: mercado observado, contexto externo y operación propia. Relacionarlas por propiedad, geografía y tiempo, sin sobrescribir su procedencia o granularidad.

Modelo adicional propuesto:

```text
property / source_property_mapping
booking_event / booking_daily_snapshot / inventory_daily
capture_schedule / capture_schedule_run
quality_issue / watchlist / alert_rule / alert_event / notification_delivery
recommendation / decision_revision / approval / publication_event
forecast_run / forecast_value / forecast_evaluation
```

Estos nombres son propuestas, no tablas implementadas. `hotel_inventory` actual no debe reinterpretarse como inventario propio de habitaciones.

Cada reserva necesita identificador de origen, modificación, fecha de conocimiento, fechas de estancia, estado, unidades e ingreso con moneda y tratamiento fiscal definidos. Para reconstruir pace histórico se requieren cambios históricos o snapshots; una exportación actual aislada no reconstruye todas las cancelaciones pasadas. Para analítica de revenue normalmente bastan identificadores operativos sin nombres de huéspedes.

Conservar fecha de observación y fecha de estancia por separado. Al validar predicciones, usar únicamente información que estaba disponible en el momento de pronosticar. Los datos meteorológicos revisados, eventos añadidos después o cancelaciones conocidas a posteriori no pueden entrar retrospectivamente como información disponible entonces.

Los nuevos módulos pueden extraerse como servicios Python detrás de las rutas existentes. `database.py`, `flask_app.py` y `atlas.js` concentran mucha funcionalidad: aprovechar cada incremento para separar responsabilidades acotadas, manteniendo contratos y comportamiento, sin una reescritura general.

### Papel de Jev en el scraper de reseñas

Jev debe actuar como controlador de navegación, no como fuente de verdad del dato. El flujo recomendado es:

```text
URL / hotel objetivo
        ↓
Playwright observa controles visibles
        ↓
Jev elige una acción acotada
        ↓
la aplicación valida página y objetivo
        ↓
Playwright ejecuta click / scroll / wait
        ↓
parser determinista lee reseñas visibles
        ↓
calidad, evidencia y persistencia
```

El repositorio de Jev Ultrafast documenta una acción indexada y limitada (`CLICK`, `TYPE_TEXT`, `SELECT`, `SCROLL_UP`, `SCROLL_DOWN`, `WAIT`, `DONE` y `BLOCKED`) y una integración Python mediante `Agent` ([README](https://github.com/browser-use/jev-ultrafast)). Conviene limitar el objetivo a descubrir el control de reseñas, abrir el diálogo y cargar un número pequeño de páginas. Los selectores y el parser deben seguir siendo propios, con aserciones sobre nombre del hotel, estado del diálogo y campos encontrados.

El scraper debe terminar con un estado explícito `blocked` cuando aparezca CAPTCHA, login o una página que no se pueda verificar. No se debe usar Jev para eludir controles anti automatización, introducir credenciales, descargar contenido masivo ni convertir una decisión probabilística en una acción sin validación. Jev devuelve decisiones del modelo, no garantías de que la página esté correcta; los límites de pasos, tiempo, dominios y acciones son responsabilidad de la aplicación.

## 6. Orden de ejecución y criterios de aceptación

| Entrega | Alcance recomendado | Qué debe demostrarse antes de continuar |
|---|---|---|
| A. Observación fiable | Sincronizaciones externas en la cola existente; captura recurrente; calidad y alertas persistentes. | Reinicio sin duplicar fotos; mismas condiciones de comparación; fallos visibles; reintentos acotados; alerta enlazada a evidencia y sin repetición innecesaria. |
| B. Datos propios | Importador de un PMS/CSV real; catálogo de propiedades y correspondencias; reservas e inventario; pickup/pace. | Reimportación idempotente; modificación/cancelación correctas; conciliación de noches e ingresos con origen; contratos de moneda/fechas. |
| C. Trabajo compartido | Identidad individual, permisos efectivos, comentarios, decisiones y calendario. | Autoría por persona; permisos de lectura/escritura; conflictos de edición controlados; decisiones reproducibles desde sus fuentes. |
| D. Operación continua | Workers externos, PostgreSQL si requiere despliegue, métricas y trazas. | Pruebas de concurrencia y recuperación; restauración ensayada; tiempos y errores medidos con datos representativos. |
| E. Forecast | Baseline, validación temporal, intervalos y comparación por hotel/horizonte/temporada. | Error frente al baseline, sesgo, cobertura de intervalos y limitaciones del histórico. No ocultar series insuficientes. |
| F. Decisión y ejecución | Recomendaciones versionadas, aprobación, publicación y conciliación. | Reglas y límites comprobados; registro de aprobación; idempotencia; estado de destino verificado; medición posterior. |

Las entregas B y C pueden avanzar en paralelo si hay acceso a datos y varios usuarios. La separación de workers y PostgreSQL puede adelantarse si el despliegue actual lo necesita. Las mejoras de interfaz deben cumplir la validación visual y de accesibilidad del proyecto.

Medir utilidad con tiempo para encontrar una fecha que requiere atención, porcentaje de alertas atendidas, cobertura comparable, antigüedad del último dato válido y decisiones con evidencia completa. Para modelos, añadir error temporal y sesgo. Una mejora de ingresos requiere una evaluación de negocio que controle cambios de temporada, disponibilidad y demanda; no se deduce de un dashboard más completo.

## 7. Qué dejar fuera por ahora

- Otro PMS/ERP completo dentro de Flask; integrar el sistema operativo real del hotel.
- React/Next.js o un sistema de build solo para poder añadir una tabla.
- Kafka, Kubernetes o un orquestador de datos grande sin volumen y operación que lo exijan.
- Base vectorial para métricas estructuradas que ya resuelve el catálogo semántico.
- RQ y APScheduler simultáneos para la misma responsabilidad de programación.
- Forecast de ocupación construido únicamente con precios públicos; optimización automática antes de tener datos propios y validación.
- Bibliotecas de gráficos, calidad o agentes que dupliquen capacidades existentes sin un caso verificable.

## 8. Mantenimiento y licencias

La investigación contrastó repositorios oficiales, documentación y, para varios proyectos, releases y metadatos públicos. La actividad por sí sola no prueba estabilidad ni idoneidad. Como referencias verificadas: [APScheduler 3.11.3](https://github.com/agronholm/apscheduler/releases/tag/3.11.3), [RQ v2.12](https://github.com/rq/rq/releases/tag/v2.12), [Valkey 9.1.2](https://github.com/valkey-io/valkey/releases/tag/9.1.2), [DuckDB v1.5.5](https://github.com/duckdb/duckdb/releases/tag/v1.5.5) y [StatsForecast v2.1.1](https://github.com/Nixtla/statsforecast/releases/tag/v2.1.1). Son referencias consultadas, no versiones instaladas ni una matriz de compatibilidad probada.

Antes de reutilizar código, fijar versión/commit y registrar licencia, avisos y dependencias del componente exacto. Los proyectos OSL/AGPL/GPL requieren comprobar condiciones del uso concreto; una integración por API tampoco sustituye esa revisión. Distinguir coste de licencia, autohospedaje, soporte, conectividad y consumo de APIs. Las mejoras funcionales propuestas pueden implementarse sobre nuestra arquitectura sin copiar código de otro PMS.

La selección recomendada para empezar es deliberadamente pequeña: Pydantic y cola existentes, programación recurrente y alertas; identidad individual si trabaja un equipo. El primer conector PMS aporta más capacidad de revenue que incorporar a la vez varias plataformas de IA y analítica.
