# 07-Registro de gasto · Pulido Atlas (tope lógico 5 €, clave actual sin límite físico)

El director lo abre en F0.8: tipo USD→EUR fijo del día, precio por búsqueda SerpAPI, saldos iniciales con `gasto.py`. Protocolo por acción: reserva (coste máximo) → negar si gasto+reserva > 4 € de trabajo (seguir hasta 5 € total) → saldos → ejecutar → saldos → coste REAL del proveedor (no el de la app, que infravalora, PA-80).

| Fecha | Acción | Reserva | Coste real | Saldo OpenRouter | Saldo SerpAPI | Base escrita |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — | — |

Reparto: Copilot live ≤2,00 € (2 casos unitarios primero, nunca `--strict` sin `--case`) · reseñas Servatur Monte Feliz 0,50 € · SerpAPI aérea oleada 1 ≤1,00 € (tras PA-97) · F4 coste ≤0,50 € · colchón 1,00 € (Jev Maps Servatur solo tras PA-81).
