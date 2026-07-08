# Implementation Plan: Interfaz de Comunicación ESP32 → Flask

**Branch**: `model-kitty-v1` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/kitty-specs/interfaz-comunicacion-esp32-flask-01KWZKM3/spec.md`

## Summary

Definir la interfaz de comunicación serial entre el firmware ESP32-CSI-Tool (active_ap,
passive) y el servidor Flask. La interfaz abarca la capa física UART a 921600 baud,
el formato CSV de las líneas CSI, el protocolo de streaming, la detección del rol
según el tipo de flasheo, y el manejo de errores. Se entregarán diagramas de
secuencia, especificación del protocolo y código Python de ejemplo.

## Technical Context

**Language/Version**: Python 3.11+ (Flask), C++ (ESP-IDF v6.0.1, firmware existente)
**Primary Dependencies**: pyserial (lectura de puerto serial), Flask (servidor web),
numpy (procesamiento de datos CSI)
**Storage**: Archivos .csv en disco durante captura; sin base de datos en esta fase
**Testing**: Verificación empírica conectando ESP32 físico; pruebas unitarias del
parser CSV con datos simulados
**Target Platform**: Linux (servidor de borde), ESP32 (firmware existente)
**Project Type**: web (backend Flask) + embedded (firmware ESP32 existente)
**Performance Goals**: Lectura de ≥1000 líneas CSI/segundo a 921600 baud; buffer de
4096 bytes sin bloqueo
**Constraints**: Sin control de flujo hardware; formato de línea fijado por firmware
ESP32-CSI-Tool; sin ACK en comandos de control
**Scale/Scope**: 1 puerto serial, 1 ESP32, streaming unidireccional (datos) +
comandos ocasionales (host → ESP32)

## Charter Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Risk boundaries | OK | Proyecto académico, sin producción |
| Documentation policy | OK | Documentación sincronizada con el código |
| Testing | OK | Verificación empírica + pruebas unitarias de parser |
| Review policy | OK | Por definirse |

Sin conflictos detectados entre el charter y el plan propuesto.

## Project Structure

### Documentation (this mission)

```
kitty-specs/interfaz-comunicacion-esp32-flask-01KWZKM3/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── contracts/           # Phase 1 — código Python de ejemplo
└── tasks.md             # Phase 2 (/spec-kitty.tasks)
```

### Source Code

```
src/flask_serial/
├── reader.py            # Lector de puerto serial
├── parser.py            # Parser de líneas CSI
├── commands.py          # Envío de comandos de control
└── models.py            # Modelos de datos CSI

tests/
├── test_parser.py       # Tests unitarios del parser CSV
└── test_reader.py       # Tests del lector serial (simulado)
```

**Structure Decision**: Proyecto Python simple con módulo `flask_serial/` y tests
unitarios. Sin estructura de backend completa porque esta capa es un middleware de
comunicación, no una aplicación web.

## Architecture Decisions

Ver documento completo: `architecture.md`

| Estilo/Patrón | Decisión |
|---------------|----------|
| **Layered + Component-Based** | Capas: Serial → Parseo → Procesamiento → API. Cada etapa como módulo independiente |
| **Client/Server** | ESP32 como cliente de datos, Flask como servidor de procesamiento |
| **RESTful** | API HTTP para consultar datos procesados y controlar experimentos |
| **Pipeline** | Cadena de procesamiento: AGC → Hampel → Butterworth → SG → Fondo → Detección |
| **DTO** | `CsiLine` transporta datos entre capas sin acoplamiento |
| **Repository** | Abstracción del origen: serial, archivo o mock |
| **Polling** | Lector serial consulta el puerto en bucle |
| **Store and Forward** | Buffer de líneas CSI antes de procesar |
| **Strategy** | Algoritmo de detección intercambiable |
| **MVC** | Flask routes (C), modelos (M), templates o API JSON (V) |

**No aplican**: SOA, Microservices, Message Bus, Service Registry/Discovery, API Gateway,
Circuit Breaker, Load Balance, SSO — sistema académico local de 1 servidor.

## Implementation Concern Map

### IC-01 — Protocolo de línea y parser CSV

- **Purpose**: Definir el formato exacto de las líneas CSI y el parser que las
convierte en estructuras de datos Python
- **Relevant requirements**: FR-002, FR-003, FR-005
- **Affected surfaces**: `src/flask_serial/parser.py`, `src/flask_serial/models.py`
- **Sequencing/depends-on**: none
- **Risks**: El formato de 26 campos debe coincidir exactamente con el firmware

### IC-02 — Lector de puerto serial y bufferización

- **Purpose**: Implementar la lectura del puerto serial UART con bufferización
eficiente y reconstrucción de líneas a partir del delimitador `\n`
- **Relevant requirements**: FR-001, FR-004, FR-006, FR-008
- **Affected surfaces**: `src/flask_serial/reader.py`
- **Sequencing/depends-on**: IC-01 (parser define el formato de salida)
- **Risks**: Pérdida de datos si el buffer se satura; timeout en desconexión

### IC-03 — Comandos de control (host → ESP32)

- **Purpose**: Implementar el envío de comandos SETTIME y RESET por UART
- **Relevant requirements**: FR-007
- **Affected surfaces**: `src/flask_serial/commands.py`
- **Sequencing/depends-on**: IC-02 (lector debe estar funcionando)
- **Risks**: Sin ACK; comando puede perderse si el ESP32 está ocupado
