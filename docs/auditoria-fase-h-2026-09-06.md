# Auditoría fase H · catálogo de fuentes públicas

Fecha de corte: 6 de septiembre de 2026.

El análisis operativo de ISTAC y Dataestur, con series recomendadas, modelo de
observaciones, alcance P0/P1/P2 y uso con los modelos de IA, está en
[analisis-istac-dataestur-2026-09-06.md](analisis-istac-dataestur-2026-09-06.md).

## Implementación

Se ha creado `backend/app/external_sources.py` con un catálogo tipado de cinco fuentes públicas y series recomendadas para ISTAC/Dataestur:

- ISTAC: alojamiento turístico, mensual/anual.
- Dataestur / SEGITTUR: indicadores turísticos y conectividad.
- AEMET: observación, predicción y avisos; requiere API key.
- Aena: tráfico aeroportuario mensual.
- Eurostat: benchmark turístico europeo.

El endpoint conserva el contrato `external-sources.v1` y añade `recommended_datasets`
para que la siguiente fase pueda elegir una serie concreta sin codificarla en la
UI. En Dataestur se han registrado, entre otras, las series de precio por
antelación, rentabilidad por punto turístico y conectividad aérea.

El endpoint `GET /api/external/sources` devuelve `external-sources.v1` y sólo metadatos de integración. No realiza llamadas externas, no incorpora secretos y no presenta pasajeros, búsquedas o clima como ocupación hotelera.

## Decisiones de gobierno

Cada fuente declara granularidad, accesibilidad, usos de decisión y nota de licencia. Antes de activar un conector real habrá que registrar endpoint/dataset concreto, frecuencia efectiva, zona horaria, fecha de observación, versión/revisión, hash del payload y condiciones de redistribución.

La primera ingesta recomendada es ISTAC y Dataestur para benchmark mensual. AEMET y Aena deben entrar como contexto de destino con su propia granularidad. Las métricas externas no deben sumarse a las fotos de Booking ni cambiar el significado de ADR, pickup u ocupación.

## Validación

- 2 pruebas nuevas de catálogo y endpoint.
- 108 pruebas backend aprobadas.
- 8 pruebas JavaScript aprobadas.
- Sintaxis Python y JavaScript aprobada.

## Siguiente paso

Construir el registro persistente `external_sources` / `external_observations` y un conector de sólo lectura para un dataset ISTAC o Dataestur elegido por el equipo. El conector debe ser idempotente, conservar revisiones y bloquear alertas cuando falte fecha, unidad, cobertura o licencia.
