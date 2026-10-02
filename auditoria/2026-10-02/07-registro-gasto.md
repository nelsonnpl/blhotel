# 07-Registro de gasto · Pulido Atlas (tope lógico 5 €, clave actual sin límite físico)

El director lo abre en F0.8: tipo USD→EUR fijo del día, precio por búsqueda SerpAPI, saldos iniciales con `gasto.py`. Protocolo por acción: reserva (coste máximo) → negar si gasto+reserva > 4 € de trabajo (seguir hasta 5 € total) → saldos → ejecutar → saldos → coste REAL del proveedor (no el de la app, que infravalora, PA-80).

| 2026-10-02 09:15 | Copilot L1+L2 (reserva 2,00) | 2,00 | ~0,0045 (app 0,00043×2+0,0036; proveedor sin mover a esta precisión) | 0,6786 | 51 | no |
| 2026-10-02 09:30 | Copilot air+deepseek | (de 2,00) | proveedor 0,6786→0,6851 = 0,0065 total Copilot (air GLM agota tiempo, coste 0; deepseek ok 0,0040) | 0,6851 | 51 | no |
| 2026-10-02 09:35 | Reseñas Servatur (reserva 0,50) | 0,50 | 0,0076 (proveedor 0,6851→0,6927; job cdf8e7cf FAILED «sin JSON estructurado») | 0,6927 | 51 | sí (run fallido) |
| 2026-10-02 10:40 | SerpAPI MAD_LPA×3 (reserva 1,00 oleada 1) | 1,00 | 0,00 € (cuota free 51→54; job c5fcac49 succeeded, sin `api_key` persistida) | 0,6992* | 54 | sí (snapshots 171-172) |
| 2026-10-02 11:37 | (observado, no gastado) | — | SerpAPI 54→187 por consumidor externo de la clave compartida; no computa en el tope | 0,6992 | 187 | no |
| 2026-10-02 12:30 | Chat quick F4 (reserva 0,50 prueba de coste) | 0,50 | run 40 `cost_usd` 0,00239 > 0 ✓ (PKG-04 verificado en producción; harness 0,00236) | 0,7074 | 187 | sí (run 40) |

Reparto: Copilot live ≤2,00 € (2 casos unitarios primero, nunca `--strict` sin `--case`) · reseñas Servatur Monte Feliz 0,50 € · SerpAPI aérea oleada 1 ≤1,00 € (tras PA-97) · F4 coste ≤0,50 € · colchón 1,00 € (Jev Maps Servatur solo tras PA-81).

## Apertura F0.8 (2026-10-02)

- Tipo fijo del pulido: USD→EUR BCE 01-10-2026 = **1,1298** (último publicado; el del día 2 sale a las 16:00 CET).
- Precio SerpAPI/búsqueda: pendiente de `account.json` en F1B (con clave).
- Saldos iniciales: `gasto.py` sin claves en este entorno → `openrouter sin clave / serpapi sin clave`. Los saldos reales se leen en F1B.3 (protocolo por acción) antes de cada gasto.
