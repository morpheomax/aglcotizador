# DECISIONS — Registro de decisiones técnicas

## ADR-001 — Streamlit como MVP

Decisión: construir el MVP en Python + Streamlit.

Motivo:

- Permite validar cálculos rápido.
- Lee Excel fácilmente.
- Exporta BOM a Excel sin fricción.
- Reduce tiempo inicial frente a una web app completa.

Consecuencia:

- UX suficiente para uso interno.
- Migración futura a Astro/React será viable si el motor queda desacoplado.

## ADR-002 — Separar motor de cálculo de UI

Decisión: `app.py` no contendrá fórmulas técnicas.

Motivo:

- Facilita testing.
- Facilita migración futura.
- Reduce errores por cambios de interfaz.

## ADR-003 — Catálogos externos

Decisión: códigos, precios, cilindros, flooding factors y reglas BOM vivirán fuera del código.

Motivo:

- Los códigos y precios cambian.
- Comercial puede mantener archivos sin tocar código.
- El motor debe ser estable.

## ADR-004 — Manifold con cilindros iguales

Decisión: para manifold, el selector solo permitirá cilindros iguales con mismo llenado.

Motivo:

- Regla técnica crítica de configuración.
- Evita BOM inválido aunque sea más barato.

## ADR-005 — Sistema como pre-dimensionador comercial

Decisión: el sistema no declarará cumplimiento final de diseño hidráulico.

Motivo:

- Los manuales indican sistemas engineered y requieren diseño/cálculo específico.
- La herramienta sirve para cotizar, no para reemplazar software certificado o revisión de ingeniería.

## ADR-006 — Archivo de continuidad para OpenCode

Decisión: mantener `PROJECT_GRAPH.md` como memoria operativa del proyecto.

Motivo:

- Permite retomar el trabajo rápido sin depender solo del historial de conversación.
- Resume invariantes arquitectónicas, estado actual, grafo de dependencias y próximo paso recomendado.
- Reduce riesgo de mezclar responsabilidades entre UI, motor técnico, BOM y exportación.

Consecuencia:

- Debe actualizarse cuando cambie el grafo del proyecto, el estado de implementación o el próximo paso recomendado.

## ADR-007 — Scaffolding primero, lógica después

Decisión: crear primero la estructura modular y placeholders antes de implementar modelos, cálculos o BOM.

Motivo:

- Respeta el orden de `docs/08_OPENCODE_PROMPTS.md`.
- Evita introducir fórmulas en `app.py`.
- Deja límites claros para las siguientes fases testeables.

Consecuencia:

- Los módulos iniciales contienen docstrings y quedan pendientes de implementación en los prompts siguientes.

## ADR-008 — Catálogos semilla procesados

Decisión: crear catálogos CSV semilla en `data/processed/` para habilitar el flujo funcional inicial.

Motivo:

- Permite probar selección de sistema, cálculo, cilindros, BOM y opcionales antes de terminar la normalización del Excel.
- Mantiene los datos fuera del motor, cumpliendo la regla de no hardcodear precios ni catálogos técnicos en funciones de cálculo.
- Facilita que el usuario edite componentes y opcionales sin tocar código.

Consecuencia:

- Los valores semilla deben validarse contra `data/raw/calculo_supresion.xlsx` y manuales antes de uso comercial real.

## ADR-009 — Una sala funcional antes de múltiples salas

Decisión: implementar primero el flujo funcional para una sala completa antes de extender a múltiples salas.

Motivo:

- Reduce complejidad inicial y permite validar el ciclo completo: entrada -> cálculo -> cilindro -> BOM -> opcionales.
- La lógica queda preparada para repetirse por sala cuando se agregue `st.data_editor` multi-sala.

Consecuencia:

- El siguiente incremento debe generalizar el flujo actual a una lista de salas y consolidar BOM total.

## ADR-010 — UI por pasos con tabla multi-sala

Decisión: reorganizar la interfaz en tres pasos principales y mover datos generales del proyecto al sidebar.

Motivo:

- Reduce saturación visual frente a formularios largos.
- Permite comparar y editar múltiples salas en una sola tabla.
- Separa claramente entrada, cálculo y BOM para guiar al usuario comercial/técnico.

Consecuencia:

- La configuración avanzada por sala, como forzar cilindros o boquillas, queda pendiente para un incremento posterior.
- El cálculo por sala sigue delegándose al motor y el BOM a `src/bom/`; la UI solo orquesta y presenta.

## ADR-011 — Exportación Excel con OpenPyXL

Decisión: implementar la exportación Excel en memoria usando `openpyxl`.

Motivo:

- Ya está disponible en el entorno y en dependencias del proyecto.
- Permite generar y validar hojas XLSX sin depender de `xlsxwriter`.
- Mantiene la exportación encapsulada en `src/exporters/`.

Consecuencia:

- `requirements.txt` conserva `openpyxl` y elimina `xlsxwriter` como dependencia inicial.

## ADR-012 — UI de alto contraste y tablas resumidas

Decisión: mostrar en pantalla vistas resumidas y legibles, manteniendo datos completos para exportación.

Motivo:

- Evita saturar al usuario con columnas técnicas internas.
- Mejora contraste de métricas, tabs, sidebar y encabezados de sección.
- Optimiza el espacio para cotizaciones con varias salas.

Consecuencia:

- Las funciones `_results_display_df`, `_cylinders_display_df` y equivalentes de BOM controlan la presentación sin alterar los DataFrames fuente.

## ADR-013 — Tema minimalista profesional

Decisión: definir tema Streamlit en `.streamlit/config.toml` y CSS local con paleta neutra profesional.

Motivo:

- Mejorar legibilidad de texto sobre fondos claros.
- Reducir ruido visual manteniendo jerarquía entre sidebar, tabs, métricas, tablas y alertas.
- Evitar combinaciones de bajo contraste en componentes nativos de Streamlit.

Consecuencia:

- Los estilos visuales principales viven en `_inject_style()` y el tema base en `.streamlit/config.toml`.
- Cualquier ajuste futuro de UI debe preservar contraste entre texto y fondo.

## ADR-014 — Gestión explícita de salas en UI

Decisión: reemplazar la dependencia de filas dinámicas implícitas por botones visibles `Agregar sala` y `Quitar salas`.

Motivo:

- El usuario necesita una forma clara de cargar y eliminar salas sin conocer controles ocultos de `st.data_editor`.
- Separar `Calcular` de `Quitar` evita eliminar accidentalmente salas que solo estaban marcadas para cálculo.
- Mostrar área y volúmenes calculados en la tabla reduce incertidumbre antes de ejecutar el cálculo técnico completo.

Consecuencia:

- La tabla mantiene columnas de preview calculadas en la UI, mientras el cálculo técnico oficial sigue viviendo en `src/engine/`.

## ADR-015 — Fallback a múltiples cilindros iguales

Decisión: si `SISTEMA` no encuentra un cilindro simple compatible, el selector intenta múltiples cilindros iguales y emite advertencia.

Motivo:

- Evita bloquear el cálculo técnico cuando el volumen o la altitud elevan el agente requerido sobre la capacidad de un cilindro simple.
- Mantiene la regla crítica de no mezclar tamaños de cilindro.
- Permite al usuario revisar el resultado y decidir si corresponde cambiar el tipo de sistema a `MANIFOLD`.

Consecuencia:

- El BOM multiplica componentes dependientes de cilindro como descarga cuando la selección usa más de un cilindro.

Actualización:

- La selección automática puede usar múltiples cilindros iguales, pero todos deben quedar dentro de sus límites absolutos.
- Si no existe una combinación válida dentro del máximo configurado, el cálculo de esa sala se bloquea con un error técnico; no se genera un BOM con llenado inválido.
- Las salas se calculan independientes; no se asume que varias salas pertenezcan al mismo manifold.

## ADR-016 — Reserva y Main Reserve explícitos pero no implícitos

Decisión: exponer `Reserva` y `Main reserve` como flags por sala, pero no generar BOM adicional hasta implementar sus reglas específicas.

Motivo:

- Evita duplicar componentes por accidente.
- Hace visible la intención comercial del usuario sin mezclar reglas incompletas.
- Permite que el cálculo de agente y BOM base funcione aunque reserva/main reserve estén desmarcados.

Consecuencia:

- Si el usuario marca reserva o main reserve, la UI muestra advertencia informativa hasta implementar `reserve_builder.py` y `main_reserve_builder.py`.

## ADR-017 — Catálogo BOM y cilindros desde Excel base

Decisión: regenerar `bom_catalog.csv` y `cylinder_catalog.csv` desde `data/raw/calculo_supresion.xlsx`, hoja `BDD_SISTEMAS- MANIFOLD`.

Motivo:

- El catálogo semilla no incluía cilindros pequeños como `TANK SIZE 16L` y `TANK SIZE 32L`.
- El Excel base contiene códigos reales, rangos de llenado en libras y componentes por tamaño de cilindro.
- La estimación debe acercarse al programa/manual de la marca, especialmente en agente, cilindro e ítems base.

Consecuencia:

- La selección de cilindros prioriza menor cantidad de cilindros y luego menor exceso.
- La UI muestra kg, lb y porcentaje de llenado del cilindro para revisar que no se cargue fuera de rango.
- Los rangos en libras se convierten a kg para el motor, manteniendo lb visibles para operación de carga.

## ADR-018 — Margen recomendado de llenado para presurización

Decisión: agregar `recommended_max_fill_pct` al catálogo de cilindros y usarlo para optimizar la selección preliminar.

Motivo:

- Un cilindro técnicamente puede estar dentro del máximo absoluto, pero quedar demasiado cargado para un margen razonable de presurización.
- La operación carga cilindros en libras, por lo que se muestran kg, lb y porcentaje de llenado.
- Para el MVP se usa `85%` como margen recomendado editable en catálogo, independiente del máximo absoluto del manual/catálogo.

Consecuencia:

- Si un cilindro supera el margen recomendado, el selector prefiere el siguiente tamaño compatible antes de emitir advertencia.
- Caso de referencia FK-5-1-12, 2 x 4 x 2.5 m, 4.5%, 1 msnm: `13.5 kg / 29.8 lb`, `TANK SIZE 16L`, llenado aproximado `70.9%`.

## ADR-019 — Corrección de outliers decimales en flooding factors

Decisión: sanear factores de `tabla_temperatura` cuando el valor imperial es mayor a `0.2 lb/ft³`, dividiendo por 10 y marcando la fuente como `corrected_decimal_outlier`.

Motivo:

- En la tabla FM-200 del Excel existen valores con decimal corrido, por ejemplo `0.4500` donde corresponde `0.0450`.
- Esos outliers multiplicaban el agente calculado por 10 y generaban diferencias enormes.

Consecuencia:

- `flooding_factors.csv` queda regenerado con correcciones explícitas en la columna `source`.
- Hay tests que impiden volver a cargar factores FM-200 fuera de rango razonable.

## ADR-020 — Edición estable de salas

Decisión: envolver el editor de salas en un formulario con botón `Guardar cambios de salas`.

Motivo:

- Evita que Streamlit rerenderice la tabla en cada tecla o cambio parcial.
- Reduce pérdida de valores cuando el usuario ingresa dimensiones rápidamente.
- Mantiene el cálculo técnico desacoplado: solo se recalcula al guardar y luego al presionar `Calcular salas seleccionadas`.

Consecuencia:

- Área y volumen se actualizan al guardar cambios, no en cada tecla.
- `MANIFOLD` se retira del flujo principal visible para evitar activar múltiples cilindros por error; se retomará en una etapa específica de reserva/main reserve.

## ADR-021 — Selección manual y previsualización de cilindros

Decisión: permitir `Automático` o cilindro forzado por sala, y mostrar una tabla de alternativas de llenado.

Motivo:

- El usuario necesita comparar rápidamente si conviene mantener el cilindro recomendado o elegir otro tamaño.
- Para FM-200 cerca de 29 lb, el cilindro correcto es `16L`; múltiples `8L` no deben ser preferidos automáticamente.
- Los cilindros fuera de rango deben visualizarse como alternativa no válida o crítica antes de generar BOM.

Consecuencia:

- El BOM se filtra por el cilindro finalmente seleccionado.
- El selector automático prioriza un cilindro único válido dentro del rango absoluto y solo advierte si está cerca/sobre el margen recomendado.

Actualización:

- La selección manual de cilindro se movió fuera del `st.data_editor` a un control dedicado por sala para evitar problemas de edición/guardado dentro de la grilla.
- La previsualización de alternativas permite aplicar directamente un cilindro válido a la sala calculada y obliga a recalcular antes de generar BOM.

## ADR-022 — Cierre de sesión MVP técnico

Decisión: dejar como baseline funcional el flujo de cálculo independiente por sala, selección/previsualización de cilindro y BOM base exportable.

Motivo:

- FK-5-1-12 y FM-200 ya calculan agente en kg/lb con catálogos procesados desde Excel.
- La selección de cilindros usa rangos reales en lb y muestra porcentaje de llenado.
- El usuario puede forzar cilindro válido y regenerar BOM según ese cilindro.

Consecuencia:

- En el cierre original, el próximo foco era reserva, main reserve y opcionales reales.
- Esta prioridad queda reemplazada por ADR-023 a ADR-026: primero se estabilizarán fórmulas, altitud y cilindros contra manuales oficiales.
- Antes de uso comercial, se validarán el cálculo técnico y el BOM contra manuales, software oficial y casos reales.

## ADR-023 — Manuales del fabricante como autoridad técnica

Decisión: las fórmulas, rangos y límites técnicos se validarán contra los manuales oficiales del fabricante; el Excel base será únicamente una referencia comercial y comparativa.

Motivo:

- `flooding_factors.csv`, derivado del Excel, contiene valores FK-5-1-12 discontinuos y físicamente inconsistentes.
- Los manuales documentan las ecuaciones necesarias para calcular factores sin depender de filas corruptas.
- El pre-dimensionamiento debe ser trazable a una fuente técnica identificable.

Consecuencia:

- FK-5-1-12 usará `S = 0.0664 + 0.000274T`.
- FM-200 usará `S = 0.1269 + 0.000513T`.
- En ambos casos se calculará `W/V = (1/S) * (C/(100-C))` dentro de `src/engine/`.
- Los coeficientes inmutables de las ecuaciones viven en `src/engine/agent.py`; los catálogos externos conservan los datos comerciales y tablas de referencia, sin gobernar la fórmula.
- Las tablas impresas se usarán para regresión cuando sean consistentes con la ecuación; no se copiarán ciegamente errores tipográficos aparentes.

Implementación:

- FM-200 usa el coeficiente más preciso publicado: `S = 0.1269 + 0.0005131T`, dentro de `-10 °C` a `55 °C` y `6.4%` a `15%`.
- FK-5-1-12 usa `S = 0.0664 + 0.000274T`, dentro de `-20 °C` a `65 °C` y `4%` a `10%`.
- Las entradas fuera del dominio tabulado se rechazan para evitar extrapolación no autorizada.

## ADR-024 — Corrección de altitud según NFPA 2001

Decisión: aplicar la tabla NFPA 2001, con factor `1.0` dentro de la banda opcional entre `-914 m` y `+914 m`, e interpolación lineal fuera de ella.

Motivo:

- El usuario seleccionó NFPA 2001 como norma gobernante del MVP.
- Ambos manuales indican que el agente requerido se multiplica por el factor de altitud.
- El catálogo provisional actual invierte el efecto físico al aumentar el factor con la altitud positiva.

Consecuencia:

- La entrada en metros se convertirá a pies antes de consultar/interpolar la tabla NFPA.
- No se extrapolará fuera del dominio documentado.
- Las entradas no soportadas producirán un mensaje de validación en español.

Implementación:

- `altitude_factors.csv` contiene los puntos NFPA de `0 ft` a `10000 ft`, expresados también en metros exactos.
- `src/engine/altitude.py` interpola linealmente entre puntos; entre `-914 m` y `+914 m` retorna `1.0` por la banda opcional acordada.
- Altitudes inferiores a `-914 m` se rechazan porque los manuales no publican factores negativos; sobre `3048 m` se rechazan para no extrapolar.

## ADR-025 — Familia DOT welded con mapeo comercial y técnico

Decisión: usar para el MVP la familia DOT welded de 8, 16, 32, 52, 106, 147, 180 y 343 L, conservando los SKU comerciales `445732` a `445739` y agregando la referencia de ensamble oficial por agente.

Motivo:

- Es la familia que coincide con los tamaños comercializados en el catálogo actual.
- Los números de ensamble y límites técnicos difieren entre FM-200 y FK-5-1-12.
- Separar el SKU comercial de la referencia técnica evita perder continuidad comercial o atribuir un ensamble incorrecto.

Consecuencia:

- `cylinder_catalog.csv` deberá incorporar la referencia técnica y fuente documental.
- Los límites mínimo/máximo se actualizarán desde las tablas DOT welded de cada manual.
- El selector no podrá devolver una configuración fuera de esos límites, ni siquiera como fallback preliminar.

Implementación:

- Los límites de `cylinder_catalog.csv` se actualizaron desde la Tabla 2-6 de cada manual, manteniendo los SKU comerciales existentes.
- Si no hay una combinación de cilindros iguales dentro del rango absoluto y del máximo configurado, el selector genera error en español en vez de fabricar una alternativa inválida.

## ADR-026 — Arquitectura objetivo React y FastAPI

Decisión: después de estabilizar el motor, evolucionar la aplicación a una SPA React/TypeScript responsive que consuma una API FastAPI versionada y privada.

Motivo:

- La tabla Streamlit actual es demasiado ancha para una experiencia móvil adecuada.
- El motor Python ya está parcialmente desacoplado y debe seguir siendo la única autoridad de cálculo.
- Una capa de servicio independiente del framework permitirá reutilizar cálculo, BOM y exportación sin duplicarlos en React.

Consecuencia:

- Antes de FastAPI se extraerá de `src/ui/main.py` un servicio de aplicación para orquestación y DTO.
- React no implementará fórmulas técnicas ni reglas BOM.
- FastAPI podrá servir la API y el build estático como un único artefacto de despliegue.
- La plataforma de hosting y el mecanismo de autenticación privada quedan pendientes de definición.
- La corrección técnica tiene prioridad sobre reserva, main reserve y el nuevo frontend.

## ADR-027 — Flujo por sala y política preliminar de boquillas

Decisión: reemplazar la grilla principal por formularios independientes con identidad estable, eliminación directa y cálculo al guardar. Calcular boquillas por volumen protegido y aplicar como preferencia interna una cantidad total par, excepto cuando sala, piso técnico y cielo falso requieren exactamente una cada uno.

Motivo:

- La grilla obligaba a guardar marcas antes de eliminar y podía perder configuraciones ocultas.
- El usuario necesita ver agente, cilindro y boquillas inmediatamente después de completar cada sala.
- Los manuales exigen al menos una boquilla por espacio protegido, pero no exigen paridad; por eso la paridad se documenta como política interna y no como requisito normativo.

Consecuencia:

- Cada sala conserva un `room_id` independiente de su posición o nombre.
- Piso técnico y cielo falso se incluyen en volumen y boquillas solo cuando el usuario los marca como protegidos.
- FM-200 usa cobertura estándar preliminar de `95.3 m²` y FK-5-1-12 de `96 m²`, mantenidas en `nozzle_coverage.csv`.
- El mínimo del fabricante, la recomendación interna y la cantidad final se conservan como valores separados.
- Las configuraciones de cilindros visibles en UI son generadas por `src/engine/cylinder_selector.py`; Streamlit no replica sus límites.
- El requisito de descarga de `6 a 10 s` siempre queda marcado para validación hidráulica certificada.

## ADR-028 — Formulario guiado y lenguaje explícito

Decisión: organizar cada sala en cuatro pasos visibles y usar etiquetas que describan directamente el efecto de cada control.

Motivo:

- Etiquetas aisladas como `Incluir` obligaban al usuario a inferir si afectaban cálculo, BOM o visualización.
- Reducciones, overrides y reservas no forman parte del recorrido habitual y aumentaban la carga cognitiva.
- El resultado recién calculado debe permanecer visible para confirmar inmediatamente la acción realizada.

Consecuencia:

- La selección principal indica explícitamente `Incluir esta sala en el cálculo, los totales y el BOM de la cotización`.
- El formulario sigue el orden identificación, dimensiones, espacios adicionales y condiciones de diseño.
- Reducciones, override de boquillas y alcance comercial quedan dentro de `Ajustes avanzados`.
- La sala recién agregada o guardada se mantiene abierta y muestra su estado como pendiente, calculada, no incluida o requiere revisión.
- Marcar piso técnico o cielo falso como protegido exige una altura positiva y explica que agrega volumen y una boquilla independiente.

## ADR-029 — Factor atmosférico por escalón de tabla

Decisión: calcular el factor atmosférico por defecto con el escalón inferior de la tabla NFPA/ANSUL expresada en pies, sin interpolación lineal.

Motivo:

- El manual ANSUL indica que el agente inicial se multiplica por el factor de altitud.
- El software de memoria de cálculo reporta `Factor de Corrección Atmosférica = 1` para `50 m` y `0.96` para `500 m`.
- Ese comportamiento coincide con convertir msnm a pies y seleccionar el mayor escalón publicado menor o igual a la elevación real: `50 m = 164 ft -> 0 ft -> 1.00`; `500 m = 1640 ft -> 1000 ft -> 0.96`.
- La herramienta debe alinearse por defecto con el software certificado usado como referencia.

Consecuencia:

- `50 msnm` usa factor `1.0`; `500 msnm` usa factor `0.96`; `914 msnm` usa factor `0.93`.
- La interpolación lineal queda disponible en el motor con `interpolate=True`, pero no es el comportamiento predeterminado.
- Caso de referencia SAPPHIRE/FK-5-1-12, `18 x 6 x 4 m`, `16 °C`, `4.52%`, `50 msnm`: `288.92 kg`, igual al software de memoria de cálculo.
- Caso de referencia SAPPHIRE/FK-5-1-12, `18 x 6 x 4 m`, `16 °C`, `4.52%`, `500 msnm`: `277.36 kg`, igual al software de memoria de cálculo.
- Caso de referencia SAPPHIRE/FK-5-1-12, `18 x 6 x 4 m`, `16 °C`, `4.53%`, `500 msnm`: `278.00 kg`, igual al agente ajustado requerido del software.

## ADR-030 — Agente ajustado y concentración lograda

Decisión: redondear el agente requerido hacia arriba a `1 kg` y calcular las concentraciones logradas mínima y máxima con el agente redondeado.

Motivo:

- El software de memoria de cálculo reporta un agente mínimo exacto y un agente ajustado requerido redondeado a kg entero.
- La concentración ajustada y concentración máxima del software se obtienen recalculando la concentración con el agente redondeado y el factor atmosférico.
- La comparación contra software certificado requiere conservar ambos valores: mínimo exacto y ajustado comercial/técnico.

Consecuencia:

- `agent_required_exact_kg` representa el mínimo matemático previo al redondeo.
- `agent_required_rounded_kg` representa el agente ajustado requerido para selección de cilindro y BOM.
- `minimum_concentration_achieved_pct` usa temperatura mínima; `maximum_concentration_achieved_pct` usa temperatura máxima.
- Caso de referencia SAPPHIRE/FK-5-1-12, `18 x 6 x 4 m`, `16 °C` a `27 °C`, `4.52%`, `500 msnm`: mínimo `277.36 kg`, ajustado `278 kg`, concentración ajustada `4.530%`, concentración máxima `4.71%`.

## ADR-031 — UI de captura simplificada y sidebar técnico

Decisión: simplificar la carga por sala mostrando primero nombre, agente, tipo de sistema, dimensiones y condiciones de diseño, dejando reducciones, boquillas, reserva y opcionales dentro de ajustes avanzados. El sidebar usa un estilo visual diferenciado de color azul petróleo profesional.

Motivo:

- La operación habitual requiere cargar muchas salas con pocos datos críticos.
- El tipo de sistema impacta selección de cilindros y debe ser visible al usuario.
- Un sidebar más contrastado separa datos del proyecto de cálculo técnico y mejora navegación.

Consecuencia:

- Cada sala permite elegir `SISTEMA` o `MANIFOLD` desde la tarjeta principal.
- Los resultados inmediatos destacan agente exacto, agente ajustado y concentraciones logradas.
- El estilo mantiene una estética minimalista profesional con paleta azul técnico, cian de acento y superficies claras.

## ADR-032 — Perfiles, reducciones y volumen muerto según manuales

Decisión: implementar perfiles de concentración desde catálogo externo, validar reducciones por objetos según criterio de sólidos permanentes/no removibles y agregar masa retenida por volumen muerto de manifold/tubería como carga almacenada separada de la masa descargada al recinto.

Motivo:

- Los manuales ANSUL PN442940-01 y PN451540-01 publican concentraciones mínimas por perfil UL/FM y agente.
- Los manuales permiten descontar solo objetos sólidos permanentes/no removibles ubicados dentro del volumen protegido.
- La Tabla 5-8 publica volúmenes muertos de manifold; el agente retenido se suma a la carga almacenada, pero no debe aumentar la concentración del recinto.
- La selección de cilindros y BOM deben usar la carga total almacenada; la concentración lograda debe usar el agente disponible para descarga en el recinto.

Consecuencia:

- `concentration_profiles.csv` gobierna perfiles como `UL/FM Class A`, `UL/FM Class C`, `FM Class C` y referencias Class B que requieren revisión técnica.
- `dead_volume_factors.csv` contiene DN65, DN80, DN100 y DN150 con volúmenes de extremo muerto y sección de reserva de Tabla 5-8.
- `agent_required_exact_kg` representa carga total exacta: agente del recinto más retención por tubería/manifold.
- `enclosure_agent_required_exact_kg` representa solo el agente requerido para el recinto.
- `pipe_agent_allowance_kg` representa el agente retenido estimado y no participa en el cálculo de concentración lograda.
- El cálculo hidráulico final, orificios, presiones, tiempos de descarga y distribución siguen fuera del alcance del cotizador y requieren software certificado.

## ADR-033 — Acciones rápidas y contraste visual

Decisión: agregar eliminación rápida visible por sala y ajustar los selectores CSS del sidebar para evitar texto claro sobre controles claros.

Motivo:

- El usuario necesitaba eliminar salas sin abrir cada tarjeta.
- Los estilos previos aplicaban color claro a elementos internos de widgets del sidebar, causando texto blanco sobre fondos blancos.
- La interfaz debe mantener contraste profesional para carga rápida de datos técnicos.

Consecuencia:

- Cada sala muestra una barra compacta con nombre, agente, sistema y estado junto a un botón `Eliminar`.
- El sidebar conserva fondo azul petróleo y labels claros, mientras los valores dentro de inputs/selects usan texto oscuro sobre fondo claro.
- La eliminación dentro del formulario sigue disponible como acción secundaria.

Actualización:

- El encabezado principal se reemplaza por un bloque narrativo que explica el flujo `Proyecto -> Salas -> Validación -> BOM`.
- La guía superior usa steps circulares compactos para reducir altura en cotizaciones con muchas salas.
- Los botones secundarios y sus estados hover usan texto azul oscuro sobre fondos claros para evitar texto blanco sobre blanco.
- Los botones del sidebar tienen reglas específicas para que los textos internos no hereden el color claro usado por los labels del panel lateral.
