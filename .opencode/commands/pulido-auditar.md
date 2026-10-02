---
agent: director
subtask: false
description: Pulido Atlas — auditar (F0 F1 F1B F2 hasta parada 1)
---

Estado: !`git status --porcelain` · Rama: !`git branch --show-current` · Registro: @auditoria/2026-10-02/00-registro.md

# /pulido-auditar

Ejecuta F0 → F1 → F1B → F2 y se detiene en la parada 1.

1. Lee `auditoria/2026-10-02/PLAN_MAESTRO.md`, `00-contrato.md` y `fases/F0.md`.
2. Ejecuta F0 paso a paso (F0.1–F0.8): humos de permisos/paralelismo/imágenes, commit del kit con `git add -f opencode.json .opencode/agents .opencode/commands auditoria/2026-10-02 tests/e2e`, tag `pre-pulido`, rama `pulido/auditoria`, backup n.º 1, captura Booking real F0.5 en `:5070` (mercado 1, backup previo, esperar fin, parar), backup n.º 2, copias, `:5060` + `:8001`, línea base, registro y gasto.
3. Ejecuta F1 en tandas de 3 con `task` (perfil AUDITORÍA, base `http://127.0.0.1:5060`, evidencias `artifacts/visual-qa/pulido/<id>/`, gasto prohibido). Cada entrega: `informes/<id>.md` + resumen ≤15 líneas.
4. Ejecuta F1B secuencial (solo tú ejecutas gasto, protocolo de reserva, tope 5 €, I1 diseña casos, nunca `--strict` sin `--case`).
5. Ejecuta F2 con G1 y B2: `02-backlog.md`, `03-oleadas.md`, `04-decisiones.md`.
6. Presenta parada 1 (10 hallazgos, oleadas, decisiones, gasto) y termina tu turno. No sigas sin `PARADA-1: APROBADO`.
