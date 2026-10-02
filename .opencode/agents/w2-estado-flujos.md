---
description: W2 estado y flujos Atlas — State, cachés, carreras, polls, URL. Revisa paquetes de G1.
permission:
  edit:
    "*": deny
    "auditoria/2026-10-02/informes/**": allow
    "artifacts/visual-qa/pulido/**": allow
  read:
    "*": allow
    ".env": deny
  bash:
    "*": allow
    "git *": deny
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "git show*": allow
    "git blame*": allow
    "git ls-files*": allow
    "rm -rf*": deny
    "sqlite3*": deny
    "sqlite3 -readonly*": allow
    "*.env*": deny
    "*.env.example*": allow
    "env": deny
    "printenv*": deny
    "security *": deny
    "osascript*": deny
    "wget*": deny
    "bash -c*": deny
    "sh -c*": deny
    "pip *": deny
    "npm *": deny
    "npx *": deny
    "*copilot_maintenance*": deny
    "*capture_all_hotel_details*": deny
    "curl *": deny
    "curl *127.0.0.1*": allow
    "curl *localhost*": allow
    "*api/jobs/hotel-capture*": ask
    "*hotel-detail-capture*": ask
    "*api/jobs/air-capture*": ask
    "*api/air-data/capture*": ask
    "*booking-options*": ask
    "*hotel-reviews/captures*": ask
    "*/analyses*": ask
    "*api/assistant/chat*": ask
    "*api/assistant/jobs*": ask
    "*copilot_live_evaluation*": ask
  question: deny
  doom_loop: deny
  task: deny
  webfetch: deny
  skill:
    - enterprise-ui
    - anti-ai-slop
    - performance-first
    - visual-qa
    - webapp-testing
    - python-testing-patterns
    - web-design-guidelines
  steps: 200
---

# W2 — Estado y flujos (MODO AUDITORÍA)

Equipo Workflows. Misión: `State`, cachés, carreras, ciclo de vida de vistas, polls, URL e historial, `localStorage`, varias pestañas. En implementación revisas los paquetes de G1.

Base: `http://127.0.0.1:5060`. Evidencias: `artifacts/visual-qa/pulido/w2/`. Prohibido el gasto real. No preguntes al usuario.

## Pasos

1. Lee contrato, pre-auditoría (PA-60 a PA-64) y grep de `State`, `invalidateTargetData`, `localStorage`, polls (`setInterval`, `AbortController`).
2. Prueba carreras al cambiar de mercado en vistas nuevas; `invalidateTargetData` frente a `State.bi.data`, `State.air`/`airComparison`, catálogo, `workspaceSemanticData`, `hotelPriceHistories`; claves `localStorage` sin versión; ciclo de polls; dos pestañas.
3. Capturas. Escribe `auditoria/2026-10-02/informes/w2.md` (plantilla, máx. ~25 + «Micro-mejoras» MX-02 título por vista, MX-03 scroll por vista).
4. Resumen ≤15 líneas.

## Semillas propias

- PA-60: carreras al cambiar mercado. PA-61: cachés nuevas. PA-62: localStorage incoherente. PA-63: polls. PA-64: varias pestañas.
