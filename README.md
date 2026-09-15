# Cotizador Supresión FK-5-1-12 / FM-200

Aplicación Streamlit para cotización y pre-dimensionamiento técnico-comercial de sistemas de supresión por agente limpio FK-5-1-12 y FM-200.

## Objetivo

Crear un cotizador técnico-comercial en **Python + Streamlit** para sistemas de supresión por agente limpio:

- FK-5-1-12 / ANSUL SAPPHIRE.
- FM-200 / ANSUL FM-200.
- Múltiples salas independientes.
- Sistemas individuales, manifold, reserva y main reserve.
- BOM descargable en Excel con códigos, cantidades y precio futuro.

## Estado actual

MVP funcional inicial creado:

- Estructura modular bajo `src/`.
- `app.py` liviano que delega la UI a `src/ui/main.py`.
- UI organizada en 3 pasos: sistemas y salas, resultados, BOM y opcionales.
- Diseño visual optimizado con mayor contraste, métricas tipo tarjeta y vistas de tabla reducidas.
- Sidebar técnico diferenciado con paleta azul profesional, controles legibles y estados hover consistentes.
- Encabezado narrativo con flujo guiado de proyecto, salas, validación y BOM para orientar al usuario.
- Ingreso de múltiples salas mediante tarjetas independientes con identidad estable.
- Acciones directas para agregar y eliminar salas, incluyendo botón rápido de eliminación sin abrir la tarjeta.
- Botón `Guardar y calcular esta sala`, con agente en kg/lb y configuración técnica mostrados inmediatamente.
- Selección explícita de piso técnico y cielo falso como volúmenes protegidos.
- Ajustes avanzados por sala para registrar `Reserva` y `Main reserve`; no generan BOM adicional hasta implementar sus reglas específicas.
- Cálculo preliminar por sala de volumen, agente, altitud, boquillas y cilindro.
- Resultados de agente en kg y lb.
- Resultado de cilindro con kg/cilindro, lb/cilindro y porcentaje de llenado respecto al máximo permitido.
- Selector optimizado con margen recomendado de llenado del `85%` para reservar volumen de presurización.
- Selección automática o manual entre configuraciones de cilindros técnicamente válidas, incluyendo múltiples cilindros iguales.
- Cálculo de boquillas por volumen protegido con cobertura oficial y preferencia interna por cantidades pares.
- Excepción automática de tres boquillas cuando sala, piso técnico y cielo falso requieren una cada uno.
- Cantidad manual impar permitida únicamente con justificación técnica.
- Cada sala se calcula de forma independiente, aunque use distinto agente o esté en otro sector.
- El cálculo de agente permanece visible aunque no exista una selección de cilindros válida; el BOM se bloquea hasta corregirla.
- Generación de BOM base desde `data/processed/bom_catalog.csv`.
- Opcionales editables desde `data/processed/optional_items.csv`.
- BOM detallado por sala y BOM consolidado total en pantalla.
- Descarga Excel con hojas de resumen, salas, resultados, cilindros, BOM y advertencias.
- `requirements.txt` con dependencias iniciales.
- `data/raw/calculo_supresion.xlsx` disponible como fuente operativa.
- Catálogos semilla editables en `data/processed/`.
- Documentación de producto, técnica y arquitectura en `docs/`.
- Archivo de continuidad para OpenCode en `PROJECT_GRAPH.md`.

Última validación:

- Suite unitaria y flujo real de Streamlit automatizados con `pytest` y `streamlit.testing`.
- Baseline actual: `53 passed`.
- Fórmulas de agente, altitud, cilindros y cobertura de boquillas trazadas a manuales ANSUL.
- Tiempo de descarga de `6 a 10 s` mostrado como requisito pendiente de validación hidráulica certificada.

Pendiente antes de uso comercial real:

- Validar una cotización completa contra software oficial y un caso comercial real.
- Mapear formalmente SKU comerciales a ensambles oficiales.
- Implementar reserva y main reserve.
- Implementar reglas BOM de reserva y main reserve.
- Validar BOM exportado con una cotización real contra Excel/programa de la marca.
- Revisar opcionales reales y clasificar qué entra por defecto y qué queda seleccionable.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar la app

```bash
python -m streamlit run app.py
```

## Ejecutar tests

```bash
pytest
```

## Retomar Trabajo

Para continuar:

1. Ejecutar `python -m pytest -p no:cacheprovider`; se esperan `53 passed`.
2. Ejecutar `python -m streamlit run app.py`.
3. Probar una sala FK-5-1-12 y una FM-200 con el flujo guiado.
4. Probar exclusión, cambio de cilindro, eliminación y el caso sala + piso + cielo.
5. Generar BOM y descargar Excel.
6. Comparar contra el Excel/programa de la marca y una cotización real.

Siguiente foco recomendado: revisión visual/manual y validación end-to-end; después, reserva, main reserve y opcionales reales.

## Flujo de uso actual

1. Abrir la app con `python -m streamlit run app.py`.
2. Completar datos del proyecto.
3. Ir a `1. Sistemas y salas`.
4. Usar `Agregar sala` y completar la tarjeta correspondiente.
5. Indicar si piso técnico y cielo falso son volúmenes protegidos.
6. Presionar `Guardar y calcular esta sala` para obtener agente, cilindro y boquillas inmediatamente.
7. Mantener la configuración automática de cilindros o aplicar otra alternativa válida.
8. Revisar el mínimo técnico y la cantidad final de boquillas; usar override solo cuando sea necesario.
9. Usar `Eliminar esta sala` dentro de la tarjeta para quitarla directamente.
10. Ir a `2. Resultados` para revisar el consolidado o recalcular todas las salas.
11. Ir a `3. BOM y opcionales`, generar el BOM y descargar el Excel.

## Catálogos editables

- `data/processed/flooding_factors.csv`: tabla histórica de referencia; las ecuaciones oficiales viven en `src/engine/agent.py`.
- `data/processed/altitude_factors.csv`: corrección por altitud.
- `data/processed/cylinder_catalog.csv`: cilindros y rangos de llenado, normalizados desde el Excel base.
- `data/processed/nozzle_coverage.csv`: cobertura estándar y máximo preliminar de boquillas por agente.
- `data/processed/bom_catalog.csv`: componentes base del sistema, normalizados desde `BDD_SISTEMAS- MANIFOLD`.
- `data/processed/optional_items.csv`: opcionales seleccionables.

Los catálogos técnicos de altitud, cilindros y boquillas ya fueron contrastados con los manuales disponibles. El BOM, los opcionales y el mapeo comercial final todavía deben validarse contra una cotización real y el software oficial.

## Estructura

```txt
├── app.py
├── requirements.txt
├── PROJECT_GRAPH.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── templates/
├── docs/
├── src/
│   ├── bom/
│   ├── data/
│   ├── engine/
│   ├── exporters/
│   ├── models/
│   └── ui/
└── tests/
```

## Lectura recomendada para OpenCode

OpenCode debe leer los archivos en este orden:

1. `AGENTS.md`
2. `docs/01_CONTEXT.md`
3. `docs/02_PRODUCT_REQUIREMENTS.md`
4. `docs/03_TECHNICAL_RULES.md`
5. `docs/04_DATA_MODEL.md`
6. `docs/05_ARCHITECTURE_STREAMLIT.md`
7. `docs/06_IMPLEMENTATION_PLAN.md`
8. `docs/07_TEST_CASES.md`
9. `docs/08_OPENCODE_PROMPTS.md`
10. `PROJECT_GRAPH.md`
11. `TASKS.md`

## Principio central

Separar siempre:

```txt
UI Streamlit != motor de cálculo != motor BOM != exportación Excel
```

La app debe poder migrar después a una web app con Astro/React sin reescribir la lógica técnica.

## Responsabilidades por módulo

- `app.py`: configuración Streamlit, orquestación y renderizado de alto nivel.
- `src/models/`: modelos tipados del dominio.
- `src/engine/`: fórmulas técnicas, validaciones y selección preliminar.
- `src/bom/`: construcción, reserva, main reserve y consolidación de BOM.
- `src/data/`: lectura del Excel base y normalización de catálogos.
- `src/exporters/`: exportación Excel en memoria usando `openpyxl`.
- `src/ui/`: componentes Streamlit reutilizables.

## Alcance inicial

MVP v0.1:

- Ingreso de datos generales del proyecto.
- Ingreso de múltiples salas.
- Selección de agente.
- Cálculo de volumen y agente requerido.
- Selección preliminar de cilindros.
- Generación de BOM base.
- Consolidación de BOM total.
- Descarga Excel.

## Fuentes técnicas

- `calculo_supresion.xlsx`: archivo actual usado como base operativa.
- `PN442940-01 Manual 2022.pdf`: manual FM-200 ANSUL.
- `pn451540-01 Manual FK 5-1-12 3.pdf`: manual SAPPHIRE / FK-5-1-12 ANSUL.

## Advertencia de uso

Este proyecto es un **cotizador y pre-dimensionador técnico-comercial**. No reemplaza el cálculo hidráulico final, aprobación de ingeniería, revisión de autoridad competente, software certificado del fabricante ni diseño firmado por personal autorizado.
