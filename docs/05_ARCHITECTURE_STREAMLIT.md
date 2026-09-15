# 05 — Arquitectura Streamlit

## Stack recomendado

```txt
Python 3.11+
Streamlit
Pandas
Pydantic o dataclasses
OpenPyXL o XlsxWriter para exportación
Pytest
```

## Estructura propuesta

```txt
cotizador_supresion/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   │   └── calculo_supresion.xlsx
│   ├── processed/
│   │   ├── bom_catalog.csv
│   │   ├── cylinder_catalog.csv
│   │   ├── flooding_factors.csv
│   │   ├── altitude_factors.csv
│   │   └── optional_items.csv
│   └── templates/
│       └── bom_export_template.xlsx
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── room.py
│   │   ├── system_config.py
│   │   ├── cylinder.py
│   │   └── bom.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── volume.py
│   │   ├── agent.py
│   │   ├── altitude.py
│   │   ├── nozzles.py
│   │   ├── cylinder_selector.py
│   │   └── validators.py
│   ├── bom/
│   │   ├── __init__.py
│   │   ├── catalog_loader.py
│   │   ├── bom_builder.py
│   │   ├── reserve_builder.py
│   │   ├── main_reserve_builder.py
│   │   └── consolidator.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── excel_loader.py
│   │   └── normalizer.py
│   ├── exporters/
│   │   ├── __init__.py
│   │   └── excel_exporter.py
│   └── ui/
│       ├── __init__.py
│       ├── project_form.py
│       ├── rooms_editor.py
│       ├── system_options.py
│       ├── results_view.py
│       └── bom_view.py
└── tests/
    ├── test_volume.py
    ├── test_agent.py
    ├── test_cylinder_selector.py
    ├── test_bom_builder.py
    └── test_exporter.py
```

## Responsabilidades

### `app.py`

Solo debe:

- Configurar la página.
- Cargar catálogos.
- Renderizar UI.
- Orquestar llamadas.
- Mostrar resultados.
- Permitir descarga.

No debe contener fórmulas técnicas ni reglas de BOM.

### `src/engine/volume.py`

Funciones:

```python
calculate_area(length_m, width_m)
calculate_room_volume(length_m, width_m, height_m)
calculate_total_protected_volume(room)
calculate_net_volume(room)
```

### `src/engine/agent.py`

Funciones:

```python
get_flooding_factor(agent_type, concentration_pct, min_temp_c)
calculate_required_agent(net_volume_m3, flooding_factor, altitude_factor)
round_agent_quantity(agent_kg)
```

### `src/engine/altitude.py`

Funciones:

```python
get_altitude_factor(altitude_m, altitude_factors_df)
```

### `src/engine/nozzles.py`

Funciones:

```python
calculate_min_nozzles(area_m2, coverage_m2)
```

### `src/engine/cylinder_selector.py`

Funciones:

```python
select_cylinder(agent_required_kg, agent_type, system_type, catalog_df)
select_manifold_cylinders(agent_required_kg, agent_type, catalog_df)
validate_forced_cylinder(...)
```

### `src/bom/bom_builder.py`

Funciones:

```python
build_system_bom(room, result, selected_cylinder, catalog_df)
build_optional_bom(...)
```

### `src/bom/reserve_builder.py`

Funciones:

```python
build_reserve_bom(room, selected_cylinder, catalog_df, rules)
```

### `src/bom/main_reserve_builder.py`

Funciones:

```python
build_main_reserve_bom(room, selected_cylinder, catalog_df, rules)
```

### `src/exporters/excel_exporter.py`

Funciones:

```python
export_quote_to_excel(project_info, rooms_df, results_df, bom_detail_df, bom_consolidated_df) -> bytes
```

## UI recomendada

### Sidebar

- Datos del proyecto.
- Botón cargar catálogos.
- Parámetros generales.

### Main

Tabs:

1. `Proyecto`
2. `Salas`
3. `Configuración`
4. `Resultados técnicos`
5. `BOM`
6. `Exportar`

## Estado de sesión Streamlit

Usar `st.session_state` para:

- `project_info`
- `rooms_df`
- `system_configs`
- `calculation_results`
- `bom_detail_df`
- `bom_consolidated_df`

## Exportación

Usar `BytesIO` para descargar sin escribir obligatorio a disco.

```python
st.download_button(
    label="Descargar BOM Excel",
    data=excel_bytes,
    file_name=file_name,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
```
