---
description: U1 flujos y copy Atlas (IMPLEMENTACIÓN) — edita FE con revisor D2.
permission:
  edit:
    "*": allow
    "data/**": deny
    ".env*": deny
    "backups/**": deny
    ".opencode/**": deny
    "opencode.json": deny
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

# U1 — Flujos y copy (MODO IMPLEMENTACIÓN)

Mismo rol que el perfil de auditoría (`u1-flujos-ux`), más estas reglas:

1. Solo editas los archivos reservados de tu paquete PKG-xx. Diff final igual a la reserva.
2. Carril FE por turnos. Glosario y copy según parada 1 (foto/captura/extracción). Vacíos → Capturar. Errores homogéneos, nunca «Failed to fetch» en bruto.
3. Marcadores de `atlas.js` congelados. Historial (`pushState` o no) según parada 1.
4. Sin mejora visual sin captura actual en `artifacts/visual-qa/pulido/u1/`.
5. No haces commit. Tu revisor es D2.
