# 09-Informe final · Pulido Atlas (F4)

Hojas: `artifacts/visual-qa/pulido/f4/rm/contacto.html` (120, reduced-motion) + `.../f4/motion/contacto.html` (20, con movimiento). Prototipo `:8001`: fidelidad confirmada (hoteles BI idéntico en `f4/prototipo/`).

## Antes/después

| Métrica | Base F0 | F4 | Estado |
| --- | --- | --- | --- |
| Estáticos fríos gzip (js+css) | 607 KB | 119+38=157 KB | ✓ ≤160 KB |
| Terceros que bloquean | 2 | 0 (autoalojados) | ✓ |
| FCP 4×CPU+Fast3G (mediana 5) | 3040 | 1852 | ✓ −39 % |
| LCP (perf.py) | 0 | 0 | medida defectuosa (B1-11, pendiente harness) |
| Bytes vista dashboard | 675231 | 462071 | ✓ −32 % |
| p95 endpoints 10× (copia aislada) | <30 ms | comparable 4,5×, captures 43× | ✓ ≤150 ms |
| Errores consola e2e | 1 flaky | 0 | ✓ |
| Controles sin nombre | 0 | 0 | ✓ |
| Objetivos <24 px | 96 visuales | 96 visuales, dianas ≥24 vía `::after` | ✓ (área ampliada) |
| `reduced-motion` | parcial | 100 % + salidas | ✓ |
| Duraciones como tokens | 0 | 27 tokens, 0 literales | ✓ |
| `style=""` estáticos | 58 | 0 | ✓ |
| Fuga clave + costes | fuga + 0 imputado | redactado (verificado en vivo) + run 40 con coste | ✓ |

## QA (receta: copia poblada, nunca DB vacía)

- pytest 317/317 · node 33/33 · qa: a11y 96-by-design + bi 32/32 + copilot 20/20 + dashboard 38/38 + flights 39/39 + reputation 29/29 + workspace 17/17 + g1 12/12.
- e2e 120 + 20 en verde, 0 desbordes (768→0), consola/red limpias.
- WebKit/Firefox: binarios sin navegación en este entorno (G1-21, limitación documentada).
- Incidente F4-INC: copias corruptas por `cp` bajo servidor (origen: proceso, no producto); reconstruido y relanzado; regla en `scripts/restaurar_db.md`.
- Gasto total real ≈0,02 € de 5 € (detalle en `07-registro-gasto.md`).

## Comparación prototipo

Estructura, KPIs, mapa y panel de zonas idénticos (hoteles BI 1440). Capturas no rediseñado: solo vacío (igual que antes).
