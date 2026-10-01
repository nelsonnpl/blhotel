# Comparativa antes/después (28-09, mismas condiciones: copia visual.sqlite, :5010)

## Visual
- 28 capturas base (`*-1440x900.png` etc.) + 4 `after-*-1440x900.png` + `viz-clip.png`.
- Copilot: sin overflow documental (scrollW=1440=clientW; viz 525+803=1328<1440); hardening `min-width:0/overflow-x:clip` + grid `minmax(0,…)` (PKG-05). Sin regresión en dashboard/hotels/workspace (after OK, sin pageerrors).
- Consola: solo warnings WebGL mapa + 1 racha `ERR_NETWORK_CHANGED` CDN (fonts/unpkg) con Reintentar funcional.

## Rendimiento (local, copia 18.5M)
- APIs: health 8ms/96B, targets 2ms, snapshots 3-5ms/46KB, captures 14ms, photos 2ms, hotels/history 11ms/429KB, dashboard 8ms/21KB, air-runs 1ms, external 1-2ms, workspaces 1ms, catalog 14ms/48KB. Sin cambios antes/después (fixes sin coste medible; 429KB sugiere paginar a mayor volumen — no actuado).
- Estáticos: atlas.js 318K + atlas.css 123K (+CDN maplibre/fonts).
- DOM por vista acumulada: 1759→7132 nodos (diseño: vistas montadas; sin cambio).
- Suites: backend 185 passed (1 regresión intermedia detectada y corregida en el acto), JS 8 passed, Copilot local passed.

## Gasto externo
0 € / 5 € (sin llamadas reales; todo local o bloqueado).
