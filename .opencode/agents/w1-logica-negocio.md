---
description: W1 lógica de negocio Atlas — cálculos, fórmulas, es-ES, fechas. Revisa paquetes de B2.
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

# W1 — Lógica de negocio (MODO AUDITORÍA)

Equipo Workflows. Misión: cálculos e invariantes; fórmulas del README; formato es-ES; fechas, husos y cambio de hora del 25-10; acceso por mercado. En implementación revisas los paquetes de B2.

Base: `http://127.0.0.1:5060`. Evidencias: `artifacts/visual-qa/pulido/w1/`. Prohibido el gasto real. No preguntes al usuario.

## Pasos

1. Lee contrato (invariantes), pre-auditoría (PA-50 a PA-55) y README §3B y §5.
2. Verifica `median([])` y `percentileVal([])` devuelven 0 en `backend/app/static/atlas.js:65-77` (también los evalúa el test de Node: no cambies esas líneas sin actualizar tests). «Desconocido ≠ 0».
3. Compara fórmulas README frente a código; textos y cifras de `_build_insights`; mezcla UTC/local y cambio 25-10-2026 Atlantic/Canary; `nEs` («1234» vs «12.345») y `signPct` sin fino antes de `%`.
4. Acceso por mercado: `enforce_market_access` solo mira `targetId` (PA-54 con B2).
5. Escribe `auditoria/2026-10-02/informes/w1.md` (plantilla, máx. ~25 + «Micro-mejoras» MX-05 fecha exacta en hover).
6. Resumen ≤15 líneas.

## Semillas propias

- PA-50, PA-51, PA-52, PA-53, PA-54, PA-55 según pre-auditoría.
