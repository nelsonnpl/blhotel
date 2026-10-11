# Atlas UI: recursos y decisiones

Se conserva Flask/Jinja/JavaScript, Atlas azul, Archivo/Space Mono, los dos temas y las tres densidades. No se incorporan dependencias ni solicitudes nuevas. Las APIs, los cálculos, las rutas y las claves de preferencias permanecen iguales.

## Referencias examinadas

| Recurso | Patrones adaptados | Aplicación |
| --- | --- | --- |
| [Arc UI](https://uiarc.dev/components/filter-toolbar) | Jerarquía entre vistas, facetas, búsqueda y selección; paneles y controles compactos | Barra de Hoteles en dos niveles, filtros BI, controles comunes |
| [Beautiful UI](https://www.beautifului.dev) | Registros con identidad legible, conversación, contexto, fuentes y acciones de historial | Reputación, Copilot, catálogo Workspace y seguimiento de Capturas |
| [Space UI](https://www.spaceui.one/primitives/dialog) | Formularios agrupados y diálogos con contenido desplazable, cierre por Escape y devolución del foco | Capturas, diálogo y foco de controles |

Son referencias de interacción y composición. La implementación modifica los componentes propios; no copia fragmentos de estas bibliotecas. No se incluyen sus demostraciones, datos ficticios, iconos comerciales, componentes Pro ni paquetes React, Tailwind o Motion.

## Licencias

Las fuentes gratuitas consultadas publican licencia MIT: [Beautiful UI](https://www.beautifului.dev/license), [Arc UI](https://github.com/kuratlielia/arc-library/blob/main/LICENSE), [Space UI](https://www.spaceui.one/terms). Al no redistribuir código de esas fuentes, no se añade un aviso de copyright ajeno al código propio. Si se incorporan fragmentos posteriormente, deben conservarse sus avisos originales. Los iconos y fuentes locales existentes se mantienen con sus licencias.

## Implementación

- Tokens de radios y duración junto a las bases de tema; radios de superficies de hasta 8 px y transiciones de controles entre 140 y 180 ms.
- Cifras, barras y filas se muestran completas, sin conteo ni entrada escalonada. Los indicadores de actividad siguen vinculados a estados reales y se respeta movimiento reducido.
- Cabeceras compactas, señales sin tarjetas anidadas, filtros y resumen BI más cortos; se conservan variantes, columnas, exportación y detalles.
- Reputación asigna más ancho a identidad y permite nombres en varias líneas; fechas completas y casillas de 24 px. Vuelos mantiene mapas y todas sus pestañas.
- Copilot permite envolver los controles de contexto, ampliar el texto del historial, consultar sus acciones y mantener fuentes, adjuntos, modelos y trazabilidad.
- Workspace reduce el catálogo lateral y elimina tarjetas dentro del resumen; Capturas agrupa campos y limita la consola a su propia zona desplazable.

## Comprobación reproducible

El backup previo y la evidencia local quedan fuera de Git. Véase `atlas-validation.md` para resultados y límites. Las pruebas e2e interceptan operaciones de pago o escritura. Se corrigió el mock para que GET de conversaciones lea el historial real: antes devolvía por error la respuesta simulada de creación de sesión.
