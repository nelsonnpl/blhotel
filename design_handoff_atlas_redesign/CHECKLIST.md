# CHECKLIST · Rediseño Atlas

Fuente de verdad: `README.md` y los prototipos de `prototype/`. Una fila por requisito.
Formato: `- [ ] §sección · requisito · estado (hecho / parcial / falta) · archivo:función`.
Al completar una fila se marca `[x]`. Las desviaciones conscientes (datos que no existen, decisiones del usuario) se anotan con **Nota**.

Abreviaturas: `js` = `backend/app/static/atlas.js` · `css` = `backend/app/static/atlas.css` · `html` = `backend/app/templates/index.html` · `py` = `backend/app/flask_app.py`.

## Design Tokens
- [x] §Tokens · `:root` claro con los 26 tokens del README · hecho · css:`:root`
- [x] §Tokens · bloque `html[data-theme="oscuro"]` con los valores oscuros · hecho · css:`html[data-theme="oscuro"]`
- [x] §Tokens · mapas cambian de estilo positron ↔ dark-matter con `setStyle` (no filtros CSS) · hecho · js:`atlasMapStyle`, `restyleMaps`
- [x] §Tokens · semáforo fijo de mapas `#1f7a52 / #c98a1e / #b94f50` en Dashboard y BI · hecho · js:`renderDashboardHotelMap`, `renderBiMap`
- [ ] §Tokens · tramos de ruta aérea `#9bcfaf / #e7c66c / #df9898` · falta · css:`.air-position__*`
- [x] §Tokens · celdas de calor con alfa ≤ .6 (verde bajo / rojo sobre / `--line-soft` ±5 %) · hecho · js:`biHeatBg`
- [x] §Tokens · densidad `--rp` 8/13/18 px con `body[data-density]` · hecho · css:`body[data-density]`
- [x] §Tokens · tipografía Archivo + Space Mono con los roles de la tabla · hecho · css
- [x] §Tokens · radios (14/12/8–9/9–7/5/999/10/14) · hecho · css
- [x] §Tokens · sombras (menú, paleta, aviso, panel lateral, ventana de mapa, primario, segmentado) · hecho · css:`--shadow-*`
- [x] §Tokens · espaciado de página `28px 32px 48px`, bloques 16/14 px · hecho · css:`.page`
- [x] §Tokens · animaciones `atGrow` y `atRing` (ventana del mapa) · hecho · css:`@keyframes`
- [x] §Tokens · animaciones atIn/atWipe/atPop/atSlideL/atShimmer/atTick y `prefers-reduced-motion` · hecho · css

## 1.1 Barra lateral
- [x] §1.1 · ancho 236/68 px con `--sw`, transición 260 ms, guardado en localStorage · hecho · js:`applySidebar`
- [x] §1.1 · marca con logo 30×30 y texto oculto al contraer · hecho · html:`.brand`
- [x] §1.1 · selector de mercado con punto que late y menú de 212 px · hecho · js:`renderMarketList`, `openMarketMenu`
- [x] §1.1 · navegación agrupada Análisis / Herramientas, activo con marca izquierda, insignia de señales · hecho · html:`.nav-wrap`, js:`renderNavBadge`
- [x] §1.1 · pie con avatar RC, «Revenue · Canarias», «N mercados», tema y contraer · hecho · html:`.sidebar__foot`

## 1.2 Barra superior
- [x] §1.2 · 60 px sticky, migas, separador, ticker con máscara y pausa · hecho · js:`renderTicker`
- [x] §1.2 · indicador «Datos de hace N días» / «Actualizado · ahora» que lanza captura · hecho · js:`renderDataAge`
- [x] §1.2 · buscador ⌘K de 250 px · hecho · html:`#paletteBtn`
- [x] §1.2 · Copilot (secundario) y Capturar (primario con progreso interno) · hecho · js:`setCaptureProgress`

## 1.3 Paleta ⌘K
- [x] §1.3 · overlay, diálogo de 640 px, input de 56 px, grupos Hoteles / Ir a / Acciones, etiquetas IR·HTL·CAP·AI·UI · hecho · js:`paletteGroups`, `renderPalette`
- [x] §1.3 · teclado ⌘K, ↑↓, ↵, Esc, ⌘O y «Sin resultados» · hecho · js:`wireEvents`
  - **Nota:** «Preguntar al Copilot» se ordena al final cuando hay texto (decisión de usabilidad ya aceptada).

## 1.4 – 1.6
- [x] §1.4 · avisos emergentes oscuros abajo a la derecha, punto de color, 3,6 s · hecho · js:`toast`
- [x] §1.5 · esqueleto 320×30 + 4×104 + 520 con `atShimmer` · hecho · js:`skeleton`
- [x] §1.6 · Capturar → `POST /api/jobs/hotel-capture` + sondeo + aviso «Foto #N guardada» + recarga · hecho · js:`confirmCapture`, `trackCaptureJob`
  - **Nota (decisión del usuario):** Capturar pide confirmación y reutiliza el último perfil.

## 2 Dashboard
- [x] §2 · cabecera «Lectura de mercado», subtítulo «{mercado} · N hoteles observados · foto #N», «Extracción dd/mm/aaaa, hh:mm» y «Actualizar datos» (oculto justo después de capturar) · hecho · js:`renderDashboard`
- [x] §2 · fuera el conmutador Mapa/Gráficas/Explorar, el Contexto externo y la tabla «Cola alta» · hecho · js:`renderDashboard`
  - **Nota:** no existen en el prototipo. Los endpoints (`/api/analytics/query`, `/api/external/observations`) se conservan; solo sale su interfaz del Dashboard.
- [x] §2 · «Señales de hoy» a todo el ancho: icono, «N requieren atención · N de lectura», «Ver las N señales / Ver menos» (solo con más de 3) · hecho · js:`dashboardSignalsHTML`
- [x] §2 · rejilla de 3 señales (todas al ampliar), chip de nivel + valor, título, texto, «Ver hotel» y «Preguntar al Copilot →», entrada escalonada 60 ms · hecho · js:`dashboardSignalsHTML`
- [x] §2 · señales = `insights` del backend, ordenadas por severidad · hecho · js:`dashboardSignalModel`
  - **Nota:** se corrigieron tildes y formato de porcentaje de los textos en `database.py:_build_insights` («Líder», «está un 131,9 %»).
- [x] §2 · rejilla de 12 columnas, gap 14 px · hecho · css:`.dash-grid`
- [x] §2 · ADR mediano (3×2): 48 px, pie, minigráfica de área con el ADR de cada foto y «foto #1 · N fotos · #N» · hecho · js:`dashboardAdrCardHTML`
- [x] §2 · Hoteles con tarifa (3): «N / N», barra verde 4 px, «X % con precio observable» · hecho · js:`renderDashboard`
- [x] §2 · Dispersión del set (6×2): enjambre, banda P25–P75, mediana etiquetada, color por tramo, tooltip oscuro, pulsar abre el hotel · hecho · js:`dashboardSwarmHTML`
  - **Nota:** los cortes de color son los cuartiles reales del mercado (P25/P75), no los 210/349 € fijos del prototipo.
- [x] §2 · Movimiento ADR (3): «±X %» y «N hoteles movidos · ▲N ▼N»; «—» si no hay foto comparable · hecho · js:`renderDashboard`
- [x] §2 · Mapa hotelero (8): MapLibre 600 px, CARTO positron/dark-matter, zoom 10.7, puntos de 14 px, scroll-zoom desactivado, controles arriba a la izquierda · hecho · js:`renderDashboardHotelMap`
  - **Nota:** el centro parte de `[-15.655, 27.782]` y se encuadra el set con zoom máximo 10.7, para que el mercado General (toda la isla) también quepa.
- [x] §2 · ventana al pulsar un punto: punto ×1.45 con anillo, anillo animado, línea discontinua, ventana ≤ 680 px que crece desde el punto, a la derecha o a la izquierda, y sigue al mapa · hecho · js:`openDashboardPopover`, `positionDashboardPopover`
  - **Nota:** si la ventana no cabe a ningún lado del punto, el mapa se desplaza para que no lo tape (en el prototipo lo tapaba).
- [x] §2 · ventana · cabecera «Inspector de tarifa · puesto N de M», nombre, cadena · zona, × · hecho · js:`dashboardPopoverHTML`
- [x] §2 · ventana · gráfica «Por extracción» (+ «Media del set») / «Por fecha de entrada» (última vs anterior), puntos que crecen y lectura · hecho · js:`dashboardPopoverChartHTML`
- [x] §2 · ventana · columna de 230 px con ADR, chip vs mediana, variación y Nota · Régimen · Habitación · Cancelación · Disponibilidad · Genius · Distancia playa · hecho · js:`dashboardPopoverFacts`
  - **Nota:** Genius muestra «Participa / No participa» (la captura no trae el nivel); la distancia a la playa sale «—» cuando Booking no la publica.
- [x] §2 · ventana · pie «Ver en la hoja de mercado» y «Preguntar al Copilot»; Esc y × cierran y devuelven el foco · hecho · js:`closeDashboardPopover`
- [x] §2 · Fuera del centro (4): 11 hoteles más alejados de la mediana con barra divergente; pulsar abre el hotel · hecho · js:`dashboardOutliersHTML`
- [x] §2 · Histórico de capturas (7): ADR medio por foto y comparación de las dos últimas semanas · hecho · js:`dashboardHistoryHTML`
- [x] §2 · Curva de entrada (5): barras ≤21 / 22–42 / >42 días y la nota · hecho · js:`dashboardCurveHTML`
- [x] §2 · mapa: fondo rayado mientras carga y «mapa · MapLibre + CARTO» si falla en ~6 s · hecho · js:`loadMapLibre`, `createAtlasMap`
- [x] §2 · CSP: `https://basemaps.cartocdn.com` en `connect-src`, con test · hecho · py:`apply_security_headers`, `test_csp_allows_carto_gl_styles_and_tiles_for_the_maps`

## 3 Hoteles (cabecera y pestañas)
- [x] §3 · h1, subtítulo, conmutador de variante y Exportar CSV solo en la Hoja · hecho · js:`renderHotels`
- [x] §3 · pestañas con subrayado, guardadas en localStorage (por defecto, Panel de análisis); desde otra vista con hotel buscado se abre la Hoja · hecho · js:`setHotelTab`, `openHotelInHotels`

## 3A Hoja de mercado
- [x] §3A · tira de KPIs (7) · hecho · js:`hotelSheetKpisHTML`
- [x] §3A · vistas guardadas con recuento, chips, buscador con ×, agrupar, densidad · hecho · js:`hotelToolbarHTML`
- [x] §3A · tabla con cabecera fija y columnas # / Hotel fijas, ordenación, columnas y celdas del README · hecho · js:`hotelSheetRowHTML`
- [x] §3A · pie, estado vacío y Exportar CSV (`;` + BOM) · hecho · js:`hotelSheetCsv`
- [x] §3A · desplegable de tipos de habitación · hecho · js:`hotelRoomsPanelHTML`
- [x] §3A · variante A por defecto y B con panel lateral de 400 px · hecho · js:`hotelAsideHTML`
  - **Nota:** Genius sin nivel y distancia a la playa «—» cuando la captura no trae el dato.

## 3B Panel de análisis (BI)
- [x] §3B · backend `GET /api/hotels/rate-calendar` (dates, hotels, medians, p25, p75, coverage, facets, extractions) con tests · hecho · py:`hotel_rate_calendar`, `backend/app/rate_calendar.py`, `backend/tests/test_rate_calendar.py`
  - **Nota:** estados `ok`/`low`/`closed`/`null` como pide el prompt, más `unknown` (el hotel no aparece en una captura **parcial**: su ausencia no prueba un cierre) y `nomatch` (hay tarifa pero ninguna cumple régimen/habitación). Ambos se pintan vacíos.
  - **Nota:** hoy hay 4 fechas capturadas en Gran Canaria (Sur) y 1 en General dentro de los próximos 90 días; el resto de columnas sale vacía con la leyenda «sin captura».
- [x] §3B · barra de filtros fija (`top:60px`): hotel propio (localStorage, borde de acento), 14/30/60/90 días, régimen, tipo de habitación · hecho · js:`biFiltersHTML`
- [x] §3B · chips de filtros cruzados (Zona, segmento, Cadena, Entrada) con ×, «Limpiar» y «N de M hoteles» · hecho · js:`biFiltersHTML`
- [x] §3B · precio efectivo = tarifa mínima que cumple régimen y tipo de habitación · hecho · py:`rate_calendar._cell`
  - **Nota:** se usa el detalle de tarifas vinculado a la foto cuando existe; si no, la tarifa de la búsqueda. Las opciones de régimen y habitación salen de los datos (no se ofrece «Todo incluido Premium» si no existe). Habitación sin pista en el nombre = «Otra», no «Doble».
- [x] §3B · fecha activa (por defecto, la estancia capturada) · hecho · js:`biState`
- [x] §3B · tira de 6 KPIs con hotel propio · hecho · js:`biKpisHTML`
- [x] §3B · tira de 6 KPIs sin hotel propio · hecho · js:`biKpisHTML`
- [x] §3B · mapa de precios 560 px: color vs mediana del día, tamaño por reseñas, hotel propio con anillo y etiqueta fija, etiqueta al pasar el cursor, pulsar abre la ficha · hecho · js:`renderBiMap`, `syncBiMarkers`
- [x] §3B · panel de zonas superpuesto (250 px) que filtra y hace `fitBounds` (padding derecho 290) · hecho · js:`biZonesHTML`
- [x] §3B · marcadores con hijo `position:relative` (sin position inline en la raíz) · hecho · js:`renderBiMap`
- [x] §3B · Tarifa sugerida: cabecera, chip de confianza, valor 40 px, actual y diferencia · hecho · js:`biRecoHTML`
  - **Nota:** el chip de confianza se deriva de reglas explícitas (baja con < 6 hoteles con tarifa; media-baja con datos de > 14 días o < 15 hoteles; si no, media), visibles en su `title`.
- [x] §3B · desglose de 6 factores con barra divergente (fórmulas del README) · hecho · js:`biRecommendation`
- [x] §3B · deslizador P25–P90 (paso 5, por defecto P60), «Copiar tarifa», «Explicar con Copilot» y nota de antigüedad · hecho · js:`biRecoHTML`
- [x] §3B · Mercado en la fecha (sin hotel propio): mediana 40 px, caja, datos y tarjeta de invitación con select · hecho · js:`biDayHTML`
- [x] §3B · Calendario de tarifas: rejilla `270px repeat(H,1fr)`, cabecera por horizonte, fila de mediana, fila de rank, filas de hoteles · hecho · js:`biCalendarHTML`
- [x] §3B · calendario: cerrado rayado, cupo bajo `inset 0 -3px 0 #c98a1e`, precio con ≤ 30 días · hecho · js:`biCalendarHTML`
- [x] §3B · calendario: un único listener (`mouseover` + `data-h`/`data-d`) con lectura, columna activa superpuesta, pulsar cambia la fecha, nombre abre ficha · hecho · js:`handleBiCalendarOver`
- [x] §3B · calendario: leyenda (5 colores, cerrado, cupo bajo, **sin captura**) y pie · hecho · js:`biCalendarHTML`
- [x] §3B · Índice de precio (con y sin hotel propio) · hecho · js:`biIndexHTML`
- [x] §3B · Evolución por extracción (mediana, P25–P75, hotel propio) · hecho · js:`biEvolutionHTML`
- [x] §3B · Rango de precios por grupo (Zona / Segmento / Cadena ≥ 2), filas que aplican filtro cruzado · hecho · js:`biBoxesHTML`
- [x] §3B · Reputación vs precio con cuadrantes y value score · hecho · js:`biScatterHTML`
- [x] §3B · Alertas de competidores (Todas / Precio / Disponibilidad) · hecho · js:`biAlerts`
- [x] §3B · Disponibilidad y cierres por semana + tabla de 6 hoteles · hecho · js:`biAvailabilityHTML`
- [x] §3B · Ficha lateral de 500 px (panel lateral genérico `#sidePanel` con trampa de foco) (KPIs 3×2, tarifa por extracción, calendario de una fila, habitaciones, fijar como propio, ver en hoja) · hecho · js:`biDrawerHTML`
- [x] §3B · adaptación estrecha (flex-wrap, mínimos 200–220 px) · hecho · css:`.bi-*`
- [x] §3B · pestaña por defecto = Panel de análisis · hecho · js:`HOTEL_TAB_KEY`

## 4 Reputación
- [ ] §4 · cabecera con «Configurar captura» (icono) y «Capturar inventario» (primario) · falta · js:`renderHotelReputationCatalog`
- [ ] §4 · tira de KPIs: Inventario · Reseñas Google · Reseñas Booking · Maps verificados N/M · Última captura · falta · js:`reputationKpisHTML`
- [ ] §4 · aviso de estado vacío descartable («Entendido») · falta · js:`reputationEmptyNoticeHTML`
- [ ] §4 · segmentado Todos / Sin captura / Maps por revisar y buscador de 300 px · falta · js:`renderHotelReputationCatalog`
- [ ] §4 · tabla: casilla 52 px · Hotel + dirección · Google · Booking · Google Maps (chip) · Último Maps · Último Booking · Ficha («Abrir»); fila seleccionada en `--accent-soft`; casilla de cabecera · parcial · js:`renderHotelReputationCatalog`
- [ ] §4 · barra de selección flotante oscura («N seleccionados», Comparar, Capturar reseñas, ×) · falta · js:`reputationSelectionBarHTML`
- [ ] §4 · panel lateral «Configuración» (460 px) con fuentes, límites, interruptor, coste, estimación, Cancelar / Guardar · falta · js:`reputationConfigHTML`

## 5 Vuelos
- [ ] §5 · cabecera «Conectividad aérea hacia Gran Canaria · N rutas directas desde N mercados emisores», «Foto aérea … · N opciones» y «Nueva captura aérea» · falta · js:`renderFlights`
- [ ] §5 · desplegable de 380 px con primera salida, presupuesto y estimación (verde/rojo); «Iniciar captura» → `POST /api/jobs/air-capture` · parcial · js:`flightPlanHTML`
- [ ] §5 · pestañas Resumen · Rutas (N) · Operación aérea (N) · parcial · js:`flightTabsHTML`
- [ ] §5 · Resumen · 7 KPIs · falta · js:`flightKpisHTML`
- [ ] §5 · Resumen · red de rutas: arcos bezier a LPA por tercil, grosor por modo (Oferta / Aerolíneas / Precio), etiquetas, LPA con halo, selección, leyenda · falta · js:`renderFlightMap`
- [ ] §5 · Resumen · ruta seleccionada (select, rejilla 3×2, barras por fecha, aerolíneas, «Ver N vuelos», Copilot) · falta · js:`flightRouteCardHTML`
- [ ] §5 · Resumen · mapa de calor ruta × semana · falta · js:`flightHeatHTML`
- [ ] §5 · Resumen · curva de antelación · falta · js:`flightLeadHTML`
- [ ] §5 · Resumen · cuota por aerolínea (top 8) · falta · js:`flightShareHTML`
- [ ] §5 · Resumen · mercados emisores · falta · js:`flightMarketsHTML`
- [ ] §5 · Resumen · señales aéreas (5) · falta · js:`flightSignalsHTML`
- [ ] §5 · Rutas · gráfico de rangos con Mín · medio · máx, Directos y Δ foto · falta · js:`flightRoutesHTML`
- [ ] §5 · Operación aérea · cabecera «N de M opciones», Exportar CSV, Pantalla completa · parcial · js:`renderAirOperations`
- [ ] §5 · Operación aérea · filtros Buscar · Mercado · Ruta · Aerolínea · Conexión · Restablecer · parcial · js:`renderAirOperations`
- [ ] §5 · Operación aérea · 17 columnas en el orden y anchos del README, primera columna y cabecera fijas · parcial · js:`airOperationRow`
- [ ] §5 · Operación aérea · ordenación por cabecera (Origen, Fecha, Duración, Precio, AAI) y paginación de 50 · parcial · js:`renderAirOperations`

## 6 Copilot
- [ ] §6 · barra lateral de conversaciones (280 px, ocultable, «+», buscador, descargo al pie) · parcial · js:`renderCopilot`
- [ ] §6 · cabecera con botón de lista, título, mercado, chip de antigüedad y select de modelo · parcial · js:`renderCopilot`
- [ ] §6 · mensajes: burbuja de usuario y tarjeta del Copilot (título, confianza, texto, barras, SIGUIENTE, límite, trazabilidad desplegable) · parcial · js:`renderMsg`
- [ ] §6 · estado «respondiendo» (avatar que late, barra, «consultando foto #N…») · parcial · js:`sendChat`
- [ ] §6 · chips de sugerencias, área de 2 filas con sombra, envío 38 px, Enter / Shift+Enter · parcial · js:`copilotPanelHTML`
- [ ] §6 · abrir con pregunta escrita desde otras vistas (crea conversación nueva y envía) · parcial · js:`askCopilot`

## 7 Espacio de trabajo
- [ ] §7 · paleta de bloques (300 px) con etiquetas KPI / TAB / LIN / AIR / QA y «+» · parcial · js:`renderWorkspace`
- [ ] §7 · cabecera: título editable, estado Guardado / Cambios sin guardar, Copilot, Guardar · parcial · js:`renderWorkspace`
- [ ] §7 · barra de contexto: extracción, entrada, observaciones, chip «Enlace A · hotel» con × · parcial · js:`workspaceContextHTML`
- [ ] §7 · tablero de 2 columnas (KPIs a todo el ancho), ↑ ↓ × por bloque · parcial · js:`renderLayer`
- [ ] §7 · pulsar un hotel en la tabla lo enlaza y la gráfica ADR muestra su cambio · parcial · js:`toggleWorkspaceHotelSelection`
- [ ] §7 · estado vacío «Tablero vacío» con «Restaurar tablero base» · falta · js:`renderWorkspace`
- [ ] §7 · guardado en el endpoint actual (o `atlas.ws.v1`) · hecho · js:`saveWorkspaceDraft`

## Interactions & Behavior
- [x] §Interactions · vista activa en `atlas.view`; saltos a Hoteles desde ticker, señales, puntos y listados · hecho · js:`openHotelInHotels`
- [x] §Interactions · atajos ⌘K, ⌘O, Esc · hecho · js:`wireEvents`
- [x] §Interactions · tema: `setStyle` en los mapas activos · hecho · js:`restyleMaps`
- [x] §Interactions · densidad global desde la tabla y la paleta · hecho · js:`applyDensity`
- [x] §Interactions · estados de carga rayados en los mapas · hecho · css:`.map-frame`
- [ ] §Interactions · estados vacíos con acción de recuperación en todas las tablas y listas · parcial · js
- [x] §Interactions · error de mapa a los ~6 s con «mapa · MapLibre + CARTO» · hecho · js:`loadMapLibre`, `createAtlasMap`
- [ ] §Interactions · accesibilidad: aria-label, aria-pressed, role="tab", role="dialog", contraste, objetivos ≥ 28 px, reduced motion · parcial · js/css

## State Management
- [x] §State · global: view, market, theme, density, sidebarCollapsed, palette, toasts, captureJob, lastExtractionAt, hotelSearch, copilotPrompt · hecho · js:`State`
- [x] §State · Hoja: tab, savedView, chips, search, sort, group, expanded, selectedId · hecho · js:`State.hotel*`
- [x] §State · Panel: ownHotelId (`atlas.ownHotel.<mercado>`), horizon, board, roomFamily, zone, segment, chain, focusDate, hover, drawerHotelId, boxMode, alertTab, targetPercentile · hecho · js:`State.bi`
- [ ] §State · Vuelos: tab, focusRoute, mapMode, filtros, sort, page, fullscreen, planOpen, budget, firstDate · parcial · js:`State.flight*`
- [ ] §State · Reputación: selected, tab, q, configOpen, config · parcial · js:`State.reputation`
- [ ] §State · Copilot: conversations, active, typing, draft, traceOpen · parcial · js:`State.copilot*`
- [ ] §State · Espacio de trabajo: blocks, title, dirty, linkHotelId · parcial · js:`State.workspace*`

## Datos y backend
- [x] §Datos · hoteles, ADR, pers, Δ, estabilidad, nota, reseñas, cancelación, disponibilidad desde la API · hecho · `/api/snapshots/latest`, `/api/dashboard/metrics`
- [x] §Datos · cadena y «adults only» derivados del nombre con tests · hecho · `backend/app/hotel_traits.py`
- [x] §Datos · calendario por `check_in` y hotel (`rate-calendar`) · hecho · py:`hotels_rate_calendar`
- [x] §Datos · cierres (sin tarifa en fecha capturada) y cupo bajo (`unitsLeft ≤ 2`) · hecho · `backend/app/rate_calendar.py`
- [x] §Datos · value score y tarifa sugerida en el cliente con las fórmulas del README · hecho · js:`biValueScore`, `biRecommendation`
- [ ] §Datos · vuelos desde la API aérea actual · parcial · js:`renderFlights`
- [x] §Datos · inventario de reputación desde la API actual · hecho · `/api/hotel-reviews/catalog`

## Control de calidad
- [ ] §QA · pytest y `node --test` en verde · pendiente
- [ ] §QA · capturas 1920×1080, 1440×900 y 1366×768 en claro y oscuro en `artifacts/visual-qa/redesign-final/` · pendiente
- [ ] §QA · sin texto cortado ni desbordes horizontales por encima de 1280 px · pendiente
- [ ] §QA · consola sin errores · pendiente
