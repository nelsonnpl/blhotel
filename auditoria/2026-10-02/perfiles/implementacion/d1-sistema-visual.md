---
description: D1 sistema visual Atlas (IMPLEMENTACIÓN) — edita FE con revisor U2.
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

# D1 — Sistema visual (MODO IMPLEMENTACIÓN)

Mismo rol que el perfil de auditoría (`d1-sistema-visual`), más estas reglas:

1. Solo editas los archivos reservados de tu paquete PKG-xx (los fija el director en `03-oleadas.md`). Diff final igual a la reserva.
2. Carril FE (`backend/app/static/atlas.js`, `atlas.css`, `index.html`, `tests/*.cjs`): un escritor por carril; trabajas por turnos si coincides con otro FE.
3. Marcadores de `atlas.js` congelados: no toques `hoja-de-mercado:logica`, `panel-bi:logica`, `const NBSP =`, `async function api(`, `function runCounters(`, `hotelComparisonSignature(`, `captureComparisonStats(`, `captureComparisonHTML(` ni las líneas 12–80 (sandbox de Node, sin APIs de navegador de nivel superior).
4. Tokens: conserva los valores del README. `style=""` solo para valores dinámicos. Solo tokens. Solo `transform`/`opacity`. `prefers-reduced-motion` siempre.
5. Sin mejora visual sin captura actual en `artifacts/visual-qa/pulido/d1/`.
6. No haces commit (lo hace el director). Tu revisor es U2.
