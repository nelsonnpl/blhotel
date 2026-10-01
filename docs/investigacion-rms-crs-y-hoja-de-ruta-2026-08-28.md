# Investigación de RMS y CRS y hoja de ruta para RIU Market Desk

Fecha de corte: 28 de agosto de 2026  
Alcance: producto, capacidades, modelo de entrega, arquitectura de integración y oportunidades de evolución.  
Método: revisión del repositorio y de la base SQLite local, contraste con documentación y páginas oficiales de proveedores. Las cifras de impacto publicadas por proveedores son afirmaciones comerciales, no resultados verificados de forma independiente.

## Resumen ejecutivo

RIU Market Desk tiene una base diferenciada de inteligencia de mercado: precios y producto hotelero observados, histórico de capturas, detalle de tarifas, conectividad aérea, trazabilidad, workspace y copiloto. No es todavía un RMS completo y no debe intentar convertirse ahora en un CRS.

La oportunidad más sólida es evolucionarlo primero hacia una **capa de decisión comercial conectada**:

1. Unificar señales externas con reservas, inventario, pickup y pace propios del PMS/CRS.
2. Convertir el análisis en una cola diaria de fechas y hoteles que requieren atención.
3. Producir recomendaciones explicables con confianza, límites y evidencia reproducible.
4. Añadir aprobación, override, auditoría y medición del resultado.
5. Publicar decisiones de forma controlada hacia el CRS, PMS o channel manager.
6. Sólo después, desarrollar forecast y optimización propios más sofisticados.

La tesis de producto es: **no competir de frente con un RMS empresarial ni reconstruir la distribución de un CRS; ocupar el espacio entre la inteligencia de destino, la decisión del revenue manager y la ejecución en los sistemas existentes**.

El activo más defendible no es un algoritmo genérico de “IA para subir precios”. Es la combinación de:

- inteligencia específica de Canarias y mercados emisores;
- comparabilidad hotelera y tarifaria auditable;
- señales aéreas y de destino alineadas por fecha de estancia;
- flujo de decisión de portfolio;
- integración bidireccional con sistemas hoteleros;
- explicaciones y control humano antes de automatizar.

## 1. Qué hacen realmente un RMS y un CRS

### RMS: de datos a decisiones y ejecución

Un RMS maduro cierra este circuito:

```text
PMS / CRS / booking engine / mercado
                ↓
reservas + inventario + demanda + competencia
                ↓
forecast de demanda no restringida y cancelaciones
                ↓
optimización de precio, mix, restricciones y overbooking
                ↓
recomendación → aprobación o automatización con límites
                ↓
publicación al CRS / PMS / sistema de distribución
                ↓
medición del resultado y recalibración
```

El núcleo no es el dashboard. Es la combinación de forecast, decisión granular, guardrails, publicación y aprendizaje.

IDeaS G3, por ejemplo, genera decisiones de precio junto con Last Room Value y controles de overbooking, y puede distribuir productos tarifarios al PMS, CRS o sistema de distribución. Su documentación exige reservas, inventario y bloques de grupo correctamente normalizados; la calidad de esos datos afecta directamente al forecast y a las decisiones ([IDeaS Pricing](https://developers.ideas.com/concepts/decisioncontrols/1pricing/), [IDeaS Inventory](https://developers.ideas.com/concepts/inbounddata/inventory/), [IDeaS Reservations](https://developers.ideas.com/concepts/inbounddata/1reservations/)).

### CRS: una fuente central de oferta y reserva

Un CRS moderno centraliza:

- ARI: disponibilidad, tarifas e inventario;
- habitaciones, rate plans, políticas, impuestos y contenido;
- restricciones como MLOS, CTA, CTD y cierres;
- reservas, modificaciones y cancelaciones;
- distribución a web propia, OTA, GDS, metabuscadores y call center;
- promociones, paquetes, códigos negociados y fidelización;
- cada vez más, ancillaries, experiencias y retailing sin habitación.

El CRS es una infraestructura transaccional y de distribución. Requiere consistencia, disponibilidad, seguridad, pagos, reconciliación, conectividad certificada y una semántica precisa. Oracle describe OPERA Cloud Distribution como sistema de registro de inventario, precio y contenido; sus APIs separan flujos de `Shop/Book` y de push ARI, y permiten reservar, modificar y cancelar con las reglas de distribución del hotel ([Oracle Distribution](https://docs.oracle.com/en/industries/hospitality/opera-cloud-distribution/24.1/ohdrn/ch_introduction.htm), [Oracle Distribution APIs](https://docs.oracle.com/en/industries/hospitality/integration-platform/ohipu/c_oracle_hospitality_distribution_apis.htm)).

### Diferencia práctica para el proyecto

| Capa | Pregunta que resuelve | Fuente de verdad natural | Papel recomendado de Market Desk |
| --- | --- | --- | --- |
| PMS | ¿Qué se ha reservado y qué ocurre en la propiedad? | Operación, reservas, folios e inventario físico | Consumir datos; no duplicar operación |
| CRS | ¿Qué se vende, dónde, con qué reglas y a qué precio? | ARI, oferta, contenido y reservas centrales | Integrar lectura y publicación controlada |
| RMS | ¿Qué conviene vender, restringir o aceptar? | Forecast, optimización y decisiones | Evolucionar gradualmente hacia esta capa |
| Market intelligence | ¿Qué ocurre fuera del hotel? | Competencia, demanda y contexto externo | Diferenciación actual y futura |
| Market Desk | ¿Qué requiere atención, por qué y qué se decidió? | Evidencia y workflow comercial | Convertirse en la mesa de decisión |

## 2. Mapa de RMS: qué ofrecen y cómo lo ofrecen

### IDeaS G3 RMS

**Propuesta:** optimización científica empresarial, especialmente fuerte en forecast, pricing granular, restricciones, overbooking, mix y grupos.

**Cómo lo ofrece:** plataforma cloud configurada e integrada con PMS/CRS; automatiza decisiones a nivel de tipo de habitación y rate code. Ofrece precios diarios, por longitud de estancia y continuos. El producto más reciente refuerza workflows de group pricing con roles, permisos y aprobaciones ([G3 RMS](https://ideas.com/wp-content/uploads/2020/06/IDeaS-G3-RMS-Brochure-EE.pdf), [Pricing](https://developers.ideas.com/concepts/decisioncontrols/1pricing/), [novedades febrero de 2026](https://ideas.com/improvements-innovations-whats-new-in-g3-rms-february-2026/)).

**Patrones explotables:**

- decisiones por fecha, habitación y producto, no un único ADR de mercado;
- controles además de precio: overbooking, disponibilidad y valor de la última habitación;
- forecast investigator y explicación de datos ausentes;
- ajuste de tarifas competitivas para comparar equivalentes reales;
- aprobación y permisos en decisiones con impacto comercial;
- cold start con hoteles comparables, pero revisión humana de las proyecciones.

**Qué no copiar ahora:** la profundidad algorítmica y de configuración de G3 requiere dos años de historia cuando están disponibles, datos propios bien normalizados y una integración certificada; construirla antes de disponer de esas entradas produciría una falsa apariencia de precisión ([guía de frecuencia de datos](https://developers.ideas.com/developer-guide/xdata-frequency-guidelines/)).

### Duetto: GameChanger, ScoreBoard, Advance y BlockBuster

**Propuesta:** un sistema operativo de revenue y beneficio con Open Pricing, automatización graduable, forecast/reporting, negocio de grupos y señales externas.

**Cómo lo ofrece:** suite SaaS modular. GameChanger ajusta por tipo de habitación, segmento, fecha y canal; el usuario puede operar manualmente o con AutoPilot. ScoreBoard centraliza forecast y reporting. Advance monitoriza anomalías y ejecuta dentro de guardrails, y expone el contexto de cada recomendación. BlockBuster añade displacement y colaboración de grupos ([GameChanger](https://www.duettocloud.com/en-us/platform/gamechanger), [ScoreBoard](https://www.duettocloud.com/en-us/platform/scoreboard), [Advance](https://www.duettocloud.com/en-us/platform/advance), [BlockBuster](https://www.duettocloud.com/hubfs/2023/Product/Product%20Sheets/duetto-blockbuster-product-sheet-en-june-2024.pdf)).

**Patrones explotables:**

- automatización graduable, por ámbito y con mínimos/máximos;
- Open Pricing: no mover en bloque todas las tarifas derivadas de BAR;
- anomalías primero, dashboard después;
- cada decisión con explicación, historial y guardrails;
- señales de mercado y eventos junto al dato propio, no en pantallas aisladas;
- forecast colaborativo y versionado, no Excel enviado por correo.

**Lectura estratégica:** Duetto ya incorpora competencia, demanda de mercado y eventos; por tanto, “tener vuelos y eventos” no basta como diferenciación. La ventaja debe estar en la calidad, granularidad regional, alineación temporal y capacidad de explicar qué señal cambió una decisión ([Duetto Advance y sus integraciones](https://www.duettocloud.com/en-us/press-releases/duetto-launches-advance-delivering-real-time-rate-optimization-and-first-to-market-data-integrations)).

### FLYR Hospitality

**Propuesta:** plataforma de decisión comercial AI-first con pricing, inventory optimization, BI y revenue planning.

**Cómo lo ofrece:** integración con el stack hotelero, forecast diario y por segmento, escenarios y versiones de forecast, automatización y recomendaciones de restricciones. Inventory Optimization evalúa precio, elasticidad, incertidumbre y múltiples estrategias para recomendar o aplicar restricciones ([Revenue Planning](https://flyr.com/resource-hub/new-flyr-hospitality-product-feature-revenue-planning/), [Inventory Optimization](https://flyr.com/resource-hub/new-flyr-hospitality-product-feature-inventory-optimization/)).

**Patrones explotables:**

- escenarios realista/optimista y comparación humano/modelo;
- forecast bloqueado frente a rolling forecast;
- versiones con autor, descripción y exactitud posterior;
- recomendaciones separadas de su aplicación automática;
- inventario y restricciones como parte de la optimización, no sólo pricing.

### Atomize

**Propuesta:** pricing en tiempo real con una experiencia más simple, autopilot y explicaciones generativas.

**Cómo lo ofrece:** RMS SaaS que permite revisar, modificar o aprobar recomendaciones y enviarlas al PMS; gran parte de sus clientes usa automatización completa. Incorpora pricing hasta dos años, forecast, restricciones, multi-property y explicación del “porqué” de una recomendación ([Atomize RMS](https://atomize.com/), [product sheet](https://help.atomize.com/hubfs/Atomize_Light_Product_Sheet_2024.pdf)).

**Patrones explotables:**

- empezar con una superficie de calendario y cambios urgentes;
- explicación literal y corta de cada recomendación;
- autopilot programable por fechas o contextos;
- jerarquías entre tipos de habitación sin perder pricing independiente;
- integración con datos futuros de búsqueda, vuelo, eventos y alojamiento alternativo ([Future Demand Insights](https://help.atomize.com/hubfs/Atomize_Product_Sheet_2024_USA.pdf)).

### RoomPriceGenie

**Propuesta:** RMS accesible para hoteles independientes, con automatización sencilla y acompañamiento.

**Cómo lo ofrece:** suscripción por propiedad en tres niveles —Core, Premium y Professional—, prueba de 14 días y onboarding incluido. Diferencia planes por horizonte, frecuencia de publicación, dashboards, forecast, segmentación, restricciones, displacement y revenue manager dedicado. Publica precios hasta 4 veces al día en Core y 24 en niveles superiores ([planes oficiales](https://roompricegenie.com/en_gb/pricing/)).

**Patrones explotables:**

- empaquetado por madurez y control, no sólo por número de gráficos;
- onboarding con estrategia de mínimos, máximos, estacionalidad y jerarquía;
- una edición básica automatiza precio; las avanzadas añaden forecast, segmentación, restricciones y servicio experto;
- el comprador entiende exactamente qué obtiene en cada nivel.

### BEONx

**Propuesta:** pasar de revenue de habitaciones a rentabilidad total, incorporando calidad del hotel y otras fuentes de ingreso.

**Cómo lo ofrece:** plataforma con forecast, automatización, reporting, Hotel Quality Index y Total Optimization Model. Combina rendimiento PMS, competencia y su índice de calidad, con actualizaciones varias veces al día ([plataforma BEONx](https://beonx.com/sustainable-profitability-platform/), [HQI](https://beonx.com/es/la-plataforma/)).

**Patrones explotables:**

- posicionamiento precio-calidad, no sólo gap frente a la mediana;
- optimización por beneficio y coste de distribución;
- total revenue de restauración, spa, eventos y otros ancillaries en etapas posteriores.

### Síntesis competitiva RMS

| Capacidad | IDeaS | Duetto | FLYR | Atomize | RoomPriceGenie | BEONx |
| --- | --- | --- | --- | --- | --- | --- |
| Forecast propio/segmentado | Muy fuerte | Fuerte | Fuerte y colaborativo | Incluido | Según plan | Incluido |
| Pricing granular | Habitación/rate code/LOS | Habitación/segmento/canal | Dinámico | Tiempo real | Automatizado y simple | Precio + calidad |
| Restricciones/inventario | Avanzado | Reglas y automatización | Optimización explícita | Incluidas | Avanzadas según plan | Incluidas |
| Overbooking | Sí | No es su mensaje principal | No es su mensaje principal | No es su mensaje principal | No es su mensaje principal | No es su mensaje principal |
| Grupos/displacement | Avanzado | BlockBuster | Parte de la plataforma | Group pricing | Plan Professional | No es el foco público |
| Señal externa | Competencia/demanda/STR | Demanda/eventos/STR | Datos integrados | Lighthouse Market Insight | Competencia/mercado | Competencia/HQI |
| Automatización | Alta y configurable | Manual a AutoPilot | Manual o automática | Autopilot | Por plan | Automatización |
| Explicabilidad/control | Investigator y overrides | Contexto y log | Transparencia del modelo | “Why” generativo | Control manual | Recomendaciones |
| Venta observada públicamente | Demo/implantación | Demo/suite modular | Demo/integración | Demo/SaaS | Planes + prueba | Demo/planes |

## 3. Mapa de CRS: qué ofrecen y cómo lo ofrecen

### Sabre SynXis

**Propuesta:** plataforma CRS empresarial para distribución consistente, reserva directa y retailing.

**Cómo lo ofrece:** CRS central conectado a OTA, GDS, booking engine y call center, con operación a nivel corporativo o de propiedad. La suite suma Booking Engine, Channel Connect, Metasearch, herramientas corporativas, voz y SynXis Retailing. Retailing permite vender experiencias, servicios y bienes con o sin reserva de habitación ([SynXis CRS y Retailing](https://investors.sabre.com/news-releases/news-release-details/kerzner-international-renews-long-standing-agreement-sabre), [evolución de Retailing](https://investors.sabre.com/news-releases/news-release-details/sabre-unveils-next-evolution-hospitality-retailing-synxis)).

**Patrones explotables:**

- una oferta es habitación + tarifa + política + add-ons, no sólo una cifra;
- disponibilidad liberada por una modificación debe reaparecer en tiempo real;
- paquetes dinámicos y personalización;
- override de restricciones con permisos y aprobación;
- fulfillment de ancillaries ligado a tareas operativas.

### Amadeus iHotelier CRS

**Propuesta:** una plataforma central para ARI, distribución y reserva directa, especialmente legible para independientes y cadenas medianas.

**Cómo lo ofrece:** dashboard único con edición rápida y masiva, control multi-property, OTA, GDS, metasearch, booking engine y call center. Añade promociones por geografía, duración, dispositivo o CRM y servicios opcionales como OTA Sync, GDS, VoicePro e integraciones PMS/RMS ([iHotelier CRS](https://www.amadeus-hospitality.com/solutions/reservations-and-booking-engine/ihotelier-crs/), [términos y módulos](https://www.amadeus-hospitality.com/legal/mssa/product/ihotelier/)).

**Patrones explotables:**

- quick edit y bulk edit para trabajo diario de portfolio;
- promoción con reglas, vigencia y audiencia;
- rendimiento de canal para reducir dependencia y coste de intermediación;
- arquitectura modular alrededor de un núcleo CRS.

### Oracle OPERA Cloud Central y Distribution

**Propuesta:** una plataforma unificada para propiedad y central: reservas, distribución, ventas, servicio, fidelización y configuración.

**Cómo lo ofrece:** single-image inventory, paridad entre propiedad y central, rate/restriction/inventory en un sistema, contacto central con vista por habitación o tarifa, upselling y perfiles. OHIP expone REST, streaming y business events para integraciones ([OPERA Cloud Central](https://www.oracle.com/hospitality/opera-central/), [datasheet](https://www.oracle.com/a/ocom/docs/industries/hospitality/hosp-opera-cloud-central-ds.pdf), [OHIP](https://docs.oracle.com/en/industries/hospitality/integration-platform/ohipu/c_preface.htm)).

**Patrones explotables:**

- consumir eventos en vez de hacer polling continuo;
- separar APIs de negocio de APIs compuestas para la interfaz;
- outbox, reintentos, idempotencia y replay de eventos;
- calendario de disponibilidad y ofertas con políticas/impuestos completos;
- permisos por tareas y auditoría centralizada.

Oracle recomienda business events para detectar cambios y un backend-for-frontend que componga sólo lo necesario para cada pantalla, en lugar de exponer APIs operativas completas al navegador ([guía OHIP](https://docs.oracle.com/en/industries/hospitality/integration-platform/ohipu/G24798_03.pdf)).

### D-EDGE CRS

**Propuesta:** núcleo de distribución modular y abierto, con especial encaje en independientes y grupos.

**Cómo lo ofrece:** CRS cloud con channel manager, booking engine, pagos, GDS, inventario central y central de reservas, disponibles juntos o por módulos. Publica conectividad con 130 PMS, 350 OTA, 17 RMS, todos los GDS, CRM y proveedores de pago mediante API abierta ([D-EDGE CRS](https://www.d-edge.com/product_family/central-reservation-system/)).

**Patrones explotables:**

- enfoque “adáptate al stack del hotel”, no sustitución forzada;
- módulos desplegables por madurez;
- conectividad como producto y catálogo visible;
- pagos y distribución delegados a especialistas.

### Cendyn CRS / RVNG

**Propuesta:** CRS conectado a GDS, OTA, booking engine y voz, integrado con el ecosistema de marketing/CRM de Cendyn.

**Cómo lo ofrece:** gestión central de tarifas, disponibilidad, reservas y contenido, con booking engine multi-property y call center. La documentación pública revisada muestra una evolución continua del booking engine, flujos móviles y configuración de portales ([visión de RVNG](https://help.cendyn.com/hc/en-us/articles/6079458460571-RVNG-the-reservation-platform), [release notes CRS](https://help.cendyn.com/hc/en-us/sections/7833055777563-Cendyn-CRS-Release-Notes)).

### Síntesis competitiva CRS

| Capacidad | SynXis | iHotelier | OPERA Cloud Central | D-EDGE | Cendyn |
| --- | --- | --- | --- | --- | --- |
| ARI central y multi-property | Sí | Sí | Sí, unido a operación | Sí | Sí |
| OTA/GDS/direct/call center | Sí | Sí | Sí | Sí | Sí |
| Booking engine | SynXis BE | iHotelier BE | Web booking/distribution | Integrado | RT4 |
| Retailing/ancillaries | Muy fuerte | Add-ons/promociones | Paquetes, upsell, loyalty | Módulos CRS | Ligado a marketing/CRM |
| PMS/operación propia | Property Hub | Integraciones | OPERA Cloud PMS | Conectores | Integraciones |
| APIs/eventos | APIs SynXis | Integraciones contratadas | OHIP REST + streaming | API abierta | Integraciones |
| Encaje principal | Empresa/cadena | Independiente y mid-market | Empresa con ecosistema Oracle | Independiente a cadena | Hotel/grupo con suite Cendyn |

## 4. Estado real de RIU Market Desk

### Activos actuales

La revisión local encuentra:

- Flask + Jinja + JavaScript/CSS estático;
- SQLite como almacén operativo;
- captura hotelera de Booking y detalle de tarifas;
- capturas aéreas y rutas;
- jobs en background;
- dashboard, hoteles, vuelos, revenue, workspace, capturas y copiloto;
- APIs de histórico, price history, rate details, heatmap, oportunidades y estabilidad;
- trabajo previo de accesibilidad, paginación y reducción de payload.

Estado de los datos locales en la fecha de la revisión:

| Entidad | Registros |
| --- | ---: |
| Mercados configurados | 2 |
| Capturas hoteleras | 24 |
| Filas hotel-captura | 923 |
| Tarifas detalladas | 8.335 |
| Fichas estables en `hotel_inventory` | 0 |
| Capturas aéreas | 12 |
| Rutas aéreas | 157 |
| Opciones aéreas | 538 |
| Workspaces | 1 |

Esto es suficiente para validar producto y flujos, pero no para entrenar ni evaluar un RMS autónomo.

### Matriz de madurez

| Capacidad | Estado | Lectura |
| --- | --- | --- |
| Rate shopping competitivo | Operativo | Es la base más madura |
| Producto y condiciones OTA | Parcial | Hay mucho detalle, falta normalización comparable |
| Histórico competitivo | Operativo | Útil para movimientos y estabilidad |
| Señal aérea | Operativa, experimental | Diferenciadora si se alinea por estancia y mercado |
| Calidad/trazabilidad | Parcial | Falta completar estado de captura y universo estable |
| Reservas propias | Ausente | Bloquea pickup, pace, forecast y elasticidad reales |
| Inventario propio | Ausente | Bloquea presión de inventario y controles fiables |
| Segmentos/canales/coste | Ausente | Bloquea mix y beneficio neto |
| Pickup propio | Ausente | La función actual mide cambio de tarifa competitiva |
| Forecast | Ausente | La “demand curve” es curva de precios observados |
| Recomendación | Heurística | Debe presentarse como señal, no decisión automática |
| Aprobación/override | Ausente | No existe workflow de decisión operativo |
| Publicación a CRS/PMS | Ausente | El ciclo no se cierra |
| Backtest/impacto | Ausente | No puede medirse calidad o uplift de recomendaciones |

### Correcciones semánticas P0

1. **Renombrar `pickup_analysis`.** El código compara el precio del mismo hotel y check-in entre snapshots. Eso es `variación de tarifa competitiva`, no pickup. Pickup significa nuevas reservas o habitaciones netas ganadas entre dos fechas de observación.
2. **Renombrar `demand_curve`.** Agrupa precios OTA por días hasta llegada. Es una `curva de precio competitivo por antelación`, no una curva de demanda.
3. **Bajar el nivel de certeza de `revenue_opportunities`.** Sin reservas ni inventario propios, deben ser alertas de mercado o hipótesis a validar.
4. **Eliminar la inferencia “vuelo caro = viajero comprometido = mantener premium”.** El precio aéreo alto también puede reducir conversión o reflejar poca capacidad; no demuestra willingness-to-pay del huésped del hotel.
5. **No interpretar `capturedRows / availableResults` como compresión.** Puede reflejar límites, paginación, calidad o bloqueo del proveedor. Sólo un universo estable con estados explícitos permite aproximar sold-out.
6. **No usar rating OTA como justificación automática de subida.** Puede apoyar posicionamiento precio-calidad, pero necesita producto comparable, reputación normalizada y elasticidad propia.

Estas correcciones no reducen el valor del producto; aumentan confianza y preparan la base para conectarlo a decisiones reales.

## 5. Qué podemos explotar

### 5.1 Cola diaria de oportunidades por fecha

La superficie principal de un revenue manager no debería ser un mosaico de KPIs, sino una tabla priorizada de `hotel × fecha de estancia`:

| Campo | Función |
| --- | --- |
| Fecha / hotel | Unidad de decisión |
| OTB, pickup y pace | Situación propia |
| Forecast y capacidad restante | Demanda e inventario esperados |
| BAR y restricciones actuales | Estado comercial ejecutable |
| Posición comp-set comparable | Contexto competitivo |
| Señales aéreas/eventos/destino | Contexto externo |
| Recomendación y rango | Acción propuesta |
| Confianza y riesgos | Grado de evidencia |
| Motivos principales | Explicación |
| Estado | Nueva, revisada, aprobada, publicada, fallida |
| Resultado | Efecto observado posterior |

Filtros clave: excepción, hotel, cluster, horizonte, segmento, canal, severidad, confianza y estado. Las acciones en lote deben existir sólo para recomendaciones homogéneas y reversibles.

### 5.2 Evidence stack explicable

Cada recomendación debe mostrar una pila corta y verificable:

```text
Pickup propio +8 habitaciones desde ayer
Pace 12% por encima del patrón comparable
Inventario vendible restante: 14
Comp-set comparable: +6% desde la última observación
Capacidad aérea desde DE: +9% para la semana
Datos: completos y actualizados
→ Probar BAR +4%, dentro del límite configurado ±5%
```

Los valores anteriores son sólo un ejemplo de formato, no datos ni umbrales propuestos para producción. Los límites reales deben definirse con Revenue.

### 5.3 Inteligencia de destino especializada

El proyecto puede construir una capa difícil de replicar por un RMS genérico:

- origen → destino → fecha de viaje → fecha de estancia;
- búsquedas y reservas aéreas de Dataestur;
- capacidad programada y conectividad;
- eventos, festivos y vacaciones escolares de mercados emisores;
- meteorología en destino y origen;
- oferta alojativa alternativa y contexto ISTAC;
- mercado hotelero competitivo comparable.

La clave es guardar qué información era conocida en el momento de cada decisión. Sin `observed_at`, `published_at`, `retrieved_at` y versión de transformación se introduce look-ahead bias en cualquier backtest.

### 5.4 Comparabilidad como producto

La competencia no debe compararse sólo por precio. Construir un `Comparable Offer Key`:

```text
property / room class / occupancy / board / cancellation / payment
/ taxes / channel / member-or-public / third-party inventory
```

Después calcular:

- cobertura comparable;
- ajustes explícitos por desayuno, impuestos o flexibilidad;
- confianza de matching;
- hoteles y canales excluidos con motivo;
- cambios de composición del comp-set.

IDeaS ya permite ignorar canales competitivos inconsistentes y ajustar diferencias de producto/tasas; esto confirma que la comparabilidad es parte central de la decisión, no una tarea de limpieza secundaria ([novedades G3 agosto de 2025](https://ideas.com/improvements-innovations-whats-new-in-g3-rms-august-2025/)).

### 5.5 Workflow de decisión y aprendizaje

Añadir entidades operativas:

- `recommendation`;
- `recommendation_evidence`;
- `decision`;
- `approval`;
- `override_reason`;
- `publication_attempt`;
- `outcome_measurement`;
- `strategy_guardrail`.

Cada acción debe conservar modelo/regla, versión, inputs, usuario, hora, valores anterior/propuesto/aplicado, destino de publicación y respuesta del sistema externo.

Esto permite responder:

- ¿qué recomendó el sistema?
- ¿por qué?
- ¿quién lo cambió y por qué?
- ¿se publicó correctamente?
- ¿qué ocurrió después?
- ¿en qué contextos falla el enfoque?

### 5.6 Control antes que autonomía

Secuencia recomendable:

1. observación;
2. recomendación sin acción;
3. aprobación individual;
4. aprobación masiva bajo filtros;
5. automatización sólo en fechas/mercados seguros;
6. excepciones y kill switch;
7. ampliación gradual del ámbito.

El producto debe soportar `manual`, `suggest`, `approve-and-publish` y `autopilot` por hotel, horizonte, día, tipo de habitación o regla.

### 5.7 Rentabilidad de canal y total revenue

Una vez conectado el CRS/PMS, priorizar:

- ADR neto de comisión y coste de adquisición;
- contribución por canal/segmento;
- coste de servicio;
- cancelación/no-show;
- total spend por estancia;
- ancillaries y paquetes;
- desplazamiento de grupo y transitorio.

No hace falta construir un booking engine para analizar si conviene un descuento directo, una promoción de mercado emisor o mantener disponibilidad en OTA.

## 6. Qué construir, qué integrar y qué no construir

### Construir como diferenciación

- modelo canónico de señales externas y comerciales;
- comparabilidad de producto hotelero;
- inteligencia Canarias/mercados emisores;
- cola de oportunidades de portfolio;
- evidence stack, confianza y calidad;
- reglas/guardrails de estrategia;
- workflow de decisión, aprobación y auditoría;
- backtesting y medición de decisiones;
- copiloto que consulta evidencia y prepara decisiones.

### Integrar o comprar

- conectividad PMS/CRS certificada;
- GDS, channel manager y booking engine;
- pagos y PCI;
- rate shopping licenciado a escala, si el scraping deja de ser viable;
- STR/Demand360 u otros benchmarks si el caso económico lo justifica;
- eventos comerciales de alta cobertura si la fuente pública no basta;
- motor RMS externo durante la fase de aprendizaje, si se necesita optimización antes de tener ciencia propia.

### No construir ahora

- un CRS nuevo;
- un channel manager;
- un booking engine;
- distribución GDS;
- procesamiento de pagos;
- loyalty/CRM completo;
- forecast ML autónomo sin datos propios suficientes;
- “IA” que inventa causalidad o decide BAR desde datos externos aislados.

## 7. Arquitectura objetivo

```text
PMS / CRS / Channel Manager         Fuentes externas
reservas, inventario, ARI           hoteles, vuelos, eventos, destino
            │                                  │
            └────────── conectores ────────────┘
                               │
                    raw events inmutables
                               │
                    modelo canónico hotelero
                               │
           métricas OTB / pickup / pace / calidad / features
                               │
           reglas + forecast + optimización + confidence policy
                               │
                 cola de recomendaciones y aprobaciones
                               │
                       transactional outbox
                               │
                 adaptador CRS/PMS + reconciliación
                               │
                        outcome measurement
```

### Modelo canónico mínimo

**Dimensiones**

- `property`, `cluster`, `room_type`, `room_class`;
- `rate_plan`, `board`, `policy`, `offer`;
- `market_segment`, `source_market`, `channel`;
- `stay_date`, `booking_date`, `observation_time`;
- `currency`, `tax_mode`, `cost_model`.

**Hechos propios**

- reservation lifecycle;
- inventory/capacity/out-of-order;
- rooms and revenue on books;
- cancellations/no-shows;
- groups and blocks;
- current ARI and restrictions;
- web search, regrets/denials and conversion, si están disponibles.

**Hechos externos**

- competitive offer observation;
- air search/booking/capacity/price;
- event/holiday/weather;
- destination demand/occupancy benchmarks.

**Decisión**

- forecast version;
- recommendation/evidence/confidence;
- approval/override;
- publication/reconciliation;
- outcome.

### Integración

- Empezar por lectura: importación CSV/SFTP o API read-only.
- Preferir eventos y webhooks/streaming a polling cuando existan.
- Mantener raw payload cifrado o minimizado, con retención explícita.
- Excluir PII del dataset de revenue salvo necesidad demostrada. IDeaS tampoco requiere PII para sus mensajes de reserva.
- Usar claves idempotentes, checkpoints y replay.
- Publicar mediante outbox; no llamar al CRS desde el request de la interfaz.
- Reconciliar valor deseado, valor enviado y valor confirmado.
- Añadir circuit breaker y kill switch por hotel.

Si el stack de RIU usa OPERA Cloud, OHIP ofrece reservas, inventario, rate plans, datos analíticos y business events, pero el acceso y algunos planes de datos son comerciales. Debe confirmarse el sistema real antes de elegir el primer conector ([OHIP Data APIs](https://docs.oracle.com/en/industries/hospitality/integration-platform/ohipu/c_calling_the_oracle_hospitality_data_apis.htm), [prerrequisitos y licencias](https://docs.oracle.com/en/industries/hospitality/integration-platform/ohipu/r_prerequisites_oracle_hospitality_data_apis.htm)).

## 8. Hoja de ruta priorizada

### Fase A — Verdad semántica y calidad

**Objetivo:** que ninguna pantalla confunda observación con demanda o recomendación con decisión.

- renombrar pickup y demand curve actuales;
- clasificar outputs como `observación`, `señal`, `hipótesis` o `recomendación`;
- eliminar causalidades no demostradas;
- persistir captura completa/parcial, universo esperado, páginas, errores y cobertura;
- normalizar offer key y matching competitivo;
- poblar y validar `hotel_inventory`;
- mostrar fuente, vigencia y confianza en la misma fila que la señal.

**Gate:** Revenue acepta el glosario y una muestra de 20 lecturas puede reproducirse desde sus datos fuente.

### Fase B — Read-side PMS/CRS

**Objetivo:** obtener situación propia sin riesgo de escritura.

- confirmar PMS, CRS, channel manager y RMS existentes;
- importar reservas, inventario, ARI, segmentos, canales y bloques;
- reconstruir OTB por stay date y snapshot de observación;
- calcular pickup neto y pace real;
- separar booked room type de occupied room type;
- alinear monedas, impuestos, timezone y business date;
- monitorizar lag, cobertura y reconciliación.

**Gate:** OTB, pickup, cancelaciones e inventario cuadran contra el sistema fuente en una muestra acordada.

### Fase C — Decision cockpit

**Objetivo:** convertir datos en un flujo diario útil sin publicar cambios.

- tabla `hotel × stay date` priorizada por excepción;
- evidence stack y detalle lateral;
- recomendación de rango, no cifra falsa de precisión;
- guardrails por estrategia;
- aprobar/rechazar/editar con motivo;
- asignar, comentar y cerrar;
- sesiones de portfolio con filtros persistentes;
- copiloto limitado a datos y operaciones permitidas.

**Gate:** el equipo completa un ciclo de revisión real y puede auditar cada decisión.

### Fase D — Backtest y shadow mode

**Objetivo:** medir antes de automatizar.

- replay temporal sin usar datos futuros;
- baseline frente a “mantener tarifa” y decisiones humanas;
- forecast accuracy por horizonte/segmento;
- aceptación, override y motivos;
- simulación de límites y frecuencia;
- shadow recommendations durante operación real;
- evaluación por cohortes y periodos comparables.

**Gate:** el sistema demuestra estabilidad, calibración de confianza y ausencia de riesgos operativos materiales.

### Fase E — Publicación controlada

**Objetivo:** cerrar el ciclo con bajo riesgo.

- primer adaptador de escritura para BAR base;
- outbox, idempotencia, retry, timeout y reconciliación;
- aprobación individual y bulk limitada;
- permisos, doble aprobación donde proceda y kill switch;
- historial anterior/propuesto/aplicado;
- alertas de fallo o divergencia;
- rollback mediante una nueva publicación compensatoria, no borrando historia.

**Gate:** publicación y reconciliación son fiables en un piloto acotado.

### Fase F — Forecast, restricciones y automatización

**Objetivo:** avanzar de decision support a RMS propio donde exista ventaja.

- forecast unconstrained por segmento y room class;
- cancelación/no-show;
- elasticidad y escenarios;
- room-type pricing;
- MLOS/CTA/CTD y last-room controls;
- displacement de grupo;
- optimización por contribución y coste de canal;
- autopilot sólo en dominios validados.

**Gate:** cada nueva familia de decisiones supera backtest, shadow mode y control operativo antes de automatizarse.

## 9. Próximo incremento recomendado

El siguiente incremento coherente no es “añadir más dashboards”. Es un **Revenue Decision Ledger** en modo read-only:

1. Corregir nombres y niveles de certeza actuales.
2. Añadir esquema de recomendación/evidencia/decisión sin escritura externa.
3. Crear importador canónico CSV de reservas e inventario para validar el modelo antes del conector.
4. Implementar OTB, pickup y pace reales por stay date.
5. Crear una tabla compacta de oportunidades con datos propios + competencia + señal aérea.
6. Añadir aprobación/rechazo/override y auditoría.
7. Construir replay temporal y backtest de reglas.
8. Elegir el primer conector sólo después de confirmar el stack real de RIU.

Este incremento aprovecha el trabajo existente, no exige cambiar Flask/Jinja/SQLite y crea la base que cualquier integración RMS/CRS necesitará. SQLite sigue siendo válido para el piloto local; la migración a una base multiusuario debe decidirse por concurrencia, volumen, disponibilidad y gobierno, no por moda tecnológica.

## 10. Métricas de producto y control

### Calidad de datos

- cobertura y frescura por fuente;
- reservas/inventario reconciliados;
- ofertas comparables frente al total;
- eventos retrasados, duplicados o descartados;
- porcentaje de decisiones reproducibles.

### Calidad analítica

- bias y error de forecast por horizonte;
- calibración de confianza;
- precisión de alertas/anomalías;
- estabilidad frente a datos faltantes;
- sensibilidad a cambios de comp-set.

### Flujo de trabajo

- fechas revisadas y cerradas;
- tiempo desde alerta hasta decisión;
- aceptación, edición y rechazo;
- motivos de override;
- uso de acciones en lote;
- trabajo manual eliminado, medido y no estimado.

### Ejecución

- publicaciones correctas/fallidas;
- latencia hasta confirmación;
- divergencias entre deseado y CRS;
- rollbacks/compensaciones;
- automatizaciones pausadas por guardrails.

### Resultado comercial

- ADR, ocupación, RevPAR y contribución neta;
- mix por canal/segmento;
- cancelación y no-show;
- forecast accuracy;
- uplift validado mediante experimentos o diseños cuasi-experimentales, no simple antes/después.

## 11. Riesgos que deben gobernarse

- **Legal/licencia:** scraping, almacenamiento de datos OTA, reputación y fuentes externas.
- **Privacidad:** minimizar PII y separar analítica comercial de perfiles de huésped.
- **Causalidad:** una correlación aérea o competitiva no demuestra demanda propia.
- **Look-ahead bias:** nunca usar en backtest un dato publicado después de la decisión.
- **Automatización:** límites, permisos, kill switch, auditoría y reconciliación obligatorios.
- **Comparabilidad:** precio sin impuestos, política, régimen y ocupación equivalentes induce errores.
- **Disponibilidad:** ausencia en resultados OTA no equivale a sold-out.
- **Multi-property:** jerarquías de estrategia sin borrar autonomía local.
- **Vendor lock-in:** mantener modelo canónico y adaptadores separados.
- **Explicabilidad cosmética:** una explicación generada no sustituye evidencia calculada y reproducible.

## 12. Decisiones de dirección propuestas

1. Posicionar Market Desk como **Revenue Decision Intelligence for Resort Portfolios**, no como CRS.
2. Elegir entre dos rutas para RMS:
   - capa complementaria que integra un RMS existente; o
   - RMS propio gradual, empezando por recomendaciones y shadow mode.
3. Adoptar como unidad central `hotel × stay date × room class × segment/channel`.
4. Hacer de calidad, comparabilidad y decisión auditable capacidades visibles del producto.
5. Integrar PMS/CRS en lectura antes de añadir más fuentes externas.
6. No habilitar write-back hasta disponer de aprobación, outbox, reconciliación y kill switch.
7. Medir algoritmos contra decisiones humanas y baselines, no contra métricas retrospectivas aisladas.
8. Mantener la UI densa y operativa: tablas, filtros, excepciones, detalle lateral y acciones inline; evitar nuevas parrillas de cards.

## Fuentes primarias principales

- [IDeaS G3 RMS](https://ideas.com/wp-content/uploads/2020/06/IDeaS-G3-RMS-Brochure-EE.pdf)
- [IDeaS Developer: Reservations](https://developers.ideas.com/concepts/inbounddata/1reservations/)
- [IDeaS Developer: Inventory](https://developers.ideas.com/concepts/inbounddata/inventory/)
- [IDeaS Developer: Pricing](https://developers.ideas.com/concepts/decisioncontrols/1pricing/)
- [Duetto GameChanger](https://www.duettocloud.com/en-us/platform/gamechanger)
- [Duetto ScoreBoard](https://www.duettocloud.com/en-us/platform/scoreboard)
- [Duetto Advance](https://www.duettocloud.com/en-us/platform/advance)
- [FLYR Revenue Planning](https://flyr.com/resource-hub/new-flyr-hospitality-product-feature-revenue-planning/)
- [FLYR Inventory Optimization](https://flyr.com/resource-hub/new-flyr-hospitality-product-feature-inventory-optimization/)
- [Atomize RMS](https://atomize.com/)
- [RoomPriceGenie Pricing](https://roompricegenie.com/en_gb/pricing/)
- [BEONx Platform](https://beonx.com/sustainable-profitability-platform/)
- [Sabre SynXis CRS y Retailing](https://investors.sabre.com/news-releases/news-release-details/kerzner-international-renews-long-standing-agreement-sabre)
- [Amadeus iHotelier CRS](https://www.amadeus-hospitality.com/solutions/reservations-and-booking-engine/ihotelier-crs/)
- [Oracle OPERA Cloud Central](https://www.oracle.com/hospitality/opera-central/)
- [Oracle Hospitality Distribution APIs](https://docs.oracle.com/en/industries/hospitality/integration-platform/ohipu/c_oracle_hospitality_distribution_apis.htm)
- [D-EDGE CRS](https://www.d-edge.com/product_family/central-reservation-system/)

