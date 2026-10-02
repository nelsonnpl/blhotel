---
agent: director
subtask: false
description: Pulido Atlas — implementar por oleadas (F3 F4 hasta parada 2)
---

Estado: !`git status --porcelain` · Rama: !`git branch --show-current` · Registro: @auditoria/2026-10-02/00-registro.md

# /pulido-implementar

1. Lee el registro. Si NO contiene `PARADA-1: APROBADO`, niégate y termina el turno.
2. Anota `$ARGUMENTS` como decisiones del usuario en `04-decisiones.md` y el registro.
3. Verifica que `.opencode/agents/` contiene el perfil IMPLEMENTACIÓN (copiado en parada 1 + reinicio de OpenCode). Si no, detente y pide el reinicio.
4. Ejecuta F3 por oleadas (lotes de ≤3, un escritor por carril FE/BE/QA, árbol quieto, verificación en `:5061`/`:5060`, revisores en paralelo, un commit por paquete `tipo(alcance): … [PKG-xx]` con `git diff --cached --name-only` igual a la reserva, regresión al cerrar oleada).
5. Ejecuta F4 integral (regresión 6 anchos × 2 temas, reduced-motion + con movimiento, prototipo `:8001`, WebKit/Firefox smoke, `perf.py` antes/después, a11y, consola/red, prueba de coste ≤0,50 €, `contact_sheet.py` → `09-informe-final.md`).
6. Presenta parada 2 y termina tu turno. No sigas sin `PARADA-2: APROBADO`.
