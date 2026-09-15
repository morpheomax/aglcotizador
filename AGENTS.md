# AGENTS.md — Instrucciones para OpenCode

## Rol del agente

Actúa como desarrollador senior Python especializado en aplicaciones de cálculo técnico-comercial, Streamlit, Pandas, Excel export, arquitectura modular y pruebas unitarias.

## Objetivo del proyecto

Construir una app Streamlit para cotizar sistemas de supresión por agente limpio FK-5-1-12 y FM-200, con múltiples salas, selección preliminar de cilindros, configuración de sistema, opcionales, reserva, main reserve y descarga de BOM en Excel.

## Reglas obligatorias

1. No mezclar lógica de cálculo dentro de `app.py`.
2. Toda fórmula técnica debe vivir en `src/engine/`.
3. Toda regla de BOM debe vivir en `src/bom/`.
4. Toda exportación debe vivir en `src/exporters/`.
5. Validar entradas antes de calcular.
6. Usar tipos explícitos y modelos Pydantic o dataclasses.
7. Crear tests unitarios para cálculos base, selección de cilindros y BOM.
8. Mantener los catálogos en archivos externos CSV/XLSX para facilitar mantenimiento comercial.
9. Nunca hardcodear precios en el motor.
10. Documentar cada decisión técnica en `DECISIONS.md`.

## Estilo de código

- Python 3.11+.
- Type hints obligatorios en funciones principales.
- Funciones pequeñas y testeables.
- Nombres claros en inglés para código: `RoomInput`, `AgentType`, `CylinderOption`, `BomItem`.
- UI en español.
- Mensajes de validación en español.

## Arquitectura esperada

```txt
cotizador_supresion/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── templates/
├── src/
│   ├── engine/
│   ├── bom/
│   ├── data/
│   ├── exporters/
│   ├── models/
│   └── ui/
└── tests/
```

## Definición de terminado del MVP

El MVP se considera funcional cuando:

- Permite ingresar al menos 1 sala y varias salas.
- Calcula volumen total por sala.
- Calcula agente requerido usando flooding factor desde catálogo.
- Aplica corrección por altitud desde catálogo.
- Selecciona cilindro válido preliminarmente.
- Genera BOM por sala.
- Consolida BOM total por código.
- Descarga Excel con hojas `Resumen`, `Salas`, `BOM_Detalle`, `BOM_Consolidado`.
- Tiene tests mínimos ejecutables con `pytest`.

## Restricción técnica importante

El resultado es de cotización/pre-dimensionamiento. No afirmar que reemplaza el cálculo hidráulico final ni diseño certificado.
