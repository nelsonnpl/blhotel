# 04-Decisiones · Pulido Atlas (para la parada 1)

## D1 · Dividir `atlas.js` en módulos ES

ADR B1: NO (5927 líneas, pero parse+eval sin evidencia >150 ms a 4×CPU y sin largas >200 ms al arrancar; perf FCP ~3 s bajo throttling dominado por red/pintado). Recomendación: no dividir; reevaluar si F4 lo justifica.

## D2 · Desvíos del README hi-fi

- Contraste `--faint` (4,29/3,97:1) y `--fainter` (2,35/2,17:1, oscuro 3,28:1): no llegan a 4,5:1. Recomendación: ajustar valores (decisión de parada 1, son tokens README).
- Fuentes 33→~15 roles y radios 24→8 roles: consolidar conservando valores (PKG-15).
- Duraciones a tokens MM-01 conservando 420/260/700 (PKG-16).

## D3 · Separar el worker

Un hilo FIFO: un Jev de 30 min bloquea el Copilot (B2-07, P1). Recomendación: SÍ, cola rápida + cola larga (PKG-26, oleada 5).

## D4 · MapLibre y fuentes

2 terceros bloquean + unpkg sin SRI (B1-03, D2-04/G1-12). Opciones: (a) autoalojar 4.7.1 + fuentes (resuelve SRI, H-19 y CSP unpkg); (b) diferir CSS + SRI. Recomendación: (a) si el peso es aceptable, si no (b). PKG-06.

## D5 · Historial entre vistas

Atrás sale de la app (U1-01 P1). Recomendación: SÍ `pushState` + `popstate` (PKG-09).

## D6 · Glosario

`foto`/`captura`/`extracción`/`barrido` como sinónimos (U1-03). Propuesta: **foto** = snapshot de mercado con fecha (la unidad comparable); **captura** = la acción/proceso de obtener fotos; **extracción** = fecha de check-in dentro de una foto; **barrido** se elimina (un solo uso). PKG-10.

## D7 · Semántica verde/rojo

Significado por contexto + umbrales inconsistentes (D2-14/15/16). Recomendación: guía explícita en PKG-12 (verde = favorable al revenue propio, rojo = riesgo; outliers en azul se mantienen por ser comparativa, no estado).

## D8 · Jev

Seguía excluido salvo Maps ≤1 € tras PA-81. F1B: análisis de reseñas Booking falla («sin JSON estructurado», 0,0076 € reales). Recomendación: mantener exclusión; probar UNA captura Maps en Servatur (colchón ≤1 €) tras PKG-03+PKG-23; si falla, Jev queda fuera del pulido.

## Corrección F2 del director (sin paquete)

`ia/casos-live.md` usaba IDs inexistentes (`luna_missing_pms`…). Válidos: `luna_quick_market`, `minimax_hotel_analysis`, `air_connectivity_analysis` (GLM agota tiempo, coste 0; fallback Luna previsto), `critic_independent_check`, `deepseek_synthesis`. F1B ejecutó L1/L2/air/deepseek reales. El director actualiza el archivo en F2.
