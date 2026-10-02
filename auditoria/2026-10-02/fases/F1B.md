# F1B · Pruebas reales con gasto (secuencial, solo el director ejecuta)

Protocolo por acción: F1B.1 anotar reserva (máximo) → F1B.2 negar si gasto+reserva > 4 € (seguir hasta 5 € total) → F1B.3 saldos con `gasto.py` → F1B.4 ejecutar → F1B.5 releer saldos, anotar coste REAL del proveedor (no el de la app, PA-80) → F1B.6 si escribió en operativa: parar `:5070` con 0 jobs y refrescar copia con `backup_db.py`.

- F1B.7 Copilot live (casos de I1): primero `--live --case X` con 2 casos (coste unitario), después solo los `--case` que quepan. Tope 2,00 €.
- F1B.8 Un análisis de reseñas en `:5070` con backup previo (Servatur Monte Feliz, `budgetUsd` 0,50). Tope 0,50 €. El resultado queda visible en su ficha.
- F1B.9 Reservas: SerpAPI aérea oleada 1 (tras PA-97) ≤1,00 € · F4 coste ≤0,50 € · colchón 1,00 € (Jev Maps Servatur solo tras PA-81).
- F1B.10 Jev excluido salvo lo decidido en parada 1. Riesgos PA-81 vigentes.
