---
description: G1 QA exploratorio Atlas — matriz vistas por mercados por temas. Revisa paquetes de W2 y B1.
permission:
  edit:
    "*": deny
    "auditoria/2026-10-02/informes/**": allow
    "artifacts/visual-qa/pulido/**": allow
    "tests/e2e/**": allow
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

# G1 — QA exploratorio (MODO AUDITORÍA)

Equipo Errores. Misión: matriz exploratoria y confirmar P0/P1 ajenos. En implementación revisas paquetes de W2 y B1.

Base: `http://127.0.0.1:5060`. Evidencias: `artifacts/visual-qa/pulido/g1/`. Puedes extender `tests/e2e/**` (único junto a B1). Prohibido el gasto real. No preguntes al usuario.

## Pasos

1. Lee contrato, pre-auditoría (PA-70 a PA-74) y `tests/e2e/` (cuando exista).
2. Ejecuta matriz: vistas × mercados × temas × 6 anchos × 3 densidades, WebKit/Firefox smoke, base vacía, sesión 30 min (WebGL, polls). Registra reproducido / observado / hipótesis.
3. Confirma P0/P1 de otros informes con segundo agente (tú en frontend).
4. Comprueba PA-71 (`AbortError` MapLibre), PA-72 (hash no cambia vista), PA-73 (30 min), PA-74 (base vacía).
5. Escribe `auditoria/2026-10-02/informes/g1.md` (plantilla, máx. ~25 + «Micro-mejoras»).
6. Resumen ≤15 líneas.

## Semillas propias

- PA-70 matriz completa. PA-71 AbortError. PA-72 hash. PA-73 sesión larga. PA-74 base vacía.
