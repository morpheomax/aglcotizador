# 08 — Prompts listos para OpenCode

## Prompt 1 — Inicializar proyecto

```txt
Lee AGENTS.md y todos los archivos dentro de docs/. Luego crea la estructura base del proyecto Streamlit según docs/05_ARCHITECTURE_STREAMLIT.md. No implementes todavía toda la lógica. Crea carpetas, archivos __init__.py, app.py mínimo, requirements.txt y README.md técnico. Mantén app.py liviano y separa módulos según arquitectura.
```

## Prompt 2 — Implementar modelos

```txt
Implementa los modelos definidos en docs/04_DATA_MODEL.md usando dataclasses o Pydantic. Usa type hints estrictos. Crea tests básicos para instanciar ProjectInfo, RoomInput, SystemConfig, RoomCalculationResult, CylinderOption, SelectedCylinder y BomLine.
```

## Prompt 3 — Implementar cálculo de volumen

```txt
Implementa src/engine/volume.py con funciones para área, volumen sala, volumen piso técnico, volumen cielo falso, volumen bruto y volumen neto. Agrega validaciones para dimensiones negativas o cero donde corresponda. Crea tests usando los casos de docs/07_TEST_CASES.md.
```

## Prompt 4 — Cargar Excel base

```txt
Implementa src/data/excel_loader.py para leer data/raw/calculo_supresion.xlsx. Debe cargar las hojas CALC_AGENT, INGRESO_DATOS_SALA, BDD_SISTEMAS- MANIFOLD, tabla_temperatura y COT AGENTES. Crea una función para normalizar BDD_SISTEMAS- MANIFOLD a un bom_catalog_df con columnas snake_case. No modifiques el Excel original.
```

## Prompt 5 — Crear catálogos procesados

```txt
Crea src/data/normalizer.py para exportar catálogos procesados a data/processed/: bom_catalog.csv, flooding_factors.csv y un cylinder_catalog.csv inicial. Usa los datos del Excel cuando sea posible, pero deja funciones separadas para editar manualmente el catálogo de cilindros si falta información.
```

## Prompt 6 — Implementar cálculo de agente

```txt
Implementa src/engine/agent.py, altitude.py y nozzles.py. Deben aceptar catálogos externos y retornar resultados determinísticos. Usa los tests de docs/07_TEST_CASES.md. Agrega advertencias cuando no se encuentre flooding factor o factor altitud.
```

## Prompt 7 — Selector de cilindros

```txt
Implementa src/engine/cylinder_selector.py. Debe seleccionar cilindro simple y manifold. Para manifold, todos los cilindros deben ser iguales y con el mismo fill weight. Debe permitir forzar cilindro y validar si el llenado por cilindro cae entre min_fill_kg y max_fill_kg.
```

## Prompt 8 — BOM base

```txt
Implementa src/bom/bom_builder.py. Debe filtrar bom_catalog_df por tipo, cilindro y agente. Debe generar BomLine por cada ítem. Debe multiplicar cantidades por número de cilindros cuando corresponda. Debe ajustar la línea de agente a la cantidad calculada cuando el código corresponda al agente.
```

## Prompt 9 — Reserva y main reserve

```txt
Implementa src/bom/reserve_builder.py y main_reserve_builder.py. La reserva no debe duplicar boquillas, descarga ni actuadores salvo regla explícita. Main reserve debe tener reglas independientes y ser configurable. Agrega tests.
```

## Prompt 10 — UI Streamlit completa MVP

```txt
Implementa la UI Streamlit con tabs: Proyecto, Salas, Configuración, Resultados técnicos, BOM y Exportar. Usa st.data_editor para múltiples salas. No pongas lógica técnica dentro de app.py; app.py debe llamar funciones del motor.
```

## Prompt 11 — Exportar Excel

```txt
Implementa src/exporters/excel_exporter.py para generar un Excel en memoria con hojas Resumen, Salas, Resultados_Tecnicos, BOM_Detalle, BOM_Consolidado y Advertencias. Agrega botón st.download_button en la UI. Usa formato básico profesional.
```

## Prompt 12 — Revisión final

```txt
Ejecuta pytest. Corrige errores. Revisa que app.py corra con streamlit run app.py. Revisa que se pueda crear un proyecto con 2 salas, calcular resultados, generar BOM y descargar Excel. Actualiza DECISIONS.md y TASKS.md con lo implementado y lo pendiente.
```
