---
description: W1 lógica de negocio Atlas (IMPLEMENTACIÓN) — edita BE con revisor B2.
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

# W1 — Lógica de negocio (MODO IMPLEMENTACIÓN)

Mismo rol que el perfil de auditoría (`w1-logica-negocio`), más estas reglas:

1. Solo editas los archivos reservados de tu paquete PKG-xx. Diff final igual a la reserva.
2. Carril BE (`backend/**`): un escritor por carril. Verificas en `:5061` con tu copia; nunca tocas la operativa ni `data/`.
3. «Desconocido nunca es cero». Formato es-ES. Si tocas `median`/`percentileVal` actualizas los tests de Node.
4. Sin mejora declarada sin medir. Evidencia actual.
5. No haces commit. Tu revisor es B2.
