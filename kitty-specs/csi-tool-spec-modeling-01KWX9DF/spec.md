# ESP32-CSI-Tool: Specification and Modeling

## Overview

Especificación de la capa de firmware **ESP32-CSI-Tool** del sistema de detección de movimiento mediante CSI. Esta capa comprende tres roles de firmware para dispositivos ESP32:

- **active_sta**: Nodo emisor que transmite paquetes WiFi en modo estación conectado a un AP
- **active_ap**: Nodo receptor que opera como punto de acceso y captura CSI de estaciones conectadas
- **passive**: Nodo monitor que escucha pasivamente en modo promiscuo para capturar CSI

El alcance incluye la captura de CSI, transmisión serial de datos al servidor de borde, y los artefactos de documentación y modelado (C4, casos de uso, historias de usuario, diagramas de secuencia en PlantUML).

La capa de procesamiento de señales en el servidor Flask (compensación AGC, filtrado digital, sustracción de fondo, detección de movimiento) se especificará en misiones posteriores.

## Domain Language

| Término canónico | Sinónimos a evitar | Definición |
|---|---|---|
| Channel State Information (CSI) | — | Información del estado del canal WiFi que describe cómo se propagan las señales entre transmisor y receptor |
| active_sta | nodo TX, emisor | Firmware ESP32 que transmite paquetes en modo estación |
| active_ap | nodo RX, receptor AP | Firmware ESP32 que opera como AP y captura CSI de estaciones conectadas |
| passive | monitor pasivo | Firmware ESP32 que escucha en modo promiscuo sin asociarse a una red |
| subcarrier | subportadora | Cada una de las 52 o 114 portadoras individuales en una señal OFDM |
| SSNR | — | Relación señal-subportadora a ruido para identificar subportadoras informativas |
| 921600 baudios | — | Tasa de transmisión serial entre ESP32 y servidor de borde |

## User Scenarios

### Usuario investigador

**Actor principal**: Investigador académico

**Trigger**: El investigador necesita capturar datos CSI en un entorno controlado para analizar patrones de movimiento.

**Happy path**:
1. El investigador configura dos ESP32: uno como active_sta y otro como active_ap
2. Flashea ambos dispositivos con el firmware correspondiente
3. Conecta el active_ap al servidor de borde mediante UART a 921600 baudios
4. El active_ap captura CSI de los paquetes enviados por el active_sta
5. Los datos CSI se transmiten por serial en formato CSV con prefijo `CSI_DATA`
6. El investigador captura la salida serial a un archivo `.csv`

**Exception path — pérdida de paquetes**: Si el buffer serial se satura, algunos paquetes CSI se pierden; el sistema continúa transmitiendo sin bloqueo ni reintento.

### Usuario con monitor pasivo

**Actor principal**: Investigador académico

**Trigger**: El investigador quiere capturar tráfico CSI de dispositivos WiFi existentes sin un emisor dedicado.

**Happy path**:
1. El investigador flashea un ESP32 con el firmware passive
2. Configura el canal WiFi a monitorear
3. El ESP32 captura CSI en modo promiscuo de todos los paquetes en ese canal
4. Los datos se transmiten por serial de la misma forma que en active_ap

## Functional Requirements

| ID | Description | Status |
|---|---|---|
| FR-001 | El firmware active_sta debe transmitir paquetes WiFi periódicamente en modo estación, conectándose a un AP configurado | Approved |
| FR-002 | El firmware active_ap debe operar como punto de acceso WiFi, aceptar conexiones de estaciones y capturar CSI de los paquetes entrantes | Approved |
| FR-003 | El firmware passive debe capturar CSI en modo promiscuo de todos los paquetes en un canal configurado, sin asociarse a ninguna red | Approved |
| FR-004 | Cada línea CSI debe incluir: tipo, rol, MAC, RSSI, tasa, modo de señal, MCS, ancho de banda, timestamp local, número de antena, número de subportadoras y los valores complejos CSI | Approved |
| FR-005 | Los datos CSI deben transmitirse por serial UART a 921600 baudios en formato CSV con prefijo `CSI_DATA` por línea | Approved |
| FR-006 | El receptor (active_ap o passive) debe poder ser identificado por su dirección MAC en la salida CSI | Approved |
| FR-007 | El timestamp del AP debe difundirse automáticamente a las estaciones conectadas para sincronización | Approved |
| FR-008 | Se debe poder inyectar un timestamp manual mediante el comando `SETTIME:<unix_seconds>` desde el monitor serial | Approved |
| FR-009 | El script Python `serial_append_time.py` debe agregar timestamps de la PC local a cada línea CSI | Approved |
| FR-010 | El script Python `serial_plot_csi_live.py` debe graficar amplitud CSI en tiempo real desde la salida serial | Approved |

## Non-Functional Requirements

| ID | Description | Threshold | Status |
|---|---|---|---|
| NFR-001 | La transmisión serial debe operar a 921600 baudios con pérdida de paquetes aceptable sin bloqueo | ≥ 921600 baud | Approved |
| NFR-002 | El formato de salida CSV debe ser consistente entre los tres roles de firmware | Misma cabecera y orden de campos | Approved |
| NFR-003 | El firmware debe compilarse correctamente con ESP-IDF v6.0.1 sin errores | Compilación exitosa con `idf.py build` | Approved |
| NFR-004 | Los experimentos deben ser reproducibles: misma configuración de canal, tasa y entorno produce datos comparables | Mismos parámetros → misma estructura de datos | Approved |

## Constraints

| ID | Description | Status |
|---|---|---|
| C-001 | El firmware debe implementarse en C++ usando ESP-IDF v6.0.1 como framework de desarrollo | Approved |
| C-002 | Los roles de firmware están definidos por el repositorio fork `ESP32-CSI-Tool/` con su propio historial git | Approved |
| C-003 | Las utilidades Python deben usar numpy y matplotlib como dependencias | Approved |
| C-004 | La sincronización temporal puede hacerse mediante difusión del AP o comando serial manual | Approved |

## Documentation Deliverables

| ID | Description | Status |
|---|---|---|
| DD-001 | Diagrama C4 de contexto del sistema completo de 3 capas en PlantUML | Approved |
| DD-002 | Diagrama de casos de uso para los roles active_sta, active_ap y passive en PlantUML | Approved |
| DD-003 | Historias de usuario para cada rol de firmware en formato estándar | Approved |
| DD-004 | Diagramas de secuencia para el flujo de datos: emisor → receptor → serial en PlantUML | Approved |
| DD-005 | Modelo de requisitos CIM documentando la relación entre actores, casos de uso y componentes | Approved |

## Success Criteria

1. Los tres firmwares (active_sta, active_ap, passive) compilan correctamente con `idf.py build` en ESP-IDF v6.0.1
2. El active_ap captura y transmite líneas CSI_DATA por serial identificables por MAC
3. El active_sta se conecta al AP y genera tráfico CSI capturable
4. El passive captura CSI de dispositivos existentes en el canal configurado
5. Los scripts Python (`serial_append_time.py`, `serial_plot_csi_live.py`) procesan correctamente la salida serial
6. Todos los diagramas PlantUML se generan y representan correctamente la arquitectura y el flujo de datos

## Key Entities

- **Dispositivo ESP32**: Hardware objetivo, puede cumplir rol de active_sta, active_ap o passive
- **Paquete WiFi**: Unidad de transmisión que porta datos CSI en las subportadoras OFDM
- **CSI Data**: Conjunto de valores complejos (amplitud y fase) por subportadora, con metadatos (MAC, RSSI, timestamp)
- **Subcarrier**: Subportadora individual (52 o 114 según ancho de banda) con valor CSI complejo
- **Serial Stream**: Flujo de datos UART a 921600 baudios que transporta líneas CSV desde el ESP32 al servidor de borde

## Assumptions

- Los tres firmwares existen como fork del repositorio upstream ESP32-CSI-Tool y serán referenciados, no reescritos desde cero
- La corrección `esp_spi_flash.h` → `esp_flash.h` para IDF v6.0.1 ya fue aplicada en active_ap y passive, y debe verificarse en active_sta
- El servidor Flask y el pipeline de procesamiento de señales están excluidos de esta misión
- Los diagramas PlantUML se almacenarán en un directorio `diagrams/` dentro de la feature dir o en `DocLatex/`
