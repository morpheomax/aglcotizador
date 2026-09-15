# PROJECT_GRAPH - Memoria operativa para retomar

Este archivo resume el estado real del proyecto. No reemplaza `AGENTS.md`, `DECISIONS.md` ni la documentacion de `docs/`.

## Nodo raiz

`Cotizador Supresion FK-5-1-12 / FM-200`

Objetivo actual: consolidar una aplicacion Streamlit profesional, simple de operar y tecnicamente trazable para cotizacion y pre-dimensionamiento. React/FastAPI queda como evolucion posterior; el motor Python seguira siendo la autoridad unica.

## Reglas invariantes

- `app.py` solo inicia la aplicacion.
- Formulas y validaciones tecnicas: `src/engine/`.
- Reglas BOM: `src/bom/`.
- Exportaciones: `src/exporters/`.
- Modelos tipados: `src/models/`.
- Catalogos mantenibles: `data/raw/` y `data/processed/`.
- Precios nunca hardcodeados en el motor.
- Decisiones tecnicas y de producto: `DECISIONS.md`.
- El resultado es preliminar y no reemplaza calculo hidraulico certificado.

## Grafo de dependencias

```txt
Manuales ANSUL FM-200 y FK-5-1-12
    -> formulas y dominios de agente
    -> factores NFPA de altitud
    -> limites DOT welded
    -> cobertura preliminar de boquillas
    -> src/engine/* + data/processed/* + tests/*

data/processed/flooding_factors.csv
    -> presencia/referencia de agentes
    -> src/engine/agent.py usa ecuaciones oficiales

data/processed/altitude_factors.csv
    -> src/engine/altitude.py

data/processed/cylinder_catalog.csv
    -> src/engine/cylinder_selector.py

data/processed/nozzle_coverage.csv
    -> src/engine/nozzles.py

data/processed/bom_catalog.csv + optional_items.csv
    -> src/bom/bom_builder.py
    -> src/bom/consolidator.py

src/models/*
    -> src/engine/*
    -> src/bom/*
    -> src/exporters/*
    -> src/ui/*

src/engine/calculator.py
    -> calculo independiente de requerimientos por sala
    -> seleccion/validacion posterior de cilindros

src/ui/main.py + src/ui/rooms_editor.py
    -> flujo Streamlit por sala
    -> resultados, BOM y descarga Excel

src/exporters/excel_exporter.py
    -> XLSX con resumen, salas, resultados, cilindros, BOM y advertencias
```

## Estado tecnico actual

- FM-200: `S = 0.1269 + 0.0005131T`.
- FK-5-1-12: `S = 0.0664 + 0.000274T`.
- Ambos agentes: `W/V = (1/S) * (C/(100-C))`.
- Entradas fuera del dominio publicado se rechazan sin extrapolacion silenciosa.
- Altitud gobernada por tabla NFPA 2001, factor `1.0` entre `-914 m` y `+914 m`, interpolacion lineal sobre puntos publicados y rechazo fuera del dominio disponible.
- Catalogo DOT welded actualizado para cilindros de 8, 16, 32, 52, 106, 147, 180 y 343 L.
- El selector nunca devuelve llenados fuera del minimo/maximo.
- El selector enumera configuraciones validas de uno o varios cilindros iguales para que la UI permita elegir una alternativa.
- El calculo de agente queda disponible aunque la seleccion de cilindro requiera correccion.
- Cobertura preliminar estandar: FM-200 `95.3 m2/boquilla`; FK-5-1-12 `96 m2/boquilla`.
- La sala principal siempre se protege. Piso tecnico y cielo falso se incluyen solo por seleccion explicita y requieren altura positiva.
- Se conserva por separado minimo tecnico, recomendacion interna y cantidad final de boquillas.
- Politica interna: recomendar cantidad par, excepto tres boquillas cuando sala, piso y cielo requieren una cada uno.
- Override impar permitido solo con justificacion y nunca bajo el minimo tecnico.
- El BOM usa la cantidad final de boquillas y se bloquea si una sala incluida no tiene configuracion tecnica valida.
- Tiempo de descarga de 6 a 10 s, presion, caudal, tuberias y orificios quedan marcados para validacion hidraulica certificada.

## Estado UX/UI actual

- Flujo principal en tres tabs: salas, resultados y BOM.
- Salas con `room_id` estable; no dependen del nombre ni de la posicion.
- La grilla ancha y el flujo de marcar `Quitar` fueron reemplazados por tarjetas independientes.
- Cada tarjeta sigue cuatro pasos: identificacion, dimensiones, espacios adicionales y condiciones de diseno.
- Control explicito: `Incluir esta sala en el calculo, los totales y el BOM de la cotizacion`.
- Acciones directas: `Agregar sala`, `Guardar y calcular esta sala` y `Eliminar esta sala`.
- La sala agregada o guardada permanece abierta.
- Estados visibles: pendiente, calculada, requiere revision y no incluida.
- Resultado inmediato en la misma tarjeta: volumen protegido, agente kg/lb, flooding, altitud, boquillas y cilindro.
- Ajustes no habituales se agrupan en `Ajustes avanzados`.
- La UI solo muestra alternativas de cilindros generadas por el motor.
- Resultados consolidados, BOM y Excel siguen disponibles.

## Archivos clave

- `src/engine/agent.py`: ecuaciones y dominios de flooding.
- `src/engine/altitude.py`: banda neutra e interpolacion NFPA.
- `src/engine/cylinder_selector.py`: recomendacion, alternativas y validacion forzada.
- `src/engine/nozzles.py`: calculo por espacio y politica de recomendacion.
- `src/engine/calculator.py`: requerimientos por sala y wrapper compatible.
- `src/models/room.py`: entrada y resultado por sala.
- `src/models/nozzle.py`: resultados por espacio protegido.
- `src/ui/main.py`: composicion y flujo Streamlit.
- `src/ui/rooms_editor.py`: operaciones puras sobre la coleccion de salas.
- `src/bom/bom_builder.py`: cantidades BOM, incluida boquilla final.
- `data/processed/nozzle_coverage.csv`: cobertura y limite preliminar.
- `DECISIONS.md`: ADR-023 a ADR-028 describen la estabilizacion tecnica y UX reciente.

## Verificacion

- Ultima ejecucion: `python -m pytest -p no:cacheprovider`.
- Resultado: `53 passed in 1.82s`.
- Incluye regresiones de agente, altitud, cilindros, boquillas, BOM, exportacion y flujo real con `streamlit.testing`.
- Se probo guardar/calcular, aplicar otra configuracion de cilindros y eliminar una sala sin excepciones de Streamlit.

## Pendientes reales

- Realizar revision visual manual en escritorio y movil con el usuario.
- Validar una cotizacion completa contra software oficial/manual y una cotizacion comercial real.
- Validar descarga Excel con usuario final.
- Crear catalogo trazable de propiedades por agente y mapeo formal entre SKU comerciales y ensambles oficiales.
- Revisar y depurar catalogo de opcionales reales.
- Implementar reglas especificas de reserva y main reserve antes de generar esas lineas en BOM.
- Extraer un servicio de aplicacion independiente de Streamlit antes de una futura API FastAPI.

## Orden de retoma

1. Leer `AGENTS.md` y este archivo.
2. Ejecutar `python -m pytest -p no:cacheprovider`; baseline esperado: `53 passed`.
3. Iniciar la app con `python -m streamlit run app.py`.
4. Revisar manualmente el flujo con una sala FM-200 y una FK-5-1-12.
5. Probar agregar, guardar/calcular, excluir, cambiar cilindro y eliminar salas.
6. Probar piso tecnico y cielo falso protegidos, incluido el caso de tres boquillas.
7. Generar BOM y Excel; compararlos con un caso comercial real.
8. Registrar hallazgos UX o diferencias tecnicas antes de iniciar reserva/main reserve.

## Punto de cierre

- Sesion cerrada: `2026-09-13`.
- Punto exacto de retoma: revision visual/manual del nuevo flujo guiado y validacion end-to-end de una cotizacion real.
- No es repositorio Git en el entorno actual.
