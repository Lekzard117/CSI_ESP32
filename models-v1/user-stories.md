# User Stories — ESP32-CSI-Tool

## active_sta (Emisor)

### US-001: Transmisión periódica de paquetes
**Como** investigador,
**quiero** que el firmware `active_sta` transmita paquetes WiFi periódicamente en modo estación,
**para** generar tráfico medible que el receptor pueda capturar y extraer CSI.
> *Criterio:* Se conecta a un AP configurado y envía paquetes a intervalos regulares.
> (Ref: FR-001)

### US-002: Conexión a red existente
**Como** investigador,
**quiero** que `active_sta` se conecte a un punto de acceso WiFi configurable,
**para** poder desplegar el emisor en redes preexistentes sin infraestructura adicional.
> (Ref: FR-001)

---

## active_ap (Receptor AP)

### US-003: Captura de CSI como punto de acceso
**Como** investigador,
**quiero** que el firmware `active_ap` opere como AP WiFi y capture CSI de las estaciones que se conectan a él,
**para** recolectar información del canal de las transmisiones entrantes sin hardware adicional.
> (Ref: FR-002)

### US-004: Formato completo de salida CSI
**Como** investigador,
**quiero** que cada línea CSI contenga los 26 campos del modelo de datos,
**para** disponer de metadatos completos (MAC, RSSI, timestamp, subportadoras) en el análisis posterior.
> (Ref: FR-004)

### US-005: Transmisión serial a alta velocidad
**Como** investigador,
**quiero** que los datos CSI se transmitan por UART a 921 600 baudios en formato CSV,
**para** minimizar la pérdida de paquetes durante la captura en tiempo real.
> (Ref: FR-005, NFR-001)

### US-006: Identificación por MAC
**Como** investigador,
**quiero** que la dirección MAC del receptor se incluya en cada línea CSI,
**para** distinguir entre múltiples dispositivos en experimentos con varios nodos.
> (Ref: FR-006)

### US-007: Sincronización temporal automática
**Como** investigador,
**quiero** que el AP difunda su timestamp automáticamente a las estaciones conectadas,
**para** mantener sincronizados los relojes sin intervención manual.
> (Ref: FR-007)

### US-008: Timestamp manual por serial
**Como** investigador,
**quiero** poder inyectar un timestamp manual mediante el comando `SETTIME:<unix_seconds>`,
**para** alinear la línea de tiempo del ESP32 con el reloj de la PC en experimentos controlados.
> (Ref: FR-008)

---

## passive (Monitor pasivo)

### US-009: Captura promiscua de CSI
**Como** investigador,
**quiero** que el firmware `passive` capture CSI de todos los paquetes en un canal configurado sin asociarse a ninguna red,
**para** analizar tráfico WiFi existente sin necesidad de un emisor dedicado.
> (Ref: FR-003)

---

## Utilidades Python (procesamiento serial)

### US-010: Timestamp de PC en línea CSI
**Como** investigador,
**quiero** que el script `serial_append_time.py` añada el timestamp de la PC local a cada línea CSI,
**para** correlacionar los datos capturados con eventos temporales externos.
> (Ref: FR-009)

### US-011: Visualización en vivo de amplitud
**Como** investigador,
**quiero** que el script `serial_plot_csi_live.py` grafique la amplitud CSI en tiempo real,
**para** verificar visualmente que la captura está funcionando durante el experimento.
> (Ref: FR-010)

---

## Criterios de aceptación transversales

- Los tres firmwares deben compilar correctamente con `idf.py build` en ESP-IDF v6.0.1. (Ref: NFR-003)
- El formato de salida CSV debe ser idéntico en los roles `active_ap` y `passive`. (Ref: NFR-002)
- La configuración idéntica de canal y tasa debe producir datos comparables entre experimentos. (Ref: NFR-004)
