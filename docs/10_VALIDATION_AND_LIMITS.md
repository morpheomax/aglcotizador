# 10 — Validaciones y límites

## Validaciones de entrada

- Cliente y proyecto no deben estar vacíos.
- Cada sala debe tener nombre único.
- Largo, ancho y alto deben ser mayores que cero.
- Altura de piso técnico y cielo falso no pueden ser negativas.
- Temperatura mínima no puede ser mayor que temperatura máxima.
- Concentración de diseño debe ser mayor que cero.
- Altitud debe permitir valores bajo o sobre nivel del mar.
- Reducciones no pueden superar volumen bruto.

## Validaciones técnicas

- Si no hay flooding factor, bloquear cálculo o marcar como advertencia crítica.
- Si no hay factor altitud, usar 1.0 solo con advertencia.
- Si el agente requerido supera la capacidad máxima del catálogo, advertir.
- Si el cilindro forzado no cumple llenado mínimo/máximo, bloquear o advertir según modo.
- Si manifold mezcla cilindros distintos, bloquear.
- Si la cantidad de boquillas manual es menor al mínimo calculado, bloquear.
- Si una cantidad manual impar no corresponde al caso de tres volúmenes con una boquilla cada uno, exigir justificación técnica.
- Si se superan 20 boquillas por recinto, exigir revisión para dividir el sistema o validar la configuración.

## Validaciones BOM

- Código vacío: advertencia.
- Precio vacío: permitido, pero total queda vacío y se advierte.
- Cantidad cero: excluir o advertir.
- Ítem duplicado con código igual y descripción distinta: advertencia.
- Ítem opcional no seleccionado: no entra en BOM final.

## Límites del MVP

- No calcula red hidráulica.
- No calcula caída de presión.
- No calcula tamaño real de tuberías.
- No valida ubicación física de boquillas.
- Muestra el requisito de descarga de 6 a 10 segundos, pero no certifica su cumplimiento sin cálculo hidráulico.
- No valida room integrity test.
- No reemplaza cálculo certificado.

## Mensaje de seguridad/compliance en UI

Mostrar al pie de resultados y exportación:

```txt
Este cálculo es preliminar para cotización. Debe ser revisado y validado por ingeniería mediante metodología/software certificado antes de usarlo para instalación o emisión final.
```
