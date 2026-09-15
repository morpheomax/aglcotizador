# 02 — Product Requirements Document

## Objetivo del MVP

Construir una app Streamlit funcional para cotizar sistemas de supresión FM-200 y FK-5-1-12 con descarga de BOM en Excel.

## Funcionalidades MVP v0.1

### 1. Datos generales del proyecto

Campos:

- Cliente.
- Proyecto.
- País.
- Ciudad.
- Altitud base msnm.
- Moneda.
- Vendedor/responsable.
- Fecha.
- Observaciones.

### 2. Ingreso de salas

Debe permitir ingresar múltiples salas mediante tabla editable o formulario dinámico.

Campos por sala:

- Nombre de sala.
- Agente: `FM-200` o `FK-5-1-12`.
- Largo m.
- Ancho m.
- Alto m.
- Altura piso técnico m.
- Altura cielo falso m.
- Reducciones estructurales m³.
- Reducciones por objetos m³.
- Temperatura mínima °C.
- Temperatura máxima °C.
- Temperatura normal °C.
- Concentración de diseño %.
- Altitud msnm.
- Notas técnicas.

### 3. Configuración de sistema por sala

Campos:

- Tipo de sistema: `SISTEMA`, `MANIFOLD`.
- Conexión descarga: `FLEXIBLE`, `HARDPIPE`.
- Reserva: `Sí/No`.
- Main reserve: `Sí/No`.
- Usar opcionales: `Sí/No`.
- Forzar cilindro: `Sí/No`.
- Cilindro forzado.
- Cantidad de cilindros forzada.
- Boquillas manuales: `Sí/No`.
- Cantidad de boquillas manual.

### 4. Resultado técnico por sala

Mostrar:

- Área m².
- Volumen sala m³.
- Volumen piso técnico m³.
- Volumen cielo falso m³.
- Volumen bruto m³.
- Volumen neto m³.
- Flooding factor usado.
- Factor altitud usado.
- Kg o lb de agente requerido.
- Cilindro recomendado.
- Cantidad de cilindros.
- Boquillas mínimas.
- Advertencias técnicas.

### 5. BOM detallado

Generar tabla con:

- Sistema.
- Sala.
- Tipo BOM.
- Agente.
- Cilindro.
- Marca.
- Código.
- Producto.
- Unidad de medida.
- Cantidad.
- Precio unitario.
- Total.
- Entrega.
- Seleccionado.
- Observación.

### 6. BOM consolidado

Agrupar por:

- Código.
- Producto.
- U/M.
- Precio unitario.

Sumar:

- Cantidad.
- Total.

### 7. Exportación Excel

Botón de descarga:

- `cotizacion_supresion_<cliente>_<fecha>.xlsx`

Hojas mínimas:

- `Resumen`
- `Salas`
- `Resultados_Tecnicos`
- `BOM_Detalle`
- `BOM_Consolidado`
- `Advertencias`

## Funcionalidades v0.2

- Selección avanzada de opcionales.
- Modo reserva configurable por categoría.
- Main reserve con exclusiones.
- Carga externa de precios.
- Plantilla visual de Excel.

## Funcionalidades v0.3

- Guardado local en SQLite.
- Historial de cotizaciones.
- Copiar proyecto.
- Versionamiento de cotizaciones.
- Importar salas desde Excel.

## Funcionalidades fuera del MVP

- Login multiusuario.
- Integración CRM/ERP.
- Control de stock en línea.
- Generación de PDF formal.
- Web app Astro/React.
