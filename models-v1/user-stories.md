# User Stories — ESP32-CSI-Tool

## active_sta (Emisor)

### US-001: Transmisión periódica de paquetes
**Como** investigador,
**quiero** que el firmware `active_sta` transmita paquetes WiFi periódicamente en modo estación,
**para** generar tráfico medible que el receptor pueda capturar y extraer CSI.
> *Criterio:* Se conecta a un AP configurado y envía paquetes a intervalos regulares.
> (Ref: FR-001)

### US-002: Conexión automática al AP
**Como** investigador,
**quiero** que `active_sta` se conecte automáticamente al punto de acceso configurado,
**para** iniciar la transmisión sin intervención manual cada vez que se enciende.
> (Ref: FR-001)

---

## active_ap (Receptor AP)

### US-003: Captura de CSI como punto de acceso
**Como** investigador,
**quiero** que el firmware `active_ap` opere como punto de acceso WiFi y capture CSI de las estaciones que se conectan a él,
**para** obtener datos del estado del canal de las transmisiones entrantes.
> (Ref: FR-002)

### US-004: Transmisión serial de datos CSI
**Como** investigador,
**quiero** que `active_ap` transmita los datos CSI por serial UART a 921 600 baudios,
**para** enviarlos al servidor de borde en tiempo real sin pérdida significativa.
> (Ref: FR-005, NFR-001)

---

## passive (Monitor pasivo)

### US-005: Captura promiscua de CSI
**Como** investigador,
**quiero** que el firmware `passive` capture CSI en modo promiscuo de todos los paquetes en un canal,
**para** analizar tráfico WiFi existente sin necesidad de un emisor dedicado.
> (Ref: FR-003)

### US-006: Configuración de canal de monitoreo
**Como** investigador,
**quiero** configurar el canal WiFi a monitorear en el firmware `passive`,
**para** enfocar la captura en la banda de interés según el experimento.
> (Ref: FR-003)
