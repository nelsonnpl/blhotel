# Fase A — Corrección de comparaciones y lectura del dato

Fecha: 5 de septiembre de 2026. Aplicación: Atlas / RIU Market Desk.

Esta entrega implementa las primeras correcciones del trabajo por fases. No cierra la auditoría completa ni convierte las tarifas públicas en métricas de reservas. Las pruebas y la revisión visual se realizaron con bases temporales; no se ejecutaron capturas ni llamadas a modelos de pago.

## Correcciones implementadas

| Problema comprobado | Comportamiento actual |
| --- | --- |
| Se comparaba la media de toda la foto actual con la de los productos emparejados de la anterior. Un hotel nuevo caro podía producir una subida ficticia. | Las dos medias de variación usan exactamente los mismos productos emparejados. Se exponen ambas medias y cobertura. |
| Dos productos con campos desconocidos podían considerarse equivalentes. | La firma exige hotel, entrada, salida, noches coherentes, ocupación, habitación, régimen, moneda y cancelación conocidos, con tarifa positiva. `false` de cancelación sigue siendo un dato conocido válido. |
| Los productos duplicados se resolvían escogiendo una fila. | Se excluyen las identidades ambiguas en la comparación y el movimiento entre fotos. |
| Una consulta sobre una foto histórica podía encontrar otra posterior. | Solo se buscan antecedentes anteriores al ancla; se conserva el umbral de cobertura del 70 %. |
| La estabilidad mezclaba diferentes estancias o habitaciones del hotel. | Se calcula exclusivamente sobre observaciones del producto actual equivalente, indicando número de observaciones y fotos. Sin dos observaciones se omite. |
| El mapa usaba seis fotos, mientras que la tabla mostraba una. | El dashboard construye los puntos a partir de las filas de la foto que muestra. Se elimina esa petición adicional del dashboard. El endpoint de mapa también usa una foto por defecto y declara alcance e identificadores. |
| El inspector agrupaba observaciones por ventanas inferidas de veinte minutos. | Presenta tarifas de fotos reales del mismo producto, con fecha e identificador, en una tabla de evidencia. Ya no infiere lotes ni promedia productos distintos. |
| La columna «vs. mediana» calculaba distancia a la media. | Utiliza un campo específico calculado respecto de la mediana. |
| «Vigencia» mostraba «Comparable», incluso en fotos antiguas. | Antigüedad y existencia de base comparable se muestran por separado. Dashboard e IA comparten la regla de vigencia. |
| La baja cobertura se describía como pico de demanda y las ausencias como posible sold-out. | Se describen como límites de extracción o ausencia en resultados. No prueban ocupación o agotamiento. También se retiran inferencias de disposición a pagar basadas únicamente en precios aéreos. |
| El gráfico del espacio de trabajo usaba precio total de estancia como tarifa por noche e inventaba una línea plana si faltaban puntos. | Usa la media por noche en EUR; con menos de dos fotos muestra un estado vacío. Advierte que la composición de las fotos puede cambiar. |
| El horizonte hasta la entrada truncaba días a partir de la hora de captura. | Usa diferencia entre fechas de calendario. La curva agrupa y muestra cada moneda por separado. Es un agregado histórico, no un forecast. |
| El historial entregado a la IA perdía fechas de estancia y condiciones; podía escoger el primer hotel coincidente. | Conserva dimensiones, moneda, IDs y fechas; acota la consulta a la zona resuelta. Devuelve candidatos cuando el nombre es ambiguo y acepta una zona para desambiguar. |

Se añaden los alias `/api/analytics/rate-movement` y `/api/analytics/observed-rate-curve`. Las rutas y los campos antiguos se conservan por compatibilidad; los nombres internos `pickup` y `demand-curve` no pasan a representar reservas o demanda real.

## Validación

- Backend: 86 pruebas aprobadas, incluidas 22 pruebas nuevas en `backend/tests/test_revenue_semantics.py`.
- JavaScript: 8 pruebas aprobadas en `tests/revenue-semantics.test.cjs`, con el ejecutor incorporado de Node y sin dependencias nuevas.
- Sintaxis de `atlas.js`: `node --check` aprobado.
- Interfaz ejecutada con copia temporal de SQLite. Dashboard e inspector a 1440 × 900; hoteles a 1920 × 1080, 1366 × 768, 993 × 900 y detalle a 1440 × 900. Imágenes inspeccionadas directamente en `artifacts/visual-qa/phase-a-20260905/`.
- Comprobados: navegación, restauración de filtros, orden ascendente, expansión de fila con Enter, apertura/ampliación del inspector y cierre con Escape que devuelve el foco al botón de origen.
- En el ejemplo real de Seaside Palm Beach, las fotos #6 y #18 tienen la misma estancia 6–13 de octubre, 2 personas y tarifa de 667 EUR/noche: variación 0 %. El mapa actual contiene 38 puntos de la misma foto, frente a la mezcla anterior de 46 puntos.
- Sin errores o avisos en el registro del navegador consultado durante la revisión de dashboard e inspector. No es una certificación general de accesibilidad ni una prueba de carga.

## Límites y trabajo pendiente para las fases siguientes

1. **Divisas:** curva, comparador local y serie del workspace ya evitan sumar monedas. Otras métricas agregadas del dashboard, fotos históricas y mapa solicitado con varias fotos todavía necesitan una política uniforme de moneda. Los datos reales auditados estaban en EUR. No se debe interpretar esta entrega como soporte multidivisa completo ni como conversión de moneda.
2. **Equivalencia limitada al dato disponible:** no se verifican uniformemente impuestos, elegibilidad Genius/móvil/residente, composición adultos/niños, número de habitaciones ni plazos de pago. La firma nueva es conservadora con los campos actuales, pero no acredita paridad tarifaria completa.
3. **Capturas:** falta hacer explícito el perfil de búsqueda acordado, persistir sus parámetros y vincular mejor las extracciones de detalle con la foto y el producto. La revisión observó un detalle tarifario con fecha anterior a la foto principal; debe conservar y mostrar su procedencia por separado.
4. **UX:** `Restablecer` elimina el filtro pero conserva texto en el campo de búsqueda. Los paneles superiores de hoteles siguen desplazando la tabla por debajo del primer pantallazo en pantallas estrechas. Son hallazgos pendientes de la fase de interfaz, no correcciones de esta entrega.
5. **Terminología:** aún quedan etiquetas históricas «ADR» para tarifa pública y nombres heredados en contratos. Hace falta una revisión transversal sin romper consumidores.
6. **IA:** esta fase corrige evidencia y desambiguación de un historial. Quedan evaluación numérica de respuestas, conversaciones, enrutamiento, trazas, límites de contexto y propuestas de acciones con confirmación.
7. **Limpieza y rendimiento:** no se han eliminado aún `app.js`/`app.css` antiguos ni scripts heredados. Se revisarán consumidores antes de retirarlos. No se afirma una mejora de latencia sin medición.
8. **Sector y fuentes:** las integraciones y comparativas de herramientas se desarrollan en sus fases específicas. No se han comprado servicios ni activado proveedores.

## Reversibilidad

El directorio no contiene metadatos Git. Los originales de los cinco archivos existentes editados se guardaron en `backups/phase-a-20260905/`, con manifiesto SHA256. Se añadieron un módulo de reglas semánticas, dos archivos de pruebas, este informe y las capturas de QA. No hay cambios de esquema de base de datos en esta fase.

## Siguiente fase

Consolidar el contrato de las fotos y perfiles de captura manual: parámetros explícitos de estancia y ocupación, procedencia y comparabilidad, vínculo con detalle tarifario, control de moneda y validación sobre copia antes de cualquier migración. Mantener Flask, SQLite y la interfaz actual. La automatización diaria y GCP quedan fuera del alcance inmediato acordado.
