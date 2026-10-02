---
agent: director
subtask: false
description: Pulido Atlas — integrar a main (F5 tras parada 2)
---

Estado: !`git status --porcelain` · Rama: !`git branch --show-current` · Registro: @auditoria/2026-10-02/00-registro.md

# /pulido-cerrar

1. Lee el registro. Si NO contiene `PARADA-2: APROBADO`, niégate y termina el turno.
2. Ejecuta F5: backup n.º 3 → merge de la última oleada a `main` sin push → arranque único sobre la base operativa para migraciones con `integrity_check` y recuentos → tag `pulido-v1` → registro cerrado.
3. Informa y termina.
