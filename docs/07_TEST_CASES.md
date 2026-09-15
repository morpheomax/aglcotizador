# 07 — Casos de prueba

## Objetivo

Definir pruebas mínimas para asegurar que el motor calcula consistentemente y no rompe reglas comerciales.

## Test 1 — Volumen simple

Entrada:

```txt
Largo: 10 m
Ancho: 5 m
Alto: 3 m
Piso técnico: 0 m
Cielo falso: 0 m
Reducciones: 0 m³
```

Esperado:

```txt
Área: 50 m²
Volumen sala: 150 m³
Volumen bruto: 150 m³
Volumen neto: 150 m³
```

## Test 2 — Volumen con piso técnico y cielo falso

Entrada:

```txt
Largo: 10 m
Ancho: 5 m
Alto: 3 m
Piso técnico: 0.5 m
Cielo falso: 0.5 m
Reducciones: 0 m³
```

Esperado:

```txt
Área: 50 m²
Volumen sala: 150 m³
Volumen piso técnico: 25 m³
Volumen cielo falso: 25 m³
Volumen bruto: 200 m³
Volumen neto: 200 m³
```

## Test 3 — Reducciones válidas

Entrada:

```txt
Volumen bruto: 200 m³
Reducciones estructurales: 20 m³
Reducciones objetos: 10 m³
```

Esperado:

```txt
Volumen neto: 170 m³
```

## Test 4 — Reducciones inválidas

Entrada:

```txt
Volumen bruto: 100 m³
Reducciones totales: 120 m³
```

Esperado:

```txt
Error de validación: las reducciones no pueden superar el volumen bruto.
```

## Test 5 — Agente requerido

Entrada:

```txt
Volumen neto: 100 m³
Flooding factor: 0.65 kg/m³
Factor altitud: 1.00
```

Esperado:

```txt
Agente exacto: 65 kg
```

## Test 6 — Corrección altitud

Entrada:

```txt
Agente base: 65 kg
Factor altitud: 1.05
```

Esperado:

```txt
Agente corregido: 68.25 kg
```

## Test 7 — Selección cilindro simple

Catálogo:

```txt
Cilindro A: min 10 kg, max 50 kg
Cilindro B: min 40 kg, max 100 kg
```

Entrada:

```txt
Agente requerido: 68 kg
```

Esperado:

```txt
Selecciona Cilindro B.
```

## Test 8 — Selección manifold con cilindros iguales

Catálogo:

```txt
Cilindro A: min 10 kg, max 50 kg
Cilindro B: min 40 kg, max 100 kg
```

Entrada:

```txt
Agente requerido: 180 kg
Sistema: MANIFOLD
```

Esperado:

```txt
2 x Cilindro B con 90 kg cada uno
```

## Test 9 — BOM base

Entrada:

```txt
Agente: FK-5-1-12
Cilindro: TANK SIZE 52L
Tipo: SISTEMA
Cantidad cilindros: 1
```

Esperado:

```txt
BOM contiene ítems filtrados por FK-5-1-12 + TANK SIZE 52L + SISTEMA.
```

## Test 10 — BOM reserva

Entrada:

```txt
Reserva: Sí
Cilindro: TANK SIZE 52L
```

Esperado:

```txt
BOM reserva incluye cilindro, agente, carga y componentes mínimos definidos.
No duplica boquillas ni descarga salvo regla explícita.
```

## Test 11 — Consolidación BOM

Entrada:

```txt
BOM detalle:
Código A, cantidad 1
Código A, cantidad 2
Código B, cantidad 1
```

Esperado:

```txt
Código A, cantidad 3
Código B, cantidad 1
```

## Test 12 — Exportación

Entrada:

```txt
Proyecto con 2 salas y BOM generado.
```

Esperado:

```txt
Excel descargable con hojas mínimas y sin errores.
```
