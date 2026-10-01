# Informe final conjunto A1–A5 (28-09, entrega parcial verificada)

## Alcance ejecutado
Fases 0–6 en local individual: 10 agentes configurados (modelo heredado por omisión acordada), protección verificable, mapa core (7 vistas, 79 rutas, 39 tablas), baseline reproducible, 20 hallazgos (4 P0, 8 P1, 8 P2), plan de 8 paquetes y 7 implementados con regresión.

## Cambios (conservadores, reversibles)
- PKG-01 E3→A4: batch detail con owner (`get_hotel_detail_batch_owner`, 404 por defecto), `ownerKey None` denegado, `detailUrl` https Booking + tope 200. Repro cruzado OK.
- PKG-02 E3→A4: adjuntos `MAX 20MB` (contrato), borrado solo sin referencias, `pypdf` en requirements + import `BytesIO` faltante (PDF vuelve a extraer). Repro compartido OK.
- PKG-03 E3→A4: TSV neutraliza `=+-@|%` iniciales con `'` preservando roundtrip (1 regresión intermedia corregida sin enmendar).
- PKG-04 E2→A2: workspace `isSaving`+payload copiado+guardias mercado; `renderWorkspace`/`selectMarket`/Copilot/adjuntos/`loadSession` con guardias; polls con `isConnected`. Sintaxis + 8 JS OK.
- PKG-05 E1→A2: hardening overflow Copilot; medido sin desborde (1328<1440), 4 after-capturas sin pageerrors.
- PKG-06 E4→A5: bulk SerpAPI usa retry existente (sin llamadas; sin consumidores actuales).
- PKG-07 E3→A3: migración postgres en fail-fast (sin TRUNCATE accidental).
- PKG-08 E5→A4: JEV documentado (12 pasan con su env; 2 fallos drift preexistente; `langdetect` fuera de prod).

## Verificación
Backend 185 + JS 8 + Copilot local passed; TSV roundtrip preservado; operativa intacta (integrity ok); gasto 0/5 €; sin secretos en evidencias.

## No hecho / limitaciones explícitas
Zoom 200% y sesión prolongada sin medir; DOM acumulativo por diseño (H-13); auth monousuario sin cambios (H-20); coste proveedor real desconocido sin muestras (diferido, tope intacto); cifras solo de herramientas ejecutadas.

## Adenda PKG-09 (28-09, 22:47)
H-15 resuelto y verificado (trap+inert+retorno foco, sin pageerrors; suites 185+8 en verde).
Nota de procedencia: el diff `backups/pkg-04/atlas.js`→actual contiene `lockFocusable`/`trapLockTab`/`inert` (mtime 22:42) que no corresponde a ninguna edición registrada de E2 en esta sesión; el contenido se auditó, se adoptó explícitamente como PKG-09 y se verificó funcionalmente en lugar de revertirlo a ciegas. Reversión disponible en `backups/pkg-04/atlas.js`. Causa del cambio no atribuida: en investigación.

## Pendiente propuesto
Muestras reales mínimas (E4/A5) solo si alguna incertidumbre lo exige; paginación `hotels/history` (429KB) a mayor volumen; H-21 cosmético a 200%.

## Adenda continuación (28-09, 22:50)
App lanzada en `http://127.0.0.1:5000` (PID 4742, base operativa, `authRequired:false`).
Mediciones en copia aislada :5010 (detenida tras medir; operativa intacta):
zoom 200% sin overflow (nota H-21 P3); sesión prolongada estable (H-13 aceptado).
Documentos actualizados: `02-matriz-flujos.md`, `03-hallazgos.md`.
