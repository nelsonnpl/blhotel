---
description: B1 rendimiento Atlas — entrega, render, red, SQLite. Mide antes y después. Revisa paquetes de W2.
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

# B1 — Rendimiento (MODO AUDITORÍA)

Equipo Debugging. Misión: entrega, parseo, render, memoria, red por vista, backend con 10× datos (copia aislada), SQLite. Mides antes y después. En implementación revisas los paquetes de W2.

Base: `http://127.0.0.1:5060`. Evidencias: `artifacts/visual-qa/pulido/b1/`. Puedes extender `tests/e2e/**` (único junto a G1). Prohibido el gasto real. No preguntes al usuario.

## Pasos

1. Lee contrato, pre-auditoría (PA-01 a PA-07) y línea base del director en `auditoria/2026-10-02/baseline.md`. NO midas rendimiento mientras otros ejecutan: usa la línea base y repite medidas puntuales al final de la fase.
2. Confirma PA-01 (estáticos sin gzip: `flask_app.py` ≈127–143 salta estáticos, `send_file` streamed; propuesta gzip en memoria por `mtime` + `Vary` + `immutable`), PA-02 (maplibre-gl.css unpkg + Google Fonts bloquean pintado, sin SRI), PA-04 (`api()` en `atlas.js:52` sin timeout), PA-05 (14 `document.addEventListener` duplicados), PA-06 (116 `innerHTML`, `renderWorkspace` repinta), PA-07 (N+1 reseñas, `capture_history` 500 fotos, `rate_calendar` sin caché, `hotels/history` sin paginar).
3. Escribe el ADR en tu informe: compresión + diferir terceros sí; dividir `atlas.js` en módulos ES por vista SOLO si a 4× CPU el parseo+evaluación > ~150 ms o hay tareas largas >200 ms al arrancar.
4. Backend con 10× datos solo en copia aislada (datos sintéticos solo ahí), nunca en operativa.
5. Escribe `auditoria/2026-10-02/informes/b1.md` (plantilla, máx. ~25 + «Micro-mejoras»).
6. Resumen ≤15 líneas.

## Semillas propias

- PA-01 a PA-07 según pre-auditoría. Medición PA-03: 4× CPU + Fast 3G, mediana de 5.
