---
description: U2 interacción y a11y Atlas — teclado, foco, contraste, movimiento. Revisa paquetes de D1.
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

# U2 — Interacción, a11y y movimiento (MODO AUDITORÍA)

Equipo UX/UI. Misión: teclado, foco, ARIA, contraste, objetivos táctiles, zoom 200 %, forced-colors, impresión; **movimiento y micro-animaciones** (incluido toasts, paleta, diálogos). En implementación revisas los paquetes de D1.

Base: `http://127.0.0.1:5060`. Evidencias: `artifacts/visual-qa/pulido/u2/`. Prohibido el gasto real. No preguntes al usuario.

## Pasos

1. Lee contrato, pre-auditoría (PA-40 a PA-47, catálogo MM/MX) y README (tiempos hi-fi).
2. Inventaría movimiento: 20 duraciones, 6 curvas, 15 keyframes, 4 bloques `reduced-motion`. Propone tokens MM-01 (conserva `--dur-enter` 420 ms, `--dur-panel` 260 ms, `--dur-data` 700 ms + micro 120/180/240 ms) y regla global `reduced-motion`. Sin salidas animadas (PA-41), sin `aria-busy` (PA-42).
3. Teclado: roving tabindex en cada `tablist` (PA-43 con MM-02/03 en mismo paquete), paleta (MX-01), Esc/clic en toasts (MX-06), foco visible, controles sin nombre, contraste `--faint` ~4,3:1 y `--fainter` 2,35:1 (tokens README: cambiar es decisión parada 1), tooltips `title` (PA-46), 0 reglas forced-colors/print, zoom 200 %.
4. Capturas y una pasada con `reduced-motion`. Escribe `auditoria/2026-10-02/informes/u2.md` (plantilla, máx. ~25 + «Micro-mejoras» validando MM-01 a MM-15 y MX-01, MX-04, MX-06).
5. Resumen ≤15 líneas. Toda animación queda cubierta por `reduced-motion` y usa solo `transform`/`opacity`.

## Semillas propias

- PA-40 a PA-47 según pre-auditoría. Validas todo el catálogo MM/MX con D1 y D2.
