# 09 — Diccionario de datos

## Hoja Excel: BDD_SISTEMAS- MANIFOLD

Uso: catálogo base para construir BOM.

| Columna original | Nombre normalizado | Descripción |
|---|---|---|
| id | id | Identificador de fila |
| KEY | key | Llave compuesta histórica |
| IN | enabled | Indica si el ítem está activo/incluido |
| TIPO | bom_type | Tipo de ítem o configuración |
| CILINDRO | cylinder_label | Tamaño de cilindro |
| AGENTE | agent_type | FM-200 o FK-5-1-12 |
| Ítem | item_order | Orden del ítem |
| Marca | brand | Marca |
| Codigo | code | Código comercial |
| Producto | product | Descripción del producto |
| U/M | unit | Unidad de medida |
| Cant. | quantity_base | Cantidad base |
| Entrega | delivery | Entrega o referencia logística |
| Precio | unit_price | Precio unitario |

## Hoja Excel: tabla_temperatura

Uso: referencia para flooding factors por agente, concentración y temperatura.

Normalización deseada:

| Campo | Descripción |
|---|---|
| agent_type | FM-200 / FK-5-1-12 |
| temperature_c | Temperatura °C |
| temperature_f | Temperatura °F |
| concentration_pct | Concentración de diseño |
| flooding_factor_metric | Factor en unidad métrica |
| flooding_factor_imperial | Factor en unidad imperial |

## Catálogo cilindros procesado

Archivo objetivo: `data/processed/cylinder_catalog.csv`

| Campo | Descripción |
|---|---|
| agent_type | Agente compatible |
| cylinder_label | Ej: TANK SIZE 52L |
| cylinder_code | Código del cilindro |
| size_l | Tamaño nominal en litros |
| min_fill_kg | Llenado mínimo kg |
| max_fill_kg | Llenado máximo kg |
| valve_size_mm | Tamaño de válvula |
| source | Fuente del dato |
| active | Activo/inactivo |

## Catálogo BOM procesado

Archivo objetivo: `data/processed/bom_catalog.csv`

| Campo | Descripción |
|---|---|
| id | ID |
| key | Llave histórica |
| enabled | Activo |
| bom_type | Tipo BOM |
| cylinder_label | Cilindro |
| agent_type | Agente |
| item_order | Orden |
| brand | Marca |
| code | Código |
| product | Producto |
| unit | Unidad |
| quantity_base | Cantidad base |
| delivery | Entrega |
| unit_price | Precio |

## Catálogo factores de altitud

Archivo objetivo: `data/processed/altitude_factors.csv`

| Campo | Descripción |
|---|---|
| altitude_m | Altitud msnm |
| altitude_ft | Altitud pies |
| correction_factor | Factor de corrección |
| source | Fuente |

## Catálogo opcionales

Archivo objetivo: `data/processed/optional_items.csv`

| Campo | Descripción |
|---|---|
| option_id | ID opcional |
| agent_type | Agente |
| system_type | Sistema |
| category | Categoría |
| code | Código |
| product | Producto |
| unit | Unidad |
| default_qty | Cantidad sugerida |
| selected_by_default | Seleccionado por defecto |
| notes | Notas |
