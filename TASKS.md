# TASKS — Cotizador Supresión

## Backlog MVP v0.1

### Setup

- [x] Crear estructura de carpetas.
- [ ] Crear entorno virtual.
- [x] Crear `requirements.txt`.
- [x] Copiar `calculo_supresion.xlsx` a `data/raw/`.
- [x] Crear `app.py` mínimo.

### Continuidad del proyecto

- [x] Crear `PROJECT_GRAPH.md` como memoria operativa para retomar.
- [x] Actualizar `README.md` técnico.

### Modelos

- [x] Crear modelos de proyecto.
- [x] Crear modelos de sala.
- [x] Crear modelos de configuración.
- [x] Crear modelos de cilindro.
- [x] Crear modelos de BOM.

### Cálculo técnico

- [x] Calcular área.
- [x] Calcular volumen sala.
- [x] Calcular piso técnico.
- [x] Calcular cielo falso.
- [x] Calcular volumen bruto.
- [x] Calcular volumen neto.
- [x] Leer flooding factor.
- [x] Aplicar factor altitud.
- [x] Redondear agente.
- [x] Calcular boquillas mínimas.

### Revalidación técnica prioritaria

- [x] Identificar fórmulas oficiales en manuales FM-200 y FK-5-1-12.
- [x] Elegir NFPA 2001 como norma gobernante del MVP.
- [x] Definir factor 1.0 en la banda opcional de -914 m a +914 m.
- [x] Crear pruebas de regresión para fórmulas oficiales de flooding.
- [x] Crear pruebas de regresión para tabla e interpolación NFPA de altitud.
- [x] Sustituir lookup por escalón por cálculo oficial de flooding.
- [x] Reemplazar catálogo provisional de altitud.
- [x] Validar rangos operativos de temperatura y concentración.
- [x] Rechazar entradas fuera del dominio técnico documentado.

### Catálogos

- [x] Leer Excel base.
- [x] Normalizar `BDD_SISTEMAS- MANIFOLD`.
- [x] Crear catálogo BOM procesado.
- [x] Crear catálogo cilindros.
- [x] Crear catálogo flooding factors.
- [x] Crear catálogo factores altitud.
- [ ] Validar catálogos procesados contra Excel/manuales con casos reales.
- [ ] Crear catálogo trazable de propiedades técnicas por agente.
- [ ] Mapear SKU comerciales a ensambles oficiales DOT welded.
- [x] Corregir límites mínimo/máximo de cilindros según manuales.

### Selector de cilindros

- [x] Selección simple.
- [x] Selección manifold.
- [x] Validación de cilindro forzado.
- [x] Advertencias.
- [x] Eliminar fallback que devuelve cilindros fuera de rango.
- [x] Reemplazar preview UI por alternativas generadas y validadas por el motor.
- [x] Probar límites exactos y ausencia de combinación válida.

### BOM

- [x] BOM sistema base.
- [x] BOM opcionales.
- [ ] BOM reserva.
- [ ] BOM main reserve.
- [x] Consolidación por código.

### UI

- [x] Datos proyecto.
- [x] Editor de salas.
- [x] Configuración por sala.
- [x] Resultados técnicos.
- [x] BOM detalle.
- [x] BOM consolidado.
- [x] Advertencias.
- [x] Selección manual de cilindro.
- [x] Previsualización de alternativas de cilindro.
- [x] Identidad estable y eliminación directa por sala.
- [x] Guardar y calcular con resultado inmediato por sala.
- [x] Selección de configuraciones válidas de uno o varios cilindros.
- [x] Selección explícita de piso técnico y cielo falso protegidos.
- [x] Política recomendada de boquillas pares con excepción de tres volúmenes.
- [x] Override de boquillas con validación y justificación para impares.

### Validación contra casos reales

- [x] Caso FK-5-1-12 pequeño con cilindro 16L.
- [x] Caso FM-200 pequeño con cilindro 16L.
- [ ] Validar BOM completo contra cotización real.
- [ ] Validar descarga Excel con usuario final.

### Exportación

- [x] Exportar Excel.
- [x] Formatear hojas.
- [x] Botón descarga.

### Tests

- [x] Tests volumen.
- [x] Tests agente.
- [x] Tests cilindros.
- [x] Tests BOM.
- [x] Tests exportación.
- [x] Tests de boquillas y flujo Streamlit.

## Pendientes post-MVP

- [ ] Historial SQLite.
- [ ] PDF comercial.
- [ ] Carga de precios desde archivo externo.
- [ ] Integración CRM/ERP.
- [ ] Extraer servicio de aplicación independiente de Streamlit.
- [ ] Implementar API FastAPI versionada.
- [ ] Implementar SPA React/TypeScript responsive.
- [ ] Definir autenticación y despliegue privado.
