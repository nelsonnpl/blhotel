# Matriz de flujos (Fase 2–3, resultado 28-09)

Leyenda: pasa / falla / bloqueado / n-a. Evidencia en `artifacts/visual-qa/baseline-20260928/`.

| Recorrido | Estado | Evidencia |
|---|---|---|
| Arranque, health, desbloqueo dev (sin auth) | pasa | `/api/health ok`, lock renderiza, 28 capturas |
| Cambio vista/mercado, recarga | pasa con fixes | `selectMarket` ahora re-renderiza las 7 vistas (PKG-04); guardias post-await |
| Dashboard filtros/búsqueda/orden/mapa/inspector/histórico/export | pasa | captura + APIs <15ms |
| Hoteles tabla 38 filas, orden ADR, búsqueda | pasa | `hotels-1440x900.png`, 4038 nodos |
| Reputación ficha/comparación/filtros/paginación/evidencias | pasa | `reputation-1440x900.png` |
| Vuelos búsqueda/filtros/paginación/captura/comparativa/fullscreen | pasa | `flights-1440x900.png`; bulk retry (PKG-06) |
| Copilot conversaciones/borradores/adjuntos/envío/evidencias/errores/cancelación | pasa con fixes | guardias sesión+mercado, push adjuntos, catch (PKG-04); overflow verificado sin desborde (PKG-05) |
| Workspace capas/edición/guardado/conflicto/revisiones/cambio mercado | pasa con fixes | `isSaving`+payload copiado+guardias (PKG-04); 409 optimista conservado |
| Capturas perfil/lanzamiento/progreso/fallo/reintento/selección/comparación | pasa | `captures-1440x900.png`; migración postgres bloqueada fail-fast (PKG-07) |
| Teclado: tabulación, foco visible, Escape panel/drawer | pasa parcial | panel/drawer con Escape+foco; lock sin trap (H-15 documentado, no fix) |
| Zoom 200% (1920/1366 emulados, DSF x2) | pasa con nota | sin overflow horizontal en dashboard/hotels/copilot; artefacto P3: cabecera Copilot solapa 1 línea de evidencia (`zoom-1920z200-hotels.png`, en realidad vista Copilot) |
| Movimiento reducido | n-a | pendiente (media query existe en CSS:1015; sin prueba con `prefers-reduced-motion`) |
| 1920/1440/1366/1024 | pasa | 28 capturas; 1366 con fallo CDN transitorio + Reintentar OK |
| Sesión prolongada (5 ciclos × 7 vistas) | pasa | nodos estables 7132, tablas 11, heap 10MB, ~11 req/ciclo acotadas; sin fuga — H-13 aceptado sin cambio |
| Restauración aislada + integridad | pasa | `/var/.../atlas-restore-20260928`, integrity ok |

Ningún P0/P1 reproducido queda sin resolver salvo H-15/H-13/H-20 (documentados, fuera del plan mínimo).
