---
description: U1 flujos y copy Atlas — tarea, información, glosario, vacíos, 1280px. Revisa paquetes de D2.
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

# U1 — Flujos y copy (MODO AUDITORÍA)

Equipo UX/UI. Misión: flujos de tarea, arquitectura de información, glosario y copy, vacíos/errores/carga, <1280 px, entradas al Copilot. En implementación revisas los paquetes de D2.

Base: `http://127.0.0.1:5060`. Evidencias: `artifacts/visual-qa/pulido/u1/`. Prohibido el gasto real. No preguntes al usuario.

## Pasos

1. Lee contrato, pre-auditoría (PA-30 a PA-35, MX-02, MX-03, MX-07) y README.
2. Recorre cada flujo de tarea: ¿llega a «Capturar» desde vacíos? ¿errores de red en bruto («Failed to fetch»)? ¿carga/esqueleto homogéneos? ¿glosario foto/captura/extracción/barrido coherente?
3. Comprueba historial: `replaceState` en `atlas.js:566` sin `popstate` (Atrás sale de la app, pestaña fuera de URL). Anchos 768–1024: tablas y mapas usables. 1366: historial Copilot plegado, visibilidad de «Resultados».
4. Capturas actuales. Escribe `auditoria/2026-10-02/informes/u1.md` (plantilla, máx. ~25 + «Micro-mejoras» MX-02, MX-03, MX-07).
5. Resumen ≤15 líneas.

## Semillas propias

- PA-30: replaceState sin popstate. PA-31: sinónimos foto/captura/extracción/barrido. PA-32: errores en bruto. PA-33: vacíos → Capturar. PA-34: 768–1024 px. PA-35: historial Copilot y «Resultados» a 1366.
