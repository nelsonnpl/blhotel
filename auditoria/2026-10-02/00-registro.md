# 00-Registro · Pulido Atlas

Log de una línea por evento: fecha-hora · fase-paso · quién · qué · resultado. El director lo abre en F0.8 y lo mantiene al día.

| Fecha | Paso | Quién | Evento |
| --- | --- | --- | --- |
| 2026-10-02 08:30 | F0.1 | director | Fuentes leídas (contrato, preauditoría, AGENTS, README hi-fi, CHECKLIST 199/199) | OK |
| 2026-10-02 08:35 | F0.2 | director | Humos: árbol limpio, 2 tareas paralelo OK, PNG legible, `.env` intacto | OK |
| 2026-10-02 08:37 | F0.3 | director | Commit kit `4105fb1` + tag `pre-pulido` + rama `pulido/auditoria` (61 ficheros; `.pyc` excluidos; archivo 28-09 sin versionar) | OK |
| 2026-10-02 08:40 | F0.4B | usuario | Autoriza detener :5012 (PID 23824) | OK |
| 2026-10-02 08:41 | F0.5 | director | Captura Booking mercado 1 (job 2ae52e7c, 4 fotos, perfil 06-10/7n/2ad) → succeeded; run 26 partial | OK |
| 2026-10-02 08:43 | F0.5B | director | Lección WAL: captura en `-wal` sin checkpoint; `cp` solo-`.sqlite` rancia → copias desde backup nº2; `sqlite3 -readonly` falla en WAL (quitado en `estado_jobs.sh`; usar Python `mode=ro`) | OK |
| 2026-10-02 08:44 | F0.6 | director | Backup nº2 `backups/pulido-20261002-084342.sqlite` → `trabajo.sqlite`+`be.sqlite` (run 26 verificado) → :5060 (claves en blanco) + :8001 | OK |
| 2026-10-02 09:00 | F0.7 | director | Base: pytest 242/242, node 31/31. Chromium bloquea :5060 (SIP) → flag en 9 scripts. `analytics/query` a blanca. Desbordes 768 (42–105 px). qa en verde salvo flights (bloqueo de pago por diseño) y a11y (desglose pendiente). perf 4×CPU en `baseline.md` (LCP 0: revisar) | OK |
| 2026-10-02 09:05 | F0.8 | director | Registro abierto. Gasto: BCE 1,1298; saldos iniciales pendientes de F1B (sin claves en este entorno) | OK |
| 2026-10-02 09:50 | F1 | director | 10/10 informes en tandas de 3 (2 reintentos por sobrecarga backend). G1 añade `qa_g1_bloqueos.py` 12/12. I1 IDs live inválidos → corregidos en F2 | OK |
| 2026-10-02 10:20 | F1B | director | Copilot 5 pagos + 1 error gratis (GLM timeout); reseñas Servatur FAILED tras 0,0076 €. Real total ≈0,014 €. Backup pre/post + copias refrescadas, :5070 parada, :5060 reiniciada | OK |
| 2026-10-02 10:35 | F2 | director | `02-backlog.md` (7 P0, P1/P2/P3) + `03-oleadas.md` (27 PKG) + `04-decisiones.md` (8) + commit `012e01e` | OK |
| 2026-10-02 10:42 | PARADA-1 | usuario+director | «ejecuta todo el plan» = APROBADO con las 8 recomendaciones D1–D8. Adaptación: sin OpenCode-desktop; F3 con subagentes en modo IMPLEMENTACIÓN | **PARADA-1: APROBADO** |
| 2026-10-02 11:40 | O1-cierre | director | 8/8 PKG + regresión (pytest 263, node 33, smoke FE) + SerpAPI MAD_LPA×3 (0 €, sin leak) + backup `113738` + copias. *OR 0,6992 con retardo de contador, no gasto nuevo | OK |
| 2026-10-02 12:30 | O2-cierre | director | 6/6 PKG (09 pushState, 10 glosario+errores con 1 remate, 11 Capturas, 12 ejes, 13 768→0, 14 es-ES) + pytest 263 + node 33 + humo 20/20 | OK |
| 2026-10-02 13:30 | O3-cierre | director | 6/6 PKG (15+15B tokens, 16 movimiento con 1 fix, 17 tabs, 18 mapas, 19 contraste) + 1 NO APTO→APTO + 1 APTO-PARCIAL→15B + cota gzip 42 KB + pytest 263 + humo 16/16. Desvío doc: MM-02/03 animan width (cubierto por reduce) | OK |
| 2026-10-02 14:10 | O4-cierre | director | 4/4 PKG (20 cifras, 21 search+modelos+adjuntos, 22 MoA+comparable 4.5×, 23 history+Jev) + pytest 292 + node 33 | OK |

Marcas: `PARADA-1: APROBADO` · `PARADA-2: APROBADO` (las anota el director al aprobar el usuario).
