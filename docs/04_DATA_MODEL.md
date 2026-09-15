# 04 — Modelo de datos

## Enumeraciones

```python
class AgentType(str, Enum):
    FM200 = "FM-200"
    FK5112 = "FK-5-1-12"

class SystemType(str, Enum):
    SYSTEM = "SISTEMA"
    MANIFOLD = "MANIFOLD"

class DischargeConnection(str, Enum):
    FLEXIBLE = "FLEXIBLE"
    HARDPIPE = "HARDPIPE"

class BomType(str, Enum):
    SYSTEM = "SISTEMA"
    OPTIONAL = "OPCIONAL"
    RESERVE = "RESERVA"
    MAIN_RESERVE = "MAIN RESERVE"
    MANIFOLD = "MANIFOLD"
```

## ProjectInfo

```python
@dataclass
class ProjectInfo:
    client: str
    project_name: str
    country: str
    city: str | None
    base_altitude_m: float
    currency: str
    seller: str | None
    quote_date: date
    notes: str | None = None
```

## RoomInput

```python
@dataclass
class RoomInput:
    room_id: str
    name: str
    agent_type: AgentType
    length_m: float
    width_m: float
    height_m: float
    raised_floor_m: float = 0.0
    false_ceiling_m: float = 0.0
    structural_reductions_m3: float = 0.0
    object_reductions_m3: float = 0.0
    min_temp_c: float = 18.0
    max_temp_c: float = 27.0
    normal_temp_c: float = 21.0
    design_concentration_pct: float = 0.0
    altitude_m: float = 0.0
    notes: str | None = None
```

## SystemConfig

```python
@dataclass
class SystemConfig:
    room_id: str
    system_type: SystemType = SystemType.SYSTEM
    discharge_connection: DischargeConnection = DischargeConnection.FLEXIBLE
    include_optional_items: bool = False
    include_reserve: bool = False
    include_main_reserve: bool = False
    force_cylinder: bool = False
    forced_cylinder_code: str | None = None
    forced_cylinder_qty: int | None = None
    override_nozzles: bool = False
    nozzle_qty_manual: int | None = None
```

## RoomCalculationResult

```python
@dataclass
class RoomCalculationResult:
    room_id: str
    area_m2: float
    volume_room_m3: float
    volume_raised_floor_m3: float
    volume_false_ceiling_m3: float
    gross_volume_m3: float
    net_volume_m3: float
    flooding_factor: float
    altitude_factor: float
    agent_required_exact_kg: float
    agent_required_rounded_kg: float
    nozzle_min_qty: int
    warnings: list[str]
```

## CylinderOption

```python
@dataclass
class CylinderOption:
    agent_type: AgentType
    cylinder_label: str
    cylinder_code: str
    size_l: float
    min_fill_kg: float
    max_fill_kg: float
    valve_size_mm: int | None
    source: str | None = None
```

## SelectedCylinder

```python
@dataclass
class SelectedCylinder:
    room_id: str
    cylinder: CylinderOption
    quantity: int
    fill_per_cylinder_kg: float
    total_fill_kg: float
    excess_kg: float
    is_forced: bool = False
    warnings: list[str] = field(default_factory=list)
```

## BomCatalogItem

```python
@dataclass
class BomCatalogItem:
    item_id: str | int
    key: str | None
    enabled: bool
    bom_type: str
    cylinder_label: str | None
    agent_type: AgentType | None
    item_order: int | None
    brand: str | None
    code: str
    product: str
    unit: str
    quantity_base: float
    delivery: str | None
    unit_price: float | None
```

## BomLine

```python
@dataclass
class BomLine:
    project_id: str | None
    room_id: str
    room_name: str
    system_type: str
    bom_type: str
    agent_type: AgentType
    cylinder_label: str | None
    brand: str | None
    code: str
    product: str
    unit: str
    quantity: float
    unit_price: float | None
    total_price: float | None
    delivery: str | None
    selected: bool = True
    notes: str | None = None
```

## DataFrames finales

### `rooms_df`

Una fila por sala ingresada.

### `results_df`

Una fila por sala calculada.

### `bom_detail_df`

Una fila por ítem por sala.

### `bom_consolidated_df`

Agrupado por código/producto/unidad/precio.
