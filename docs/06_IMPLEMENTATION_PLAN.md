# 06 — Plan de implementación

## Fase 0 — Setup

Objetivo: crear estructura base.

Tareas:

- Crear repositorio/proyecto.
- Crear entorno virtual.
- Instalar dependencias.
- Crear estructura de carpetas.
- Copiar `calculo_supresion.xlsx` a `data/raw/`.
- Crear archivos `.gitignore`, `README.md`, `requirements.txt`.

Comandos:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install streamlit pandas openpyxl xlsxwriter pydantic pytest
pip freeze > requirements.txt
streamlit run app.py
```

## Fase 1 — Modelos y cálculo de volumen

Objetivo: cálculo base por sala.

Tareas:

- Crear modelos `RoomInput`, `ProjectInfo`, `SystemConfig`.
- Crear `volume.py`.
- Crear tests de área, volumen bruto y volumen neto.
- Crear UI simple para ingresar 1 sala.

Resultado esperado:

- App muestra área, volumen bruto y volumen neto.

## Fase 2 — Catálogos

Objetivo: cargar datos desde Excel o CSV.

Tareas:

- Crear `excel_loader.py`.
- Leer hoja `BDD_SISTEMAS- MANIFOLD`.
- Normalizar columnas.
- Exportar a `data/processed/bom_catalog.csv`.
- Crear catálogo de cilindros inicial manual o extraído.
- Crear catálogo flooding factors desde `tabla_temperatura`.

Resultado esperado:

- App puede mostrar catálogos cargados.

## Fase 3 — Cálculo de agente

Objetivo: estimar agente requerido.

Tareas:

- Crear `agent.py`.
- Crear `altitude.py`.
- Crear `nozzles.py`.
- Aplicar flooding factor.
- Aplicar corrección altitud.
- Calcular boquillas mínimas.
- Crear tests.

Resultado esperado:

- App muestra agente requerido por sala.

## Fase 4 — Selección de cilindro

Objetivo: elegir cilindro preliminar.

Tareas:

- Crear `cylinder_selector.py`.
- Seleccionar cilindro compatible.
- Seleccionar múltiples cilindros iguales para manifold.
- Permitir forzar cilindro.
- Crear advertencias.
- Crear tests.

Resultado esperado:

- App recomienda cilindro y cantidad.

## Fase 5 — BOM base

Objetivo: armar BOM por sala.

Tareas:

- Crear `bom_builder.py`.
- Filtrar catálogo por `TIPO`, `CILINDRO`, `AGENTE`.
- Multiplicar cantidades por número de cilindros cuando aplique.
- Ajustar cantidad de agente según cálculo.
- Generar `bom_detail_df`.

Resultado esperado:

- App muestra BOM por sala.

## Fase 6 — Opcionales, reserva y main reserve

Objetivo: hacer configurable el BOM.

Tareas:

- Crear `reserve_builder.py`.
- Crear `main_reserve_builder.py`.
- Crear selección de opcionales.
- Excluir ítems no aplicables.
- Consolidar ítems.

Resultado esperado:

- App puede activar/desactivar opcionales, reserva y main reserve.

## Fase 7 — Exportación Excel

Objetivo: generar BOM descargable.

Tareas:

- Crear `excel_exporter.py`.
- Exportar hojas:
  - `Resumen`
  - `Salas`
  - `Resultados_Tecnicos`
  - `BOM_Detalle`
  - `BOM_Consolidado`
  - `Advertencias`
- Aplicar formato básico.

Resultado esperado:

- Botón descarga Excel funcional.

## Fase 8 — Validación con casos reales

Objetivo: comparar contra Excel actual.

Tareas:

- Crear 3 casos de prueba reales.
- Comparar agente requerido.
- Comparar cilindros.
- Comparar BOM.
- Documentar diferencias.

Resultado esperado:

- MVP validado internamente.
