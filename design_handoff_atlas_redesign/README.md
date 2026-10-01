# Handoff: Rediseño de Atlas · Rate Intelligence

## Overview

Rediseño completo de la interfaz de **Atlas · Rate Intelligence** (repositorio `blhotel-main`). La herramienta la usa un Revenue Manager que cada mañana revisa el mercado hotelero de Canarias y decide precios.

Objetivos del rediseño:
- Más coherencia visual y menos texto.
- Jerarquía clara.
- Añadir capacidades de BI propias de un RMS / rate shopper: calendario de tarifas, índice de precio, tarifa sugerida, value score y mapas.

La línea base se mantiene: Archivo + Space Mono, el azul `#2f55d4`, fondo `#f5f6f9` y tarjetas blancas con borde fino.

Pantallas incluidas:
1. Estructura común de la app (shell)
2. Dashboard
3. Hoteles, con dos pestañas: *Hoja de mercado* (dos variantes) y *Panel de análisis*
4. Reputación
5. Vuelos, con tres pestañas: *Resumen*, *Rutas* y *Operación aérea*
6. Copilot
7. Espacio de trabajo

**Capturas no se ha rediseñado.** Se mantiene la vista actual y el prototipo solo muestra un estado vacío.

---

## About the Design Files

Los archivos de `prototype/` son **referencias de diseño hechas en HTML**. Muestran el aspecto y el comportamiento buscados, pero **no son código de producción para copiar**.

La tarea consiste en **recrear estos diseños dentro de la app existente**:
- Flask + plantillas Jinja (`backend/app/templates/index.html`).
- Estilos en un único CSS (`backend/app/static/atlas.css`).
- Lógica en un único JS sin compilación (`backend/app/static/atlas.js`).
- **Hay una CSP que prohíbe scripts inline.**

Consecuencias para la implementación:
- En el prototipo todo el estilo va **inline** por una restricción de la herramienta de diseño. En producción, cada estilo debe convertirse en **clases de `atlas.css`**, reutilizando las que ya existen (`.card`, `.kpi`, `.btn`, `.chip`, `.tag`, `table.t`, `.nav__item`, etc.) y creando las nuevas con la misma nomenclatura BEM ligera.
- **No añadir React, Vite ni ningún bundler.** Todo debe seguir funcionando como JS estático servido por Flask.
- MapLibre GL 4.7.1 ya se carga en `index.html`; los mapas nuevos lo reutilizan.
- Los datos del prototipo (`prototype/atlas-data.js`) son **en parte simulados** (ver «Datos y backend»). La implementación real debe usar la API de Flask.

Para abrir el prototipo, sirve la carpeta `prototype/` con un servidor estático (por ejemplo `python -m http.server` dentro de `prototype/`) y abre `Atlas.dc.html`. Necesita conexión para Google Fonts, MapLibre y los mapas base de CARTO.

## Fidelity

**Alta fidelidad (hi-fi).** Colores, tipografía, espaciados, radios, estados y comportamiento son finales. Recréalo al píxel con el CSS y el JS existentes.

---

## Design Tokens

Sustituir el bloque `:root` de `atlas.css` por estos tokens y añadir el bloque del tema oscuro. El tema se cambia con un atributo en `<html>`: `data-theme="oscuro"`.

### Colores — tema claro (por defecto)
| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#f5f6f9` | fondo de la app |
| `--card` | `#ffffff` | tarjetas, barra lateral, menús |
| `--ink` | `#14161c` | texto principal |
| `--muted` | `#5d6377` | texto secundario |
| `--faint` | `#737a8c` | etiquetas y metadatos (**oscurecido** respecto al anterior `#8b91a3` para cumplir contraste 4.5:1) |
| `--fainter` | `#a4a9b8` | rango/# en tablas, etiquetas de grupo del menú |
| `--border` | `#e7e9ef` | borde de tarjetas |
| `--border-soft` | `#e0e3ea` | borde de inputs y botones |
| `--line` | `#eef0f4` | separadores internos |
| `--line-soft` | `#f4f5f8` | separadores de filas |
| `--input` | `#fbfcfe` | fondo de inputs y subtarjetas |
| `--accent-soft` | `#eef2fd` | fondo activo (menú, fila seleccionada, chips activos) |
| `--ac` | `#2f55d4` | acento / primario |
| `--green` | `#1f7a52` | positivo / subida / cancelación gratis |
| `--red` | `#b94f50` | negativo / bajada / crítico |
| `--good-bg` | `#eef6f1` | fondo chip positivo |
| `--warn-bg` | `#fdf3e7` | fondo chip aviso |
| `--warn-ink` | `#8a6119` | texto chip aviso |
| `--bad-bg` | `#fbeeee` | fondo chip negativo |
| `--lo` | `#c3cbdd` | escalas neutras, bordes de hover |
| `--mid` | `#7f93c9` | serie secundaria (mediana del set, valores bajo mediana) |
| `--dark` | `#14161c` | logo, avisos emergentes, barra de selección |
| `--hover` | `#f8f9fc` | hover de fila / fila expandida |
| `--topbar` | `rgba(245,246,249,.86)` | fondo de la barra superior (con `backdrop-filter: blur(12px)`) |

### Colores — tema oscuro (`[data-theme="oscuro"]`)
`--bg #0e1014` · `--card #16181e` · `--ink #eceef3` · `--muted #a3a9b8` · `--faint #8a91a2` · `--fainter #646a7a` · `--border #252a33` · `--border-soft #2c313b` · `--line #20242c` · `--line-soft #1b1f26` · `--input #1a1d24` · `--accent-soft #1c2544` · `--ac #6583f0` · `--green #55b98c` · `--red #e2807f` · `--good-bg #15261e` · `--warn-bg #2b2314` · `--warn-ink #dcae5a` · `--bad-bg #2d1b1c` · `--lo #3c4352` · `--mid #5d6b96` · `--dark #262a33` · `--hover #1b1e25` · `--topbar rgba(14,16,20,.82)`.
En tema oscuro, los mapas cambian de estilo: `positron-gl-style` → `dark-matter-gl-style` (CARTO).

### Colores fijos para mapas y semáforos de precio
- Bajo: `#1f7a52` · Medio: `#c98a1e` · Alto: `#b94f50`.
- Posición en ruta aérea: tramos `#9bcfaf` / `#e7c66c` / `#df9898`.
- Celdas de calor, con alfa proporcional a la desviación y máximo 0.6:
  - por debajo de la mediana: `rgba(31,122,82,a)`
  - por encima: `rgba(185,79,80,a)`
  - a menos de ±5 % de la mediana: `var(--line-soft)`.

### Densidad (atributo `data-density` en `<body>`, ya existe)
`--rp`: compacta `8px` · equilibrada `13px` (por defecto) · espaciosa `18px`. Es el padding vertical de las filas de tabla.

### Tipografía
- **Archivo** 400/500/600/700: todo el texto de interfaz.
- **Space Mono** 400/700: números, precios, códigos, etiquetas en mayúsculas, atajos de teclado.

| Rol | Familia | Tamaño | Peso | Otros |
|---|---|---|---|---|
| Título de página (h1) | Archivo | 28px | 700 | letter-spacing −.025em, margin-bottom 6px |
| Subtítulo de página | Archivo | 13.5px | 400 | `--muted` |
| Título de tarjeta (h2) | Archivo | 16px | 600 | letter-spacing −.015em |
| Kicker / etiqueta | Space Mono | 9.5px | 400 | uppercase, letter-spacing .12em, `--faint` |
| Valor KPI principal | Archivo | 24px (tira) / 30px (tile) / 48px (ADR hero) | 700 | letter-spacing −.03/−.04em, line-height 1 |
| Unidad KPI | Archivo | 13–20px | 500 | `--muted` |
| Pie de KPI | Archivo | 11.5–12px | 400 | `--faint` |
| Texto de tabla | Archivo | 13px | 400/500 (nombre) | — |
| Números de tabla | Space Mono | 11–13px | 400/700 (ADR) | alineados a la derecha |
| Cabecera de tabla | Space Mono | 9.5px | 400 | uppercase, letter-spacing .1em |
| Botón | Archivo | 12.5px | 500 (secundario) / 600 (primario) | — |
| Chip | Space Mono | 9.5–10.5px | 400 | padding 2–3px 6–7px, radius 5px |

### Radios
Tarjeta grande `14px` · tarjeta/tabla `12px` · botón/input `8–9px` · segmentado `9px` (contenedor) / `7px` (opción) · chip `5px` · píldora `999px` · menú desplegable `10px` · modal/paleta `14px`.

### Sombras
- Menú desplegable: `0 12px 32px rgba(20,22,28,.14)`
- Paleta ⌘K: `0 24px 64px rgba(20,22,28,.28)`
- Aviso emergente: `0 12px 32px rgba(20,22,28,.28)`
- Panel lateral: `-20px 0 60px rgba(20,22,28,.18)`
- Ventana del mapa: `0 18px 50px rgba(20,22,28,.24)`
- Botón primario: `0 1px 2px rgba(20,22,28,.18)`
- Opción activa de un segmentado: `0 1px 2px rgba(20,22,28,.08)`

### Espaciado
- Página: `padding: 28px 32px 48px`.
- Separación entre bloques: `16px` (vertical) y `14px` (rejilla).
- Tarjeta: `16–18px 18–20px`.
- Tira de KPIs: celdas `14px 18px`, separadas con `border-left: 1px solid var(--line)`.

### Animación
- Easing global `cubic-bezier(.22,1,.36,1)`.
- Entrada de página `atIn` (opacidad 0→1, translateY 8px→0, 420ms).
- Barras `atWipe` (scaleX 0→1, 700–900ms).
- Menús `atPop` (translateY −6px + scale .98 → 1, 160–180ms).
- Paneles laterales y avisos `atSlideL` (translateX 24px → 0, 260ms).
- Esqueletos `atShimmer` (1.1s lineal).
- Ticker `atTick` (60s lineal, se pausa al pasar el cursor).
- Todo se desactiva con `prefers-reduced-motion`. La regla ya existe.

---

## Screens / Views

### 1. Estructura común de la app (`index.html`)

**Layout:** `display:flex; min-height:100vh`. Barra lateral fija a la izquierda (sticky, 100vh) + `main` flex 1.

#### 1.1 Barra lateral (contraíble)
- Ancho `236px` expandida y `68px` contraída, con transición de 260ms en `width`. Controlado por la variable `--sw` y guardado en `localStorage`.
- **Marca:** padding `22px 16px 18px 19px`. Logo `30×30`, radius 9px, fondo `--dark`, con el anillo blanco actual. «Atlas» 15px/700 y «RATE INTELLIGENCE» en kicker 9px. El texto se oculta al contraer.
- **Selector de mercado:** botón a todo el ancho con altura mínima 44px, borde `--border`, fondo `--input`, radius 10px.
  - A la izquierda, un cuadrado `22×22` en `--accent-soft` con un punto de 6px en `--ac` que late (`atPulse`).
  - Luego el kicker «MERCADO» y el nombre del mercado (12.5px/600), con un chevron a la derecha.
  - Al pulsarlo se abre un menú de 212px con los mercados («Gran Canaria (Sur) · 38 htl», «Gran Canaria (General) · 52 htl»). El activo lleva fondo `--accent-soft`.
  - **Sustituye a la lista «Mercado activo» que había al pie.**
- **Navegación agrupada:**
  - «ANÁLISIS»: Dashboard, Hoteles, Reputación, Vuelos.
  - «HERRAMIENTAS»: Copilot, Espacio de trabajo, Capturas.
  - Etiqueta de grupo: kicker 9px `--fainter`. Al contraer se muestra «·».
  - Cada ítem: 36px de alto, radius 9px, gap 11px, icono 16px (los SVG actuales de `index.html`) y texto 13.5px/500.
  - Activo: fondo `--accent-soft`, color `--ac`, peso 600 y una marca izquierda de 2×16px en `--ac`.
  - Hover: color `--ac`.
  - Dashboard muestra una insignia de aviso con el número de señales de atención (fondo `--warn-bg`, texto `--warn-ink`, Space Mono 9.5px).
  - Contraída: solo iconos, con `title` como tooltip.
- **Pie:**
  - Avatar «RC» de 30px, «Revenue · Canarias» y «2 mercados».
  - Fila de botones de 32px de alto: «Tema oscuro/claro» con icono de luna/sol y botón para contraer/expandir con icono de panel (se refleja con `scaleX(-1)` al contraer).
  - Contraída: los botones van en columna.

#### 1.2 Barra superior (60px, sticky, z-index 20)
De izquierda a derecha, con gap 16px y padding `0 32px`:
1. **Migas:** «ATLAS / HOTELES» en Space Mono 10.5px uppercase. La vista actual en `--ink`.
2. Separador vertical de 1×20px.
3. **Ticker** (se mantiene): flex 1, con máscara de degradado lateral. Cada ítem es un botón con el nombre, el ADR en negrita `--ink` y la variación ▲/▼ en verde/rojo. Al pulsar un ítem se abre ese hotel en Hoteles. Se pausa al pasar el cursor.
4. **Indicador de antigüedad de los datos** (nuevo): píldora de 30px de alto.
   - Datos antiguos: fondo `--warn-bg`, texto `--warn-ink`, «Datos de hace 38 días». Pulsarlo lanza una captura.
   - Tras capturar: fondo `--good-bg`, texto `--green`, «Actualizado · ahora».
   - La antigüedad se calcula con la fecha de la última extracción.
5. **Buscador ⌘K:** botón de 250px (`flex:0 1 250px`), 34px de alto, con icono de lupa, «Buscar hotel, vista o acción» y el atajo `⌘K`.
6. Botón **Copilot** (secundario).
7. Botón **Capturar** (primario, min-width 112px). Mientras hay una captura en curso muestra «Capturando 42%» con una barra de progreso interna (`rgba(255,255,255,.18)`).

#### 1.3 Paleta de comandos ⌘K (nueva)
- Fondo `rgba(20,22,28,.32)` con `backdrop-filter: blur(3px)`. Diálogo de 640px a 14vh del borde superior.
- Input de 56px (15px) y tecla «ESC».
- Grupos:
  - **Hoteles:** coincidencias por nombre, máximo 6, con el ADR a la derecha.
  - **Ir a:** las 7 vistas.
  - **Acciones:** Capturar mercado activo, Preguntar al Copilot (con la consulta escrita), Cambiar tema, Densidad compacta/equilibrada, Contraer/expandir barra.
- Cada ítem: 40px, con una etiqueta de 24×24 (IR / HTL / CAP / AI / UI).
- Teclado:
  - `⌘K` / `Ctrl+K` abre y cierra.
  - `↑` y `↓` navegan; el ítem activo lleva fondo `--accent-soft`.
  - `↵` ejecuta y `Esc` cierra.
  - `⌘O` abre el Copilot.
- Sin resultados: «Sin resultados para «…»».

#### 1.4 Avisos emergentes (toasts)
- Esquina inferior derecha (24px), apilados con gap 8px.
- Fondo `--dark`, texto blanco 13px, radius 11px, min-width 300px, con un punto de color (ok `#55b98c`, aviso `#dcae5a`, info `#6583f0`).
- Se cierran solos a los 3,6s.

#### 1.5 Carga inicial
Esqueleto: título de 320×30, 4 bloques de 104px y 1 bloque de 520px, todos con `atShimmer`.

#### 1.6 Captura
El botón **Capturar** y el indicador de antigüedad lanzan `POST /api/jobs/hotel-capture` con el mercado activo. Después se consulta `GET /api/jobs/<id>` y el progreso se refleja en el botón. Al terminar:
- aviso «Foto #N guardada · X hoteles con tarifa»;
- el indicador pasa a verde;
- se recargan los datos.

---

### 2. Dashboard — «Lectura de mercado»

**Cabecera:** h1 «Lectura de mercado» y subtítulo «Gran Canaria (Sur) · 38 hoteles observados · foto #18». A la derecha, «Extracción 23/08/2026, 14:41» y el botón «Actualizar datos» si los datos son antiguos.

**Señales de hoy** (tarjeta a todo el ancho, radius 14px):
- Cabecera con icono, «Señales de hoy», «3 requieren atención · 3 de lectura» y el enlace «Ver las 6 señales» / «Ver menos».
- Rejilla de 3 columnas. Por defecto muestra 3 señales y al ampliar, 6.
- Cada señal:
  - chip de nivel (Atención = aviso; Lectura = neutro) y valor en Space Mono 15px/700;
  - título 14px/600 y texto 12.5px `--muted`;
  - botones «Ver hotel» (si la señal se refiere a un hotel) y «Preguntar al Copilot →».
- Entrada escalonada (60ms por tarjeta).
- Las señales son las mismas que calcula el backend hoy: movimiento competitivo, precio agresivo, protege tu tarifa, hoteles desaparecidos, líder de precio y nuevos competidores.

**Rejilla (12 columnas, gap 14px):**
- **ADR mediano** (3 columnas × 2 filas):
  - valor de 48px con «€» y el pie «Tarifa pública · habitación/noche»;
  - minigráfica de área con el ADR de las 12 fotos (línea `--ac` de 2px, área `--accent-soft`) y los extremos «foto #1 · 12 fotos · #18».
- **Hoteles con tarifa** (3 columnas): «38 / 38» y una barra verde de 4px.
- **Dispersión del set** (6 columnas × 2 filas):
  - un punto por hotel entre 150 € y 667 €;
  - banda P25–P75 en `--accent-soft` y línea de mediana con la etiqueta «mediana 268 €»;
  - color por tramo: `<210` `--mid`, `210–349` `--lo`, `>349` `--ac`;
  - al pasar el cursor, tooltip oscuro con nombre y precio; al pulsar, abre el hotel en Hoteles.
- **Movimiento ADR** (3 columnas): «+0,4 %» y «11 hoteles movidos · ▲8 ▼3».
- **Mapa hotelero** (8 columnas):
  - MapLibre de 600px con CARTO positron, zoom 10.7 y centro `[-15.655, 27.782]`;
  - puntos de 14px con borde blanco, coloreados bajo/medio/alto;
  - scroll-zoom desactivado y controles arriba a la izquierda.
  - **Ventana al pulsar un punto** (nueva):
    - el punto crece ×1.45 con un anillo `--ac` y un anillo animado que se expande;
    - una línea discontinua une el punto con la ventana;
    - la ventana (hasta 680px) crece desde el punto (`transform-origin` = coordenadas del punto, scale .25→1, 280ms) y se coloca a la derecha del punto, o a la izquierda si no cabe;
    - sigue al punto al mover el mapa.
    - Contenido de la ventana:
      - Cabecera: «INSPECTOR DE TARIFA · PUESTO N DE 38», nombre, cadena · zona y botón ×.
      - Columna izquierda: gráfica de líneas con dos modos.
        - **Por extracción:** ADR del hotel en cada foto (#1…#18), con casilla «Media del set» (línea discontinua `--faint`).
        - **Por fecha de entrada:** última captura (`--ac`) frente a la anterior (`--warn-ink`).
        - Puntos de 3.5px que crecen a 5.5 al pasar el cursor, con una lectura encima («Foto #17 · 23/08 · 527 €»).
      - Columna derecha (230px):
        - ADR de 30px en `--ac`, chip «vs mediana» y variación frente a la foto anterior;
        - lista de datos: Nota · reseñas, Régimen, Habitación, Cancelación, Disponibilidad, Genius, Distancia a la playa.
      - Pie: «Ver en la hoja de mercado» (primario) y «Preguntar al Copilot».
- **Fuera del centro** (4 columnas): los 11 hoteles más alejados de la mediana, con nombre, ADR y barra divergente centrada. Al pulsar uno, abre el hotel.
- **Histórico de capturas** (7 columnas): línea con el ADR medio por foto (12 puntos) y a la derecha «Sem. 10 ago 279 € · Sem. 17 ago 284 € · +2,0 %».
- **Curva de entrada** (5 columnas): 3 barras horizontales (≤21 días 284 €, 22–42 días 276 €, >42 días 288 €) y la nota «Observaciones agregadas por horizonte; no es una previsión.»

---

### 3. Hoteles

**Cabecera:** h1 «Hoteles» y subtítulo «Tarifas y condiciones del set competitivo · {mercado}». A la derecha, solo en la pestaña Hoja de mercado:
- el conmutador «Variante A · Tabla / B · Tabla + detalle» (en producción, **escoger una**; ver más abajo);
- «Exportar CSV».

**Pestañas** (subrayado de 2px en `--ac`): «Hoja de mercado · 38 hoteles» y «Panel de análisis · BI · rate shopping». La pestaña activa se guarda en `localStorage`. Al llegar desde otra vista con un hotel buscado, se abre la Hoja.

#### 3A. Hoja de mercado

**Tira de KPIs** (una tarjeta, `repeat(auto-fit,minmax(150px,1fr))`):
En mercado 38 · ADR hab/noche 289 € (mediana 268 € · pers. 145 €) · Todo incluido 100 % · Rating medio 8,3 (35.320 reseñas) · Cancel. gratis 82 % (31/38) · Con escasez N (0 sold-out) · Movimiento ▲13 ▼4 (entre foto #17 y #18).

**Barra de herramientas** (padding 12px 14px):
- **Vistas guardadas** (segmentado con recuento): Mercado · Tarifa alta (≥ +30 % vs mediana) · Cancelación flexible · Escasez · Menos estables (estabilidad < 90).
- Separador.
- **Chips combinables** (píldora, activo = borde `--ac` y fondo `--accent-soft`): Adults only · Con movimiento · Nuevos.
- **Buscador** de 260px con botón × para borrar: busca por hotel, cadena o zona.
- **Agrupar** (select): Sin agrupar · Cadena · Zona · Segmento · Tramo de precio. Cada grupo lleva una fila de cabecera con fondo `--bg`, «N hoteles · mediana X €».
- **Densidad**: segmentado de 3 iconos.

**Tabla** (rejilla CSS; también vale `<table>` con `position:sticky`):
- `max-height: calc(100vh - 318px)`, con scroll propio.
- **Cabecera fija arriba** y **columnas # y Hotel fijas a la izquierda**.
- Ordenación al pulsar la cabecera (flecha ↑/↓ en `--ac`).
- Columnas (variante A):

| # | Hotel | ADR/hab | ADR/pers | vs mediana | Δ foto | Estab. | Nota | Reseñas | Cancel. | Disponib. |
|---|---|---|---|---|---|---|---|---|---|---|
| 64px | minmax(300px,2fr) | 100 | 96 | 190 | 100 | 80 | 70 | 90 | 90 | 120 |

- La **columna Régimen se elimina** (100 % Todo incluido; el dato pasa a los KPIs).
- Detalle de celdas:
  - **Hotel:** nombre 13px/500, y debajo «Cadena · Zona · Adults only» a 11px en `--faint`.
  - **vs mediana:** barra divergente de 6px centrada en el 50 % (hasta ±150 % = medio ancho; positivos en `--ac`, negativos en `--mid`) y el % en Space Mono.
  - **Δ foto:**
    - «▲ 4,2 %» en verde y «▼ 4,5 %» en rojo, con fondo de color si el cambio es ≥ 8 %;
    - «0,0 %» en `--faint`;
    - «Nuevo» en chip de acento.
  - **Estab.:** chip; ≥95 positivo, <85 aviso, el resto neutro.
  - **Cancel.:** «Gratis» en verde o «No» en `--faint`.
  - **Disponib.:** «Queda 1» en chip negativo, «Quedan N» en chip de aviso, «—» si no hay dato.
- **Pie:** «N de 38 hoteles · mediana X €» y «Booking · GraphQL · foto #18 · 23/08/2026 14:41».
- **Estado vacío:** «Ningún hotel coincide», «Prueba con otro nombre o quita algún filtro.» y el botón «Restablecer filtros».
- **Exportar CSV:** separado por `;` y con BOM UTF-8. Exporta las filas filtradas.

**Desplegable de tipos de habitación por hotel** (nuevo; flecha en la primera columna, en ambas variantes):
- Panel con fondo `--hover` y la cabecera «Tarifas por habitación · N tipos · M tarifas».
- Contexto: «Estancia 06/10 → 13/10 · 7 noches · 2 adultos», «Cancelación gratuita X de M tarifas» y el chip «Participa en Genius nivel N».
- Subtabla agrupada por tipo de habitación (fila de grupo en `--bg` con «N tarifas · máx. X personas»). Columnas:
  1. Régimen
  2. Ocupación máx. («2 personas»)
  3. Cancelación · pago («Gratuita» en verde / «No gratuita», y debajo «Gratis hasta 3 días antes · Sin pago por adelantado»)
  4. Cupo (chip «Queda 1» / «Quedan N» / «Sin aviso»)
  5. Programa / descuento («Genius nivel 2» en `--ac` y «−15 % · ahorro X €» en verde)
  6. Total estancia (con el precio original tachado si hay descuento)
  7. Por noche (la tarifa que se usa en la hoja, resaltada en `--ac`)
- Pie: «Capturado el 23/08/2026, 14:41 · Genius es una señal de participación del hotel; solo se muestra como descuento cuando la oferta lo declara.»
- Datos: equivale al `hotelRatePanelHTML()` actual de `atlas.js` (campos `roomType`, `maxOccupancy`, `board`, `freeCancellation`, `cancellationText`, `prepaymentText`, `unitsLeft`, `program`, `priceOriginal`, `priceFinal`).

**Variante A · Tabla (recomendada por defecto):** tabla a todo el ancho con las filas desplegables.

**Variante B · Tabla + detalle:**
- Tabla más estrecha (sin ADR/pers ni Reseñas) y un **panel lateral fijo de 400px** (`sticky; top:76px`) con el hotel seleccionado.
- Al pulsar una fila, se selecciona; la fila activa lleva fondo `--accent-soft`.
- Contenido del panel:
  - «POSICIÓN N DE 38», chip de % frente a la mediana, nombre 18px/600 y subtítulo;
  - ADR de 36px en `--ac`, «antes X €» y la variación;
  - **Lugar en el set:** franja con todos los hoteles como puntos de 6px (`--lo`) y el seleccionado de 10px (`--ac`), con la línea de mediana;
  - rejilla 2×4: ADR/pers, Total 7 noches, Estabilidad, Nota · reseñas, Cancelación, Disponibilidad, Genius, Distancia a la playa;
  - **Tipos de habitación:** lista con «desde X €» y un chip de estado (Queda N / Genius / Oferta / Disponible) y el enlace «Ver tarifas», que abre el desplegable de la fila;
  - botones «Preguntar al Copilot» (primario) y «Fijar para comparar».

#### 3B. Panel de análisis (BI / rate shopper) — nuevo

**Barra de filtros global** (sticky bajo la barra superior, `top:60px`, tarjeta con sombra suave):
- **Hotel propio** (select de 260px):
  - «Ninguno · vista de mercado» (por defecto) o cualquier hotel;
  - se guarda en `localStorage`; si hay uno elegido, borde y fondo de acento.
- **Fechas de entrada:** segmentado 14 / 30 / 60 / **90 días** (por defecto 90). Las entradas van del 01/10 al 29/12.
- **Régimen:** Todos · Todo incluido · Todo incluido Premium.
- **Tipo de habitación:** Todas · Doble · Suite · Familiar · Bungalow / villa · Apartamento. Se deduce del nombre de la habitación con expresiones regulares.
- A la derecha:
  - chips de **filtros cruzados activos**: «Zona: X», «Adults only», «Cadena: X», «Entrada dd/mm», cada uno con ×;
  - «Limpiar»;
  - «N de 38 hoteles».
- El precio efectivo de cada hotel es la **tarifa mínima que cumple régimen y tipo de habitación**. Si ninguna tarifa los cumple, el hotel sale del análisis.

**Fecha activa:** todo el panel se calcula para una fecha de entrada activa. Por defecto es el 06/10, la estancia capturada. Se cambia pulsando cualquier columna del calendario.

**Tira de KPIs** (6):
- **Con hotel propio:** Tu tarifa · dd/mm (puesto N de M) · Índice de precio (mediana = 100) · Mediana del set · Value score /100 · Competidores cerrados (+ cupo bajo) · Movimiento del set ▲▼.
- **Sin hotel propio:** Mediana (P25 · P75) · Dispersión (P75/P25) · Hoteles en el alcance · Cerrados ese día · Mediana del horizonte (rango) · Movimiento del set.

**Fila principal** (flex con salto de línea):
- **Mapa de precios** (`flex:2 1 560px`, alto 560px), la pieza protagonista:
  - puntos coloreados por su relación con la mediana del día: ≤ −15 % `#1f7a52`, en la mediana `#c98a1e`, ≥ +15 % `#b94f50`; si está cerrado, gris `#8b91a3` al 55 %;
  - tamaño según reseñas: `min(24, 10 + √reseñas / 5)` px;
  - el hotel propio lleva un anillo `#2f55d4` de 3px, escala 1.25 y la etiqueta fija «Tu hotel · X €»;
  - al pasar el cursor aparece una etiqueta oscura con el nombre y el precio; al pulsar, se abre la ficha;
  - **panel de zonas** superpuesto arriba a la derecha (250px): zona, nº de hoteles y mediana. Al pulsar una zona se filtra todo el panel y el mapa se ajusta a los hoteles visibles (`fitBounds`, padding derecho de 290px).
  - **Importante:** los marcadores de MapLibre no pueden llevar `position` inline en su elemento raíz. Hay que envolver el contenido en un hijo con `position:relative`; si no, los puntos se amontonan.
- **Columna derecha** (`flex:1 1 340px`):
  - **Con hotel propio → Tarifa sugerida:**
    - «TARIFA SUGERIDA · ENTRADA jue 08/10», chip «Confianza media-baja» y nombre del hotel;
    - valor sugerido de 40px en `--ac`, «Actual X €» y chip de diferencia (verde/rojo).
    - **Desglose** en 6 filas, cada una con barra divergente y valor en €:
      1. Mediana del set: base (N hoteles con tarifa ese día).
      2. Posición objetivo P{n}: precio del percentil objetivo del set − mediana.
      3. Value score: `(VS − 50) / 50 × 5 % × mediana`.
      4. Escasez de la competencia: `min(8 %, (cerrados + 0,5 × cupo bajo) / hoteles × 0,35) × mediana`.
      5. Movimiento reciente del set: media de la variación entre fotos × mediana.
      6. Antelación: menos de 21 días +3 %; más de 60 días −2 %; en medio, 0.
      - Sugerida = suma de todas.
    - **Deslizador «Posición objetivo en el set»:** P25–P90 en pasos de 5 (por defecto P60).
    - Botones «Copiar tarifa» (primario) y «Explicar con Copilot», que envía el desglose como pregunta.
    - Nota: «Basada en precios públicos de hace N días. No incluye ocupación, pickup ni restricciones propias.»
  - **Sin hotel propio → Mercado en la fecha:**
    - mediana de 40px y diagrama de caja horizontal (mín · P25–P75 · mediana · máx);
    - lista de datos: Más barato, Más caro, Mejor value score y Cerrados;
    - tarjeta de invitación en `--accent-soft` que explica la tarifa sugerida, con un select para elegir el hotel propio.

**Calendario de tarifas** (a todo el ancho):
- Rejilla `270px repeat(H, 1fr)` con gap de 1px.
- **Cabecera:** con 30 días o menos, número de día; con 60 o 90, abreviatura del mes (OCT/NOV/DIC) el día 1 y el número de los lunes (se omite si cae a 2 días o menos del cambio de mes). La fecha activa va en `--ac` y negrita.
- **Fila «Mediana del set»:** barras de alto relativo (30–100 %) en `--mid` al 70 %.
- **Fila «Rank del hotel propio»** (solo con hotel propio):
  - tercio superior: fondo `--ac` con texto blanco;
  - tercio medio: `--accent-soft`;
  - tercio inferior: `--line-soft`;
  - cerrado: `--bad-bg`.
  - El número de puesto solo se escribe con 30 días o menos.
- **Filas de hoteles:** scroll vertical de hasta 560px. El hotel propio va fijado arriba con fondo `--accent-soft`; el resto se ordena por precio en la fecha activa.
  - Celda de 24px de alto y radius 2px, coloreada según la desviación frente a la mediana del día (ver tokens de calor).
  - **Cerrado:** rayado `repeating-linear-gradient(135deg, rgba(20,22,28,.45) 0 1.5px, transparent 1.5px 4px)`.
  - **Cupo bajo:** `box-shadow: inset 0 -3px 0 #c98a1e`.
  - Con 30 días o menos, cada celda muestra el precio en Space Mono 9.5px (blanco si la desviación supera el 45 %).
- **Lectura** en la cabecera al pasar el cursor: «Seaside Palm Beach · jue 08/10 · 689 € · +154 % vs mediana (271 €) · cupo bajo». Implementar con **un único listener** en el contenedor (`mouseover` + `data-h`/`data-d`), no uno por celda.
- **Columna activa:** superpuesta con borde de 1.5px `--ac` y sombra `0 0 0 3px rgba(47,85,212,.12)`. Pulsar cualquier celda o barra cambia la fecha activa.
- Pulsar el nombre de un hotel abre su ficha.
- Leyenda: escala de 5 colores «vs mediana del día», «cerrado» y «cupo bajo».
- Pie: «Pulsa una fecha para recalcular…» y «entrada dd/mm seleccionada · N con tarifa · N cerrados».

**Rejilla inferior** (flex con salto de línea):
- **Índice de precio** (`flex:1 1 520px`), SVG de 800×210:
  - Con hotel propio: índice del hotel (precio / mediana × 100), banda P25–P75 del set como índice y línea de referencia discontinua en 100. Resumen: «media N · N días cerrado».
  - Sin hotel propio: mediana en € con la banda P25–P75.
  - En ambos casos, línea vertical en la fecha activa y etiquetas el día 1 de cada mes.
- **Evolución por extracción** (`flex:1 1 520px`): mediana del set por foto (`--mid`), banda P25–P75 y línea del hotel propio (`--ac`, 2.4px). Resumen «mediana X → Y · ±Z %».
- **Rango de precios por grupo** (`flex:1 1 460px`):
  - segmentado Zona / Segmento / Cadena (en Cadena, solo grupos de 2 o más hoteles);
  - cada fila es un botón con nombre + N, bigotes, caja P25–P75 (`--accent-soft` con borde `--mid`), mediana (2px `--ac`) y un punto negro con el hotel propio si está en ese grupo;
  - pulsar una fila aplica el filtro cruzado correspondiente.
- **Reputación vs precio · value score** (`flex:1.4 1 560px`), dispersión de 300px de alto:
  - eje X: precio en la fecha activa; eje Y: nota de Booking;
  - cuadrantes delimitados por la mediana de precio y la mediana de nota, con etiquetas «Valor alto» (arriba-izquierda, verde, fondo `rgba(31,122,82,.05)`), «Premium justificado», «Económico» y «Caro para su nota» (rojo);
  - burbujas con tamaño según reseñas: verde si VS ≥ 60, rojo si VS ≤ 40, el resto `--mid`; el hotel propio en `--ac` con borde de 3px `--ink`;
  - al pasar el cursor, lectura «Nombre · precio · nota · value N»; al pulsar, ficha.
  - **Value score:** `clamp(0, 100, round(50 + (nota − medianaNota) × 22 − (precio / mediana − 1) × 60))`.
- **Alertas de competidores** (`flex:1 1 520px`):
  - segmentado Todas / Precio / Disponibilidad, con recuentos;
  - cada fila: chip de tipo (Nuevo / Bajada ≤ −3 % / Subida ≥ +5 % / Queda 1 / Cierres, este último si hay 2 o más fechas cerradas en 14 días), nombre, texto («527 € → 504 €») y valor;
  - ordenadas por relevancia; al pulsar, ficha.
- **Disponibilidad y cierres** (`flex:1 1 520px`):
  - barras apiladas por semana: cerrado en `--red` abajo, cupo bajo en `#c98a1e` arriba y % encima;
  - tabla con los 6 hoteles con más días cerrados o de cupo bajo, y su estado en la fecha activa.

**Ficha de hotel** (panel lateral de 500px con fondo oscurecido; se abre desde el mapa, el calendario, la dispersión, las alertas o la tabla de cierres):
- Cabecera: «FICHA · PUESTO N DE M», nombre 19px/600 y «Cadena · Zona · Adults only · playa a X».
- Rejilla 3×2: Tarifa del día, Índice, Value score, Nota · reseñas, Δ foto, Genius.
- Tarifa por extracción: línea del hotel y mediana del set en discontinua.
- Calendario de una fila con el horizonte elegido.
- Habitaciones y tarifas: nombre, ocupación, nº de tarifas, chip de estado y «desde X €».
- Botones «Fijar como hotel propio» (primario) y «Ver en hoja de mercado» (cambia de pestaña y busca el hotel).

**Adaptación a pantallas estrechas:** todas las cabeceras de tarjeta llevan `flex-wrap:wrap` y el bloque del título `min-width:200–220px`. Los bloques de la rejilla usan `flex` con base mínima y pasan a la línea siguiente por debajo de unos 1300px.

---

### 4. Reputación — «Inventario y reputación»
- **Cabecera:** botones «Configurar captura» (secundario, con icono de ajustes) y «Capturar inventario» (primario).
- **Tira de KPIs:** Inventario 49 · Reseñas Google 0 · Reseñas Booking 0 · Maps verificados N/49 · Última captura —.
- **Aviso de estado vacío** (borde discontinuo `--lo`, se puede descartar con «Entendido»): «Todavía no hay reseñas capturadas», con la explicación de la configuración actual.
- **Tabla:**
  - segmentado Todos / Sin captura / Maps por revisar y buscador de 300px;
  - columnas: casilla (52px) · Hotel + dirección · Google · Booking · Google Maps (chip) · Último Maps · Último Booking · Ficha («Abrir»);
  - la fila seleccionada lleva fondo `--accent-soft`; la casilla de la cabecera selecciona todas las visibles.
- **Barra de selección flotante** (fija abajo y centrada en el área de contenido, fondo `--dark`): «**N** seleccionados», «Comparar», «Capturar reseñas» (primario) y ×.
- **Panel lateral «Configuración»** (460px): **todos los controles de captura que antes estaban a la vista pasan aquí.**
  - Fuentes: Google Maps / Google Hotels / Booking, como botones con casilla.
  - Límites por hotel: Máx. reseñas (1000) y Decisiones máx. (24). Interruptor «Hasta agotar recorrido» (desactiva Máx. reseñas), con la nota del límite técnico (400 desplazamientos en Maps y 500 páginas en Booking).
  - Coste de navegación asistida: Tope Jev (USD) y USD por decisión, con la nota de que solo aplica a Maps.
  - Estimación: «Estimación para N hoteles · X USD».
  - Pie: «Cancelar» y «Guardar configuración».

---

### 5. Vuelos
**Cabecera:** «Conectividad aérea hacia Gran Canaria · 13 rutas directas desde 8 mercados emisores», «Foto aérea 23/08/2026, 14:41 · N opciones» y el botón «Nueva captura aérea».
- El botón abre un **desplegable** de 380px con: Primera salida (fecha), Presupuesto de consultas y la estimación «25 fechas × 13 rutas = 325 consultas» (verde si cabe en el presupuesto, rojo si no).
- «Iniciar captura» se desactiva si no cabe y lanza `POST /api/jobs/air-capture`.

**Pestañas:** Resumen · Rutas (13) · Operación aérea (N).

**Resumen (BI):**
- **KPIs (7):** Rutas activas · Opciones · Precio de acceso · Precio medio · Variación · Directos % · Aerolíneas (con duración media).
- **Red de rutas** (8 columnas, mapa de 560px, centro `[-1.5, 43]`, zoom 3.05):
  - arcos (bezier cuadrática, 25 puntos) desde cada aeropuerto hasta LPA `[-15.387, 27.932]`, coloreados según el tercil del precio medio (bajo/medio/alto);
  - grosor según el modo (segmentado Oferta / Aerolíneas / Precio). La ruta seleccionada va más gruesa y opaca;
  - etiquetas «AMS · 189 €» en cada origen (blancas; la seleccionada en `--ac`) y marcador de destino «LPA» con halo;
  - pulsar un arco o una etiqueta selecciona la ruta;
  - leyenda «Grosor de línea».
- **Ruta seleccionada** (4 columnas):
  - select de ruta, «AMS → LPA», aeropuerto y país;
  - rejilla 3×2: Mínimo, Medio, Máximo, Opciones, Directos, Duración;
  - barras con el mínimo por fecha de salida (25 fechas; la más barata en verde);
  - lista de aerolíneas con iniciales IATA, avión, nº de opciones y mínimo;
  - botones «Ver N vuelos» (pasa a Operación aérea filtrada por la ruta) y «Preguntar al Copilot».
- **Mapa de calor** (8 columnas): ruta × 13 semanas de salida con el precio mínimo; color según la desviación frente a la media de la ruta. Pulsar una fila selecciona la ruta.
- **Curva de antelación** (4 columnas): índice de precio frente a la media por tramo (≤14 / 15–30 / 31–60 / 61–90 días), con barras divergentes.
- **Cuota de oferta · Aerolíneas** (4 columnas): top 8, con barra, % y mínimo.
- **Mercados emisores** (4 columnas): mercado, rutas, opciones y precio desde.
- **Señales aéreas** (4 columnas, 5 señales que se pueden pulsar): ruta más cara, acceso más barato, mayor amplitud, menos directos y mayor cambio.

**Rutas:** gráfico de rangos por ruta (mínimo con aro `--ac`, medio con punto `--ink`, máximo con cuadrado `--lo`), con las columnas «Mín · medio · máx», «Directos» y «Δ foto». Pulsar una ruta vuelve a Resumen con esa ruta seleccionada.

**Operación aérea** (tabla profesional):
- Cabecera «Operación aérea · N de M opciones», «Exportar CSV» y «Pantalla completa» (tarjeta fija con 12px de margen y fondo oscurecido).
- Filtros: Buscar (aerolínea, vuelo, avión, aeropuerto) · Mercado · Ruta · Aerolínea · Conexión (Todas / Solo directos / Con escala) · Restablecer.
- **17 columnas**, con la primera fija a la izquierda y la cabecera fija arriba:
  1. Mercado + ciudad
  2. Origen (IATA + aeropuerto)
  3. Destino (LPA · Gran Canaria)
  4. Fecha + días de antelación
  5. Aerolínea (logo con iniciales)
  6. Vuelo(s)
  7. **Avión**
  8. Clase
  9. Salida
  10. Llegada
  11. **Conexión** (chip «Directo» o «1 escala · MAD»)
  12. Duración
  13. Precio
  14. Posición en la ruta (barra de 3 tramos con marcador y la etiqueta «barato para la ruta / en la media / caro para la ruta»)
  15. AAI (precio / media de la ruta: verde < 0,9, rojo > 1,1)
  16. Vuelta
  17. Captura
- Anchos: `150 170 110 100 170 150 150 80 72 72 130 88 84 150 64 84 130` (px).
- Se puede ordenar por Origen, Fecha, Duración, Precio y AAI. Paginación de 50 en 50.
- Todos estos campos ya los usa `airOperationRow()` en `atlas.js`: `market_segment`, `origin`, `departure_airport_name`, `outbound_date`, `days_ahead`, `airline`, `flight_numbers`, `aircraft_models`, `travel_classes`, `departure_time`, `arrival_time`, `is_direct`, `num_layovers`, `layover_airports`, `price`, `air_accessibility_index`, `total_duration_min`, `return_date`, `capture_run_at`.

---

### 6. Copilot (se mantiene como página propia)
- **Barra lateral de conversaciones** (280px, se puede ocultar): «Conversaciones · N sesiones», botón «+» (primario de 32px), buscador y lista (activa en `--accent-soft`). Al pie, el descargo «Respuestas basadas en capturas de Booking y vuelos. No sustituye pickup ni ocupación del PMS.»
- **Cabecera:** botón de lista, «Copilot», «Gran Canaria (Sur) · asistente de revenue», chip «Datos de hace 38 días» (aviso) y select de modelo (Modelo automático / Rápido / Razonamiento).
- **Mensajes** (máx. 880px, centrados):
  - Usuario: burbuja `--ac` con texto blanco, radius `14px 14px 4px 14px`, alineada a la derecha.
  - Copilot: avatar oscuro de 28px y tarjeta blanca con radius `4px 14px 14px 14px`, que contiene:
    - título 14px/600 y chip «Confianza media / media-baja / alta»;
    - texto principal con **negritas** en las cifras;
    - bloque opcional de barras (nombre · barra · valor);
    - bloque «SIGUIENTE» en `--accent-soft` con la acción recomendada;
    - límite de confianza en `--faint`;
    - pie «TRAZABILIDAD · Booking · foto #18», con «Formato comprobado +/−» que despliega la evidencia (métricas, comparabilidad, foto).
  - Mientras responde: avatar que late, barra de carga animada y «consultando foto #18…».
- **Entrada:**
  - chips de sugerencias: «¿Quién ha bajado precio?», «Hoteles con escasez», «Compara cadenas», «¿Cómo está Seaside Palm Beach?»;
  - área de texto de 2 filas en una tarjeta con sombra `0 4px 18px rgba(20,22,28,.05)` y botón de envío de 38px;
  - `Enter` envía y `Shift+Enter` hace salto de línea.
- Otras vistas pueden abrir el Copilot con una pregunta ya escrita, mediante los botones «Preguntar al Copilot». Eso crea una conversación nueva y la envía.
- Backend: reutilizar el endpoint del asistente actual. La estructura Lectura / Evidencia / Acción siguiente / Límite de confianza ya existe en las respuestas.

---

### 7. Espacio de trabajo — «Pizarra personal»
- **Paleta de bloques** a la izquierda (300px): KPIs certificados · Tabla hotelera · Gráfica ADR · Gráfica aérea · Calidad de datos. Cada bloque tiene una etiqueta de 30×24 (KPI / TAB / LIN / AIR / QA) y un «+».
- **Cabecera:** título editable en línea (input sin borde, 28px/700), estado «Guardado» (verde) o «Cambios sin guardar» (aviso), «Preguntar al Copilot» y «Guardar».
- **Barra de contexto:** extracción (select), entrada (select), «222 observaciones comparables» y chip «Enlace A · hotel» con × cuando hay un hotel enlazado.
- **Tablero** en rejilla de 2 columnas (KPIs a todo el ancho). Cada bloque tiene los botones ↑ ↓ × para reordenar y quitar.
  - Pulsar un hotel en «Tabla hotelera» lo enlaza (Enlace A) y la «Gráfica ADR» muestra su cambio entre fotos.
- **Estado vacío:** «Tablero vacío», con el botón «Restaurar tablero base».
- Se guarda en `localStorage` (clave `atlas.ws.v1`) o, si existe, en el endpoint actual del espacio de trabajo.

---

## Interactions & Behavior (resumen)
- **Navegación:** la vista activa se guarda en `localStorage` (`atlas.view`). Desde el ticker, las señales, los puntos y los listados se salta a Hoteles con el hotel buscado.
- **Atajos de teclado:** `⌘/Ctrl+K` paleta, `⌘/Ctrl+O` Copilot, `Esc` cierra menús y paneles.
- **Tema:** alternar `data-theme` en `<html>`, guardar en `localStorage` y hacer `setStyle` en los mapas activos.
- **Densidad:** cambia `--rp`. Es global y se puede cambiar desde la tabla de Hoteles y desde la paleta.
- **Carga:** esqueleto inicial y estados de «cargando» en los mapas (fondo rayado mientras llegan las teselas).
- **Estados vacíos** en todas las tablas y listas, con acción de recuperación.
- **Errores de mapa:** si MapLibre no carga en unos 6s, mostrar el fondo rayado con el texto «mapa · MapLibre + CARTO».
- **Accesibilidad:**
  - `aria-label` en los botones de icono, `aria-pressed` en los chips y `role="tab"` en las pestañas;
  - diálogos con `role="dialog"`, contraste mínimo 4.5:1 y objetivos táctiles de al menos 28–32px en escritorio;
  - todas las animaciones respetan `prefers-reduced-motion`.

## State Management
Estado global (el objeto `State` actual de `atlas.js`, ampliado):
- `view`, `market`, `theme`, `density`, `sidebarCollapsed`.
- `palette { open, query, index }`, `toasts[]`.
- `captureJob { id, pct }` (consultando `/api/jobs/<id>`) y `lastExtractionAt` (para el indicador de antigüedad).
- `hotelSearch` (salto a Hoteles) y `copilotPrompt` (salto al Copilot).

Hoteles · Hoja: `tab`, `savedView`, `chips[]`, `search`, `sort {key, dir}`, `group`, `expanded {hotelId: bool}`, `selectedId` (variante B).

Hoteles · Panel: `ownHotelId` (en `localStorage`), `horizon`, `board`, `roomFamily`, `zone`, `segment`, `chain`, `focusDate`, `hover {hotelId, day}`, `drawerHotelId`, `boxMode`, `alertTab`, `targetPercentile`.

Vuelos: `tab`, `focusRoute`, `mapMode`, filtros (`q`, `segment`, `route`, `airline`, `connection`), `sort`, `page`, `fullscreen`, `planOpen`, `budget`, `firstDate`.

Reputación: `selected {}`, `tab`, `q`, `configOpen`, `config {sources, maxReviews, decisions, exhaust, capUsd, costPerDecision}`.

Copilot: `conversations[]`, `active`, `typing`, `draft`, `traceOpen {}`.

Espacio de trabajo: `blocks[] {id, type}`, `title`, `dirty`, `linkHotelId`.

## Datos y backend
El prototipo usa `prototype/atlas-data.js`. Qué datos son reales y cuáles hay que obtener:

| Dato | Estado en el prototipo | En producción |
|---|---|---|
| 24 hoteles (nombre, ADR, pers, Δ, estabilidad, nota, reseñas, cancelación, disponibilidad) | reales, de las auditorías del repo | API actual de hoteles / snapshots |
| Otros 14 hoteles hasta llegar a 38 | simulados | API |
| Coordenadas | aproximadas por zona | `market_snapshots` (lat/lng ya existen para el mapa actual) |
| Señales del Dashboard | reales | cálculo actual del backend |
| ADR por foto (12 capturas) | reales | histórico de capturas |
| Histórico de ADR por hotel y por fecha de entrada | simulados | endpoint actual del «Inspector de tarifa» (`dashboardHotelTrendHTML`) |
| Tipos de habitación y tarifas por hotel | simulados | detalle de tarifas actual (`hotelRateDetails`) |
| Genius / distancia a la playa | simulados | campo `genius` y `beachDistance` que ya existen |
| **Calendario de 90 días (precio por fecha de entrada y hotel)** | **simulado** | **nuevo:** agregar snapshots por `check_in` y hotel. Se necesita una captura multi-fecha (la captura semanal ya avanza 7 días por iteración; ampliarla a diario para el horizonte) |
| **Cierres y cupo bajo por fecha** | **simulado** | **nuevo:** sold-out = hotel sin tarifa en una fecha capturada; cupo bajo = `unitsLeft ≤ 2` |
| Tarifa sugerida y value score | calculados en el cliente | se pueden calcular en el cliente con las fórmulas de arriba o en un endpoint `/api/hotels/recommendation` |
| Vuelos (614 opciones, 13 rutas, aviones, escalas) | simulados con campos reales | API aérea actual (SerpApi) |
| Inventario de reputación | real (nombres y direcciones) | API actual |

Endpoints sugeridos, si se prefiere calcular en el servidor:
- `GET /api/hotels/rate-calendar?market=&from=&days=&board=&roomFamily=` → `{ dates[], hotels[{id, prices[], status[]}], medians[], p25[], p75[] }`.
- `GET /api/hotels/recommendation?hotel=&date=&target=` → `{ suggested, current, parts[{key, value, why}] }`.

## Plan de implementación por fases
1. **Tokens y estructura común:** tokens claro/oscuro, barra lateral contraíble con navegación agrupada y selector de mercado, barra superior con indicador de antigüedad, paleta ⌘K, avisos emergentes y esqueleto de carga. *Hecho cuando* el tema, la densidad y el contraer funcionan en todas las vistas actuales sin romper nada.
2. **Hoteles · Hoja de mercado:** tira de KPIs, barra de herramientas, tabla con cabecera y columnas fijas, agrupación, desplegable de habitaciones y variante elegida. *Hecho cuando* se pueda filtrar, ordenar, agrupar, desplegar y exportar con datos reales.
3. **Dashboard:** señales arriba, rejilla y ventana del mapa con gráfica de evolución.
4. **Hoteles · Panel de análisis:** primero con los datos disponibles (una fecha de entrada); después el calendario completo cuando exista el endpoint.
5. **Vuelos:** Resumen, Rutas y Operación aérea.
6. **Reputación, Copilot y Espacio de trabajo.**
7. **Control de calidad:** 1920×1080, 1440×900 y 1366×768, tema oscuro, `prefers-reduced-motion`, navegación por teclado y tests de pytest existentes en verde.

## Assets
- **Iconos de navegación:** los SVG actuales de `backend/app/templates/index.html` (se reutilizan tal cual).
- **Iconos nuevos** (SVG de trazo 1.6–1.8, 14–16px): lupa, luna/sol, panel para contraer, descarga, ajustes, flecha de envío y chevron. Sus trazados están en los archivos del prototipo.
- **Mapas:** MapLibre GL 4.7.1 + CARTO `positron-gl-style` / `dark-matter-gl-style`.
- **Fuentes:** Google Fonts, Archivo (400–700) y Space Mono (400, 700). Ya se cargan.
- No hay imágenes rasterizadas.

## Files
En `prototype/`:
- `Atlas.dc.html`: estructura común (barra lateral, barra superior, paleta ⌘K, avisos, tema, densidad, captura). **Ábrelo como punto de entrada.**
- `Atlas-Dashboard.dc.html`: Dashboard, con la ventana del mapa.
- `Atlas-Hoteles.dc.html`: Hoteles, con las pestañas, la hoja de mercado (variantes A/B) y el desplegable de habitaciones.
- `Atlas-HotelesBI.dc.html`: panel de análisis BI / rate shopper.
- `Atlas-Reputacion.dc.html`: Reputación.
- `Atlas-Vuelos.dc.html`: Vuelos (Resumen, Rutas, Operación aérea).
- `Atlas-Copilot.dc.html`: Copilot.
- `Atlas-Workspace.dc.html`: Espacio de trabajo.
- `atlas-data.js`: datos de ejemplo y generadores (útil para ver la forma de cada estructura).
- `support.js`: entorno de ejecución de los prototipos (solo para visualizarlos; **no** se usa en producción).

En la raíz del paquete:
- `PROMPT.md`: el prompt para ejecutar la implementación con Claude Code.

La lógica de cada vista está en el bloque `<script data-dc-script>` al final de cada archivo, dentro de `renderVals()`: cálculos, fórmulas y formatos. La estructura visual es la plantilla HTML de arriba, con todos los valores de estilo exactos.
