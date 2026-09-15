# 03 — Reglas técnicas y comerciales

## 1. Alcance técnico

La aplicación calcula un pre-dimensionamiento comercial. No reemplaza el cálculo hidráulico final ni la aprobación técnica del fabricante.

## 2. Agentes soportados

```python
AgentType = Literal["FM-200", "FK-5-1-12"]
```

## 3. Cálculo de volumen

Por sala:

```txt
area_m2 = largo_m * ancho_m
volumen_sala_m3 = largo_m * ancho_m * alto_m
volumen_piso_tecnico_m3 = largo_m * ancho_m * altura_piso_tecnico_m
volumen_cielo_falso_m3 = largo_m * ancho_m * altura_cielo_falso_m
volumen_bruto_m3 = volumen_sala_m3 + volumen_piso_tecnico_m3 + volumen_cielo_falso_m3
volumen_neto_m3 = volumen_bruto_m3 - reducciones_estructurales_m3 - reducciones_objetos_m3
```

Validaciones:

- Largo, ancho y alto deben ser mayores que cero.
- Piso técnico y cielo falso pueden ser cero.
- Las reducciones no pueden superar el volumen bruto.
- El volumen neto debe ser mayor que cero.

## 4. Flooding factor

El flooding factor debe venir desde catálogo externo, idealmente normalizado desde `tabla_temperatura`.

Parámetros:

- Agente.
- Concentración de diseño.
- Temperatura mínima.
- Temperatura normal o de referencia.

Regla MVP:

```txt
agente_base = volumen_neto * flooding_factor
```

Unidad recomendada interna:

- Mantener cálculos internos en métrico.
- Exportar kg y lb cuando aplique.

## 5. Corrección por altitud

El factor de altitud debe venir desde catálogo externo.

Regla MVP:

```txt
agente_corregido = agente_base * factor_altitud
```

## 6. Redondeo de agente

Regla inicial:

- Redondear hacia arriba a 0.5 kg o unidad comercial definida.
- Mantener el valor exacto y el valor redondeado.

Campos:

- `agent_required_exact_kg`
- `agent_required_rounded_kg`

## 7. Selección preliminar de cilindro

El selector debe buscar cilindros compatibles con:

- Agente.
- Cantidad mínima de llenado.
- Cantidad máxima de llenado.
- Tipo de mercado si aplica.
- Tipo de sistema.

Regla:

```txt
cilindro válido si min_fill <= agente_por_cilindro <= max_fill
```

## 8. Selección para manifold

Regla crítica:

- Si el sistema usa manifold, todos los cilindros del mismo manifold deben ser del mismo tamaño y mismo llenado.
- No mezclar cilindros de distintos tamaños dentro del mismo manifold.

Algoritmo preliminar:

```txt
para cada tamaño de cilindro compatible:
    para n desde 1 hasta max_cylinders:
        agente_por_cilindro = agente_total / n
        si min_fill <= agente_por_cilindro <= max_fill:
            candidato válido
seleccionar candidato con menor exceso o menor costo futuro
```

## 9. Boquillas

MVP:

- Calcular boquillas mínimas por cobertura de área desde catálogo por agente.
- Permitir override manual.

Campos:

- `nozzle_coverage_m2`
- `nozzle_min_qty`
- `nozzle_qty_final`

## 10. BOM base

El BOM debe venir desde `BDD_SISTEMAS- MANIFOLD`, filtrando por:

- `TIPO`
- `CILINDRO`
- `AGENTE`

Columnas base detectadas:

```txt
id
KEY
IN
TIPO
CILINDRO
AGENTE
Ítem
Marca
Codigo
Producto
U/M
Cant.
Entrega
Precio
```

## 11. Categorías BOM

Categorías esperadas:

- `SISTEMA`
- `MANIFOLD`
- `SISTEMA MANIFOLD`
- `OPCIONAL`
- `RESERVA`
- `MAIN RESERVE`
- `SERVICIO`
- `AGENTE`
- `CILINDRO`

Nota: normalizar nombres para evitar diferencias como `-OPCIONAL`.

## 12. Opcionales

Cada opcional debe tener:

- Checkbox en UI.
- Cantidad editable.
- Descripción.
- Código.
- Precio futuro.
- Justificación o categoría.

## 13. Reserva

La reserva no debe duplicar automáticamente todo el sistema.

Regla inicial:

- Incluir cilindro.
- Incluir agente.
- Incluir servicio de carga.
- Incluir manómetro/label/LPS si está en catálogo.
- Excluir boquillas, descarga, actuadores y señalética salvo selección explícita.

## 14. Main reserve

Main reserve debe tener una configuración separada.

Regla inicial:

- Clonar parcialmente el sistema principal.
- Permitir exclusiones configurables.
- Permitir componentes específicos de manifold/conmutación.
- No duplicar opcionales salvo que el usuario lo seleccione.

## 15. Validaciones comerciales

Advertir si:

- Falta precio.
- Código vacío.
- Cantidad cero.
- Ítem repetido con distinta descripción.
- Cilindro no encontrado.
- Agente requerido excede capacidad disponible.
- Sistema con manifold mezcla cilindros distintos.

## 16. Advertencia técnica obligatoria

Cada export debe incluir una nota:

```txt
Cálculo preliminar para cotización. Debe ser validado mediante cálculo hidráulico/software certificado y revisión técnica antes de emisión final para instalación.
```
