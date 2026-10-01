# Auditoría fase F · validación visual y accesibilidad

Fecha de corte: 6 de septiembre de 2026.

## Hallazgo corregido

En anchos inferiores a 1180 px el CSS ocultaba `.copilot__scope`, y por tanto los modos Rápido, Análisis y Decisión desaparecían aunque el backend y el estado del frontend los soportaban. El encabezado responsive ahora apila el alcance y mantiene el grupo de modos visible.

## Verificación en ejecución

- Aplicación ejecutada con una copia temporal de SQLite.
- Copilot abierto y estado real inspeccionado con el árbol de accesibilidad.
- Cambio de Rápido a Análisis y a Decisión verificado por clic y por teclado (`Tab` + `Espacio`); `aria-pressed` se actualiza correctamente.
- Captura visual actual del Copilot y de Capturas revisada en el navegador integrado.
- Sin errores ni avisos de consola.
- `document.documentElement.scrollWidth` coincide con `innerWidth`; no se detecta desbordamiento horizontal.
- 109 controles focusables en la vista Copilot; todos los botones tienen nombre accesible y no hay inputs/selects sin etiqueta programática.
- Existe skip link, foco visible global, región `aria-live` para el hilo y diálogo de bloqueo con nombre y descripción.

## Observaciones restantes

El navegador integrado usado para esta revisión expone un viewport CSS aproximado de 1087 px y una captura física más estrecha. Las pantallas históricas de fases A y B cubren 1920, 1440, 1366 y 993 px. Conviene repetir la misma matriz con un navegador de escritorio y revisar específicamente el modo Decisión en 993 px antes de declarar una certificación visual completa.

La animación respeta `prefers-reduced-motion`. El mapa usa botones de marcador con nombre, la tabla conserva caption y los SVG informativos tienen nombre accesible. Esto es una revisión de producto, no una declaración formal de conformidad WCAG.

