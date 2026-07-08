# Work Packages — Interfaz de Comunicación ESP32 → Flask

**Branch**: `model-kitty-v1` | **Date**: 2026-07-08 | **Plan**: [plan.md](./plan.md)

## Subtask Index

| ID | Description | WP | Parallel |
|----|-------------|----|----------|
| T001 | Create `src/flask_serial/` package structure | WP01 | [P] |
| T002 | Implement `models.py` — CsiLine dataclass + Role enum | WP01 | [P] |
| T003 | Implement `parser.py` — parse_line() con validación bracket+space | WP01 | |
| T004 | Write `test_parser.py` — pruebas unitarias | WP01 | |
| T005 | Write DD-002 — especificación del protocolo de línea | WP01 | [P] |
| T013 | Write DD-001 — diagrama de secuencia (Mermaid) | WP01 | [P] |
| T006 | Implement `reader.py` core: connect/disconnect/lines() | WP02 | |
| T007 | Implement bufferización con reconstrucción de líneas por `\n` | WP02 | |
| T008 | Manejo de errores: líneas malformadas, timeout, reconexión | WP02 | |
| T009 | Soporte multi-puerto via SERIAL_PORTS env var | WP02 | [P] |
| T010 | Write `test_reader.py` con mock de puerto serial | WP02 | |
| T011 | Implement `commands.py` — send_settime(), send_reset() | WP03 | |
| T012 | Manejo de error para comandos sin ACK | WP03 | |
| T014 | Update `quickstart.md` con ejemplos funcionales | WP03 | [P] |

## Work Packages

---

### WP01: Models and Parser

**Goal**: Implementar `models.py`, `parser.py`, y sus tests unitarios. Producir DD-001 (diagrama de secuencia) y DD-002 (especificación del protocolo).

**Priority**: HIGH — Foundation de todo el pipeline

**Dependencies**: None

**Independent Test**: `pytest tests/test_parser.py` pasa 100%

**Prompt file**: `tasks/WP01-models-and-parser.md`

**Estimated prompt size**: ~380 lines

**Subtask count**: 6

#### Included Subtasks

- [ ] T001 — Create `src/flask_serial/` package structure
- [ ] T002 — Implement `models.py` — CsiLine dataclass + Role enum
- [ ] T003 — Implement `parser.py` — parse_line() con validación bracket+space
- [ ] T004 — Write `test_parser.py` — unit tests
- [ ] T005 — Write DD-002 — protocol specification document
- [ ] T013 — Write DD-001 — sequence diagram (Mermaid)

#### Implementation Sketch

1. Crear directorios `src/flask_serial/` y `tests/`
2. Implementar `models.py` con `Role(Enum)` y `CsiLine @dataclass`
3. Implementar `parser.py` con `parse_line()` y helpers `_int`, `_float`, `_bool`, `_parse_csi_bracket`
4. Escribir `test_parser.py` con pytest (línea válida completa, CSI vacío, prefijo inválido, campos insuficientes, brackets faltantes)
5. Redactar DD-002 como sección en `contracts/README.md` o un doc aparte
6. Escribir DD-001 como diagrama Mermaid y renderizarlo/salvarlo

#### Parallel Opportunities

- T001 puede hacerse primero
- T005 y T013 son independientes del código y pueden hacerse en paralelo
- T002 y T003 son secuenciales (models antes que parser)

#### Risks

- Formato CSI_DATA debe coincidir exactamente con `_components/csi_component.h` del firmware
- El parser debe aceptar el formato bracket+space (NO comma) para el campo 26

---

### WP02: Serial Reader and Bufferization

**Goal**: Implementar `reader.py` con bufferización, detección de timeout, reconexión, y soporte multi-puerto.

**Priority**: HIGH — Middleware de comunicación

**Dependencies**: WP01 (parser define el formato de salida de `CsiLine`)

**Independent Test**: `pytest tests/test_reader.py` pasa 100% con mock serial

**Prompt file**: `tasks/WP02-serial-reader.md`

**Estimated prompt size**: ~320 lines

**Subtask count**: 5

#### Included Subtasks

- [ ] T006 — Implement `reader.py` core: connect/disconnect/lines() generator
- [ ] T007 — Implement bufferización con reconstrucción de líneas por `\n`
- [ ] T008 — Error handling: discard malformed lines, timeout detection, reconnection loop
- [ ] T009 — Multi-port support via SERIAL_PORTS env var
- [ ] T010 — Write `test_reader.py` with mock serial port

#### Implementation Sketch

1. Implementar `SerialReader.__init__(port, baud)` con estado inicial
2. Implementar `connect()` y `disconnect()` con manejo de `SerialException`
3. Implementar `lines()` como generator que hace read(4096) en bucle
4. Implementar `_flush_lines()`: split por `\n`, decodificar, delegar a `parse_line()`
5. Implementar timeout de 5s, reconexión cada 2s
6. Implementar `create_readers()` desde `SERIAL_PORTS` env var
7. Escribir `test_reader.py` con `unittest.mock` (patch `serial.Serial`)

#### Parallel Opportunities

- Ninguna significativa — las subtareas son secuenciales
- T009 (multi-puerto) puede implementarse al final una vez que el reader base funciona

#### Risks

- Pérdida de datos si el buffer de 4096 bytes no es suficiente a 921600 baud
- El timeout de 5s puede generar falsos positivos si el ESP32 deja de transmitir momentáneamente
- Sin control de flujo, no hay forma de evitar saturación

---

### WP03: Control Commands and Quickstart

**Goal**: Implementar `commands.py` con envío de SETTIME y RESET, y actualizar `quickstart.md` con ejemplos funcionales.

**Priority**: MEDIUM — Funcionalidad de control

**Dependencies**: WP02 (necesita `SerialReader` conectado)

**Independent Test**: Verificación empírica con ESP32 físico (no hay mock trivial para comandos sin ACK)

**Prompt file**: `tasks/WP03-commands-and-quickstart.md`

**Estimated prompt size**: ~180 lines

**Subtask count**: 3

#### Included Subtasks

- [ ] T011 — Implement `commands.py` — send_settime(), send_reset()
- [ ] T012 — Manejo de error: log sin ACK
- [ ] T014 — Update `quickstart.md` con ejemplos funcionales

#### Implementation Sketch

1. Implementar `send_settime(reader, unix_seconds)` — formato `SETTIME:<unix_seconds>\n`
2. Implementar `send_reset(reader)` — formato `RESET\n`
3. Loggear comando enviado y posible error de escritura
4. Actualizar `quickstart.md` con ejemplos de uso real (conexión, lectura, comandos)

#### Parallel Opportunities

- T014 (quickstart) es independiente y puede hacerse en paralelo con T011/T012

#### Risks

- Sin ACK en firmware, no hay forma de confirmar que el comando se recibió
- Si el ESP32 está en medio de una transmisión CSI, puede perderse el comando

## Dependency Graph

```
WP01 (Foundation) ──> WP02 (Serial Reader) ──> WP03 (Commands)
```

No hay dependencias cíclicas. WP03 no puede comenzar hasta que WP02 esté completo.

## Requirement Coverage Summary

| WP | FRs cubiertos |
|----|---------------|
| WP01 | FR-002, FR-003, FR-005 |
| WP02 | FR-001, FR-004, FR-006, FR-008 |
| WP03 | FR-007 |
| (FR-009 cubierto por consistencia entre WPs) | |

## Validation

- [ ] Todos los subtasks asignados exactamente a un WP
- [ ] Cada WP tiene 3-7 subtasks
- [ ] Prompt size estimado < 700 líneas por WP
- [ ] Dependencies explícitas entre WPs
- [ ] FRs cubiertos según plan.md
- [ ] WPs independientemente implementables
