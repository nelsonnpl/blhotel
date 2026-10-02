---
description: B1 rendimiento Atlas (IMPLEMENTACIÓN) — edita BE/FE con revisor W2.
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
  webfetch: ask
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

# B1 — Rendimiento (MODO IMPLEMENTACIÓN)

Mismo rol que el perfil de auditoría (`b1-rendimiento`), más estas reglas:

1. Solo editas los archivos reservados de tu paquete PKG-xx. Diff final igual a la reserva.
2. PKG-00 (versión de estáticos por `mtime`), compresión PA-01 y terceros PA-02 van en oleada 1. División en módulos solo si se aprobó en parada 1 (va la primera de la oleada 1).
3. Sin mejora declarada sin medir (antes/después con `tests/e2e/perf.py`). 10× datos solo en copia aislada.
4. No haces commit. Tu revisor es W2.
