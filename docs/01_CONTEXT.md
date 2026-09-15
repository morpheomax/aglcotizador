# 01 — Contexto del proyecto

## Nombre del proyecto

Cotizador Supresión FK-5-1-12 / FM-200.

## Problema

Actualmente se utiliza un Excel para calcular y cotizar sistemas de supresión por agente limpio. El archivo es útil, pero se vuelve frágil cuando se requiere:

- Cotizar múltiples salas.
- Consolidar BOM.
- Manejar sistemas independientes.
- Manejar manifold.
- Activar o desactivar opcionales.
- Agregar reserva o main reserve sin duplicar costos incorrectamente.
- Generar un Excel final limpio con códigos, cantidades y precios.

## Objetivo general

Crear una aplicación Streamlit que simplifique el ingreso de datos, reduzca errores humanos y genere un BOM técnico-comercial descargable.

## Usuarios esperados

- Equipo comercial.
- Equipo técnico/comercial.
- Especialistas de sistemas de supresión.
- Analistas encargados de revisar costos, códigos y márgenes.

## Fuentes disponibles

### Excel base

Archivo: `calculo_supresion.xlsx`

Hojas detectadas:

- `CALC_AGENT`
- `INGRESO_DATOS_SALA`
- `BDD_SISTEMAS- MANIFOLD`
- `tabla_temperatura`
- `COT AGENTES`

Uso esperado:

- `CALC_AGENT`: referencia de lógica histórica de cálculo.
- `INGRESO_DATOS_SALA`: referencia de campos de entrada.
- `BDD_SISTEMAS- MANIFOLD`: base inicial de BOM, códigos, cantidades y precios.
- `tabla_temperatura`: referencia de flooding factors y factores por temperatura/concentración.
- `COT AGENTES`: referencia de estructura comercial y selección actual.

### Manual FM-200

Archivo: `PN442940-01 Manual 2022.pdf`

Uso:

- Referencia de diseño general.
- Componentes de sistema.
- Cilindros y restricciones.
- Manifold.
- Cálculo y procedimiento de diseño.

### Manual FK-5-1-12 / SAPPHIRE

Archivo: `pn451540-01 Manual FK 5-1-12 3.pdf`

Uso:

- Referencia de diseño general.
- Componentes de sistema.
- Cilindros FK-5-1-12.
- Manifold.
- Concentraciones y factores.

## Principio de diseño

La app debe ser simple para el usuario final, pero internamente rigurosa:

```txt
Entrada clara -> validación -> cálculo -> selección técnica -> BOM -> exportación
```

## Lo que no es el sistema

No es:

- Software certificado de cálculo hidráulico.
- Reemplazo de Jensen Hughes/ANSUL Design Calculation.
- Memoria de cálculo final aprobada.
- Sistema de detección de incendio.
- ERP.
- CRM.

Sí es:

- Cotizador técnico-comercial.
- Pre-dimensionador.
- Generador de BOM.
- Herramienta de estandarización interna.
