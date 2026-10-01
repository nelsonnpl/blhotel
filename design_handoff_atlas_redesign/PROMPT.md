# Prompt para Claude Code

Copia la carpeta `design_handoff_atlas_redesign/` en la raíz del repositorio `blhotel-main`. Abre Claude Code en esa raíz y pega el texto de abajo. Está pensado para ejecutarse por fases: al terminar cada una, revisa el resultado y responde «continúa» para pasar a la siguiente.

---

```
Vas a implementar el rediseño de la interfaz de Atlas · Rate Intelligence de este repositorio.

Contexto obligatorio antes de tocar código:
1. Lee entero design_handoff_atlas_redesign/README.md. Es la especificación completa: tokens, pantallas, medidas, interacciones, estado, datos y plan por fases.
2. Lee README.md y AGENTS.md del repo, backend/app/templates/index.html, backend/app/static/atlas.css y backend/app/static/atlas.js (este último por secciones; tiene unas 4.500 líneas). Identifica cómo se renderiza hoy cada vista, qué endpoints consume y el objeto State.
3. Consulta los prototipos de design_handoff_atlas_redesign/prototype/ como referencia visual y de comportamiento. Para verlos, sirve esa carpeta con `python -m http.server 8001` y abre http://127.0.0.1:8001/Atlas.dc.html. Las fórmulas (value score, tarifa sugerida, cuartiles, colores de calor) están en renderVals() de cada archivo .dc.html.

Reglas:
- El stack no cambia: Flask + Jinja + atlas.css + atlas.js estáticos. No añadas React, Vite, npm ni bundlers.
- Hay una CSP que prohíbe scripts inline. Todo el JS va en atlas.js y todos los estilos en atlas.css.
- Los estilos inline de los prototipos son solo referencia. Conviértelos en clases de atlas.css reutilizando las existentes (.card, .kpi, .btn, .chip, .tag, table.t, .nav__item…) y creando las nuevas con la misma nomenclatura.
- Usa los tokens del README: sustituye :root y añade [data-theme="oscuro"]. No inventes colores.
- Usa siempre datos reales de la API. Donde el README marca un dato como «simulado/nuevo» (calendario de 90 días, cierres por fecha, tarifa sugerida), primero comprueba si el backend ya puede proporcionarlo. Si no, crea el endpoint propuesto en el README (con tests de pytest) o, si no es viable, muestra un estado vacío honesto en esa pieza. Nunca inventes datos en producción.
- Mantén la accesibilidad actual (skip-link, aria, prefers-reduced-motion) y no rompas los tests existentes: `python -m pytest backend/tests -q` debe seguir en verde.
- En Hoteles · Hoja de mercado implementa la variante A por defecto. La B (tabla + panel lateral) va detrás de un conmutador en la cabecera, como en el prototipo.
- Los marcadores de MapLibre no pueden llevar position inline en su elemento raíz; envuelve el contenido en un hijo con position:relative.

Forma de trabajo:
- Sigue el «Plan de implementación por fases» del README, en orden, una fase por turno.
- Al empezar cada fase, resume en 5–10 líneas qué archivos y funciones vas a tocar.
- Al terminar cada fase:
  (a) ejecuta los tests;
  (b) arranca la app con `python run.py` y revisa las vistas afectadas a 1440×900 y 1920×1080, en tema claro y oscuro (si tienes Playwright, guarda capturas en artifacts/visual-qa/redesign-<fase>/);
  (c) enumera las diferencias que queden respecto al prototipo y por qué;
  (d) para y espera mi «continúa».
- Si algo del README es ambiguo o choca con el código actual, pregúntame antes de decidir.

Empieza por la Fase 1 (tokens y estructura común).
```

---

## Prompts cortos útiles durante la implementación

- **Revisar una pantalla contra el prototipo:**
  «Compara la vista Hoteles actual con prototype/Atlas-Hoteles.dc.html y la sección 3A del README. Lista las diferencias de espaciado, tipografía, color y comportamiento, y corrígelas.»
- **Solo una pieza:**
  «Implementa únicamente el Calendario de tarifas del Panel de análisis (README §3B), con el endpoint /api/hotels/rate-calendar y sus tests.»
- **Tema oscuro:**
  «Recorre todas las vistas en data-theme="oscuro" y corrige cualquier color fijo que no use los tokens.»
