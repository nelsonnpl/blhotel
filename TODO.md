# Revenue Panel TODO

## Rediseño avanzado

- [x] Línea de comandos interactiva: barra superior estilo terminal real (`.cmd-bar`) con comandos rápidos.
- [x] KPIs técnicos y enriquecidos: tarjetas con medianas, rangos y micro-indicadores dinámicos.
- [x] Gráficos SVG interactivos: sustituir barras HTML por gráfico SVG dinámico con guías y tooltips integrados.
- [x] Consola Scraper en vivo: terminal simulado (`.console-box`) con logs de progreso Decodo.
- [x] Highlights premium de RIU: resalte dorado/ámbar para hoteles RIU en tablas y mapa.
- [x] Mapa enriquecido con drawer: pines flotantes con etiquetas de precio y panel lateral (`.map-drawer`) al seleccionar hotel.
- [x] Filtros avanzados instantáneos: acciones de un clic para Solo RIU, Gaps Críticos (>15%) y ratings.
- [x] Vista Análisis RIU: gap, ranking, banda RIU-vs-mercado, alertas y acciones rápidas.

## Auditoría UX/UI

- [ ] Unificar la dirección de producto entre Flask y `web-next` para evitar dos frontends divergentes.
- [ ] Mejorar responsive móvil/tablet del panel Flask, especialmente topbar, tablas y drawer del mapa.
- [ ] Añadir estados vacíos más accionables para dashboard, mapa y explorador cuando no hay fotos.
- [ ] Revisar accesibilidad de controles terminal: labels, foco visible, contraste y `aria-live` en logs.
- [ ] Añadir verificación visual automatizada del panel principal tras cambios de UI.
