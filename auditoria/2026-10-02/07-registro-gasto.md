# 07-Registro de gasto · Pulido Atlas (tope lógico 5 €, clave actual sin límite físico)

El director lo abre en F0.8: tipo USD→EUR fijo del día, precio por búsqueda SerpAPI, saldos iniciales con `gasto.py`. Protocolo por acción: reserva (coste máximo) → negar si gasto+reserva > 4 € de trabajo (seguir hasta 5 € total) → saldos → ejecutar → saldos → coste REAL del proveedor (no el de la app, que infravalora, PA-80).

| 2026-10-02 09:15 | Copilot L1+L2 (reserva 2,00) | 2,00 | ~0,0045 (app 0,00043×2+0,0036; proveedor sin mover a esta precisión) | 0,6786 | 51 | no |
| 2026-10-02 09:30 | Copilot air+deepseek | (de 2,00) | proveedor 0,6786→0,6851 = 0,0065 total Copilot (air GLM agota tiempo, coste 0; deepseek ok 0,0040) | 0,6851 | 51 | no |
| 2026-10-02 09:35 | Reseñas Servatur (reserva 0,50) | 0,50 | 0,0076 (proveedor 0,6851→0,6927; job cdf8e7cf FAILED «sin JSON estructurado») | 0,6927 | 51 | sí (run fallido) |

Reparto: Copilot live ≤2,00 € (2 casos unitarios primero, nunca `--strict` sin `--case`) · reseñas Servatur Monte Feliz 0,50 € · SerpAPI aérea oleada 1 ≤1,00 € (tras PA-97) · F4 coste ≤0,50 € · colchón 1,00 € (Jev Maps Servatur solo tras PA-81).

## Apertura F0.8 (2026-10-02)

- Tipo fijo del pulido: USD→EUR BCE 01-10-2026 = **1,1298** (último publicado; el del día 2 sale a las 16:00 CET).
- Precio SerpAPI/búsqueda: pendiente de `account.json` en F1B (con clave).
- Saldos iniciales: `gasto.py` sin claves en este entorno → `openrouter sin clave / serpapi sin clave`. Los saldos reales se leen en F1B.3 (protocolo por acción) antes de cada gasto.
