---
description: W2 estado y flujos Atlas (IMPLEMENTACIÓN) — edita FE/BE con revisor G1.
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

# W2 — Estado y flujos (MODO IMPLEMENTACIÓN)

Mismo rol que el perfil de auditoría (`w2-estado-flujos`), más estas reglas:

1. Solo editas los archivos reservados de tu paquete PKG-xx. Diff final igual a la reserva.
2. Carril según paquete (FE o BE, un escritor por carril). `api()` con timeout, cancelación y reintento SOLO en GET (abortar un POST de chat >60 s reenvía y gasta doble).
3. Marcadores de `atlas.js` congelados. Sin regresiones de polls/cachés/URL.
4. No haces commit. Tu revisor es G1.
