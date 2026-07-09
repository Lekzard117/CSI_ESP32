# Interfaz de Comunicación ESP32 → Flask

## Overview

Definición de la interfaz de comunicación serial entre el firmware ESP32-CSI-Tool y el
servidor Flask. La interfaz transporta datos CSI capturados por el ESP32 (en roles
active_ap o passive) hacia el servidor de borde para procesamiento y detección de
movimiento.

La interfaz cubre: capa física UART, formato de datos, protocolo de línea, detección
de roles según el tipo de flasheo, y manejo de errores.

## Domain Language

| Término | Definición |
|---------|------------|
| UART | Universal Asynchronous Receiver-Transmitter, capa física RS-232 a 3.3V |
| 921600 baud | Tasa de transmisión serial entre ESP32 y servidor de borde |
| Línea CSI | Una línea CSV completa terminada en `\n` con prefijo `CSI_DATA` |
| Streaming | Flujo continuo de líneas CSI sin delimitación de paquete |
| tipo de flasheo | Rol de firmware flasheado en el ESP32: active_sta, active_ap o passive |

## Arquitectura de comunicación

```
┌──────────────┐    UART 921600 baud     ┌──────────────────┐
│  ESP32       │ ──────────────────────> │  Servidor Flask  │
│  active_ap   │    CSV streaming        │  (PC/servidor)   │
│  o passive   │                         │                  │
└──────────────┘                         └──────────────────┘
       │                                         │
       │ TX: GPIO1 (UART0)                       │ RX: Puerto serial
       │ Formato: 8N1                            │ Buffer: línea por línea
       │ Sin control de flujo                    │ Encoding: UTF-8
```

### Capa física (UART)

| Parámetro | Valor |
|-----------|-------|
| Protocolo | UART 8N1 (8 bits, sin paridad, 1 stop) |
| Baud rate | 921600 |
| Voltaje | 3.3V TTL |
| Pin TX (ESP32) | GPIO1 (TXD0) |
| Control de flujo | Sin control de flujo hardware/software |
| Delimitador de línea | `\n` (0x0A) |
| Encoding | ASCII/UTF-8 (solo caracteres imprimibles + coma + signo) |

### Formato de datos

Cada línea CSI sigue el formato:

```
CSI_DATA,<role>,<mac>,<rssi>,<rate>,<sig_mode>,<mcs>,<bandwidth>,<smoothing>,<not_sounding>,<aggregation>,<stbc>,<fec_coding>,<sgi>,<noise_floor>,<ampdu_cnt>,<channel>,<secondary_channel>,<local_timestamp>,<ant>,<sig_len>,<rx_state>,<real_time_set>,<real_timestamp>,<len>,[<I0> <Q0> <I1> <Q1> ...]
```

Los 25 primeros campos son metadatos separados por coma. El campo 26 contiene los
valores I/Q interleaved **entre corchetes `[...]` y separados por espacio**, NO por coma.
El formato exacto está definido en `_components/csi_component.h:27-79` del firmware.

Ejemplo real de línea:
```
CSI_DATA,AP,AA:BB:CC:DD:EE:FF,-65,1,0,1,1,0,0,0,0,-90,0,6,0,12345678,0,100,0,1,1712345678.500,128,[12 -5 34 -8 ...]
```

### Comportamiento por tipo de flasheo

| Rol | ¿Transmite por UART? | Campo `role` en CSV | Notas |
|-----|---------------------|---------------------|-------|
| active_sta | No | STA | Solo transmite WiFi; no conectado por UART al servidor |
| active_ap | Sí | AP | Captura CSI de estaciones conectadas; envía por serial |
| passive | Sí | PASSIVE | Captura CSI en modo promiscuo; envía por serial |

El servidor Flask debe identificar el rol mediante el campo `role` (posición 2) de
cada línea CSI para determinar el contexto de captura.

### Comandos de control (host → ESP32)

El servidor Flask puede enviar comandos de control al ESP32 por la misma UART:

| Comando | Descripción |
|---------|-------------|
| `SETTIME:<unix_seconds>\n` | Sincroniza el reloj del ESP32 con timestamp Unix |
| `RESET\n` | Reinicia el ESP32 vía software |

La respuesta del ESP32 a estos comandos es asíncrona (no hay protocolo ACK/NACK).

### Manejo de errores

| Escenario | Comportamiento |
|-----------|----------------|
| Línea malformada | Descartar línea, registrar error, continuar streaming |
| Buffer saturado | Pérdida de paquetes; el ESP32 no reintenta ni bloquea |
| Desconexión UART | El servidor detecta timeout y reinicia el puerto serial |
| GPIO1 dañado (TX) | No hay comunicación; el servidor reporta puerto muerto |
| Línea vacía | Ignorar (posible ruido eléctrico durante conexión) |

## Functional Requirements

| ID | Description | Status |
|----|-------------|--------|
| FR-001 | El ESP32 (active_ap/passive) debe transmitir datos CSI por UART a 921600 baud en formato 8N1 | Proposed |
| FR-002 | Cada línea CSI debe terminar con `\n` (0x0A) como delimitador de línea | Proposed |
| FR-003 | El formato de las líneas CSI debe ser CSV con prefijo `CSI_DATA` y los 26 campos definidos | Proposed |
| FR-004 | El servidor Flask debe poder leer el puerto serial y reconstruir líneas a partir del delimitador `\n` | Proposed |
| FR-005 | El servidor Flask debe identificar el rol del ESP32 mediante el campo `role` (posición 2) de cada línea | Proposed |
| FR-006 | El servidor Flask debe descartar líneas malformadas sin interrumpir el streaming | Proposed |
| FR-007 | El servidor Flask debe soportar el envío del comando `SETTIME:<unix_seconds>` por UART | Proposed |
| FR-008 | El servidor Flask debe detectar y reportar desconexión del puerto serial | Proposed |
| FR-009 | El formato y la tasa de transmisión deben ser consistentes entre los roles active_ap y passive | Proposed |

## Non-Functional Requirements

| ID | Description | Threshold | Status |
|----|-------------|-----------|--------|
| NFR-001 | La tasa de transmisión serial debe ser 921600 baud | ≥ 921600 | Proposed |
| NFR-002 | El buffer de lectura del servidor debe manejar al menos 4096 bytes por lectura | ≥ 4096 bytes | Proposed |
| NFR-003 | La pérdida de paquetes por saturación de buffer no debe causar bloqueo del ESP32 | Sin bloqueo | Proposed |

## Constraints

| ID | Description | Status |
|----|-------------|--------|
| C-001 | El ESP32 usa UART0 (GPIO1 TX, GPIO3 RX) para comunicación serial | Proposed |
| C-002 | No hay control de flujo hardware (RTS/CTS) disponible | Proposed |
| C-003 | El formato de línea CSI está definido por el firmware ESP32-CSI-Tool y no es configurable por el servidor | Proposed |

## Deliverables

| ID | Description | Status |
|----|-------------|--------|
| DD-001 | Diagrama de secuencia del flujo de datos: ESP32 → UART → Flask | Proposed |
| DD-002 | Especificación del protocolo de línea (formato CSV, campos, delimitadores) | Proposed |
| DD-003 | Código Python de ejemplo para lectura y parseo del puerto serial | Proposed |

## Key Entities

- **Línea CSI**: Unidad de datos, una línea CSV completa con prefijo CSI_DATA
- **Streaming UART**: Flujo continuo de bytes en el puerto serial
- **Role Tag**: Identificador del tipo de flasheo (AP, PASSIVE, STA) en cada línea
- **Buffer de línea**: Acumulador de bytes hasta encontrar `\n`
- **Comando de control**: Mensaje del servidor al ESP32 (SETTIME, RESET)
