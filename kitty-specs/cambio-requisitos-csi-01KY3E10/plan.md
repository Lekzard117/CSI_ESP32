# Implementation Plan: [MISSION]

**Branch**: `[###-mission-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/kitty-specs/[###-mission-name]/spec.md`

**Note**: This template is filled in by the `/spec-kitty.plan` command. See `src/doctrine/missions/software-dev/command-templates/plan.md` for the execution workflow.

The planner will not begin until all planning questions have been answered—capture those answers in this document before progressing to later phases.

## Summary

Reducir el formato CSI_DATA de 26 a 7 campos esenciales (mac, rssi, channel, local_timestamp, ant, len, CSI_DATA), eliminar el campo role (MAC como identificador único), y mantener 921600 baud sin cambios.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.

  If multiple developers/agents will work on this mission, add an "Implementation
  Concern Map" section below to decompose architectural intent into IC-## concerns
  before generating tasks.
-->

**Language/Version**: Python 3.13+ (parser/server), C++17/ESP-IDF v6.0.1 (firmware)
**Primary Dependencies**: pyserial 3.5+, numpy 2.x (Python); ESP-IDF v6.0.1, FreeRTOS (firmware)
**Storage**: CSV filesystem (captura a archivo), sin base de datos
**Testing**: pytest 8.x con mocking de serial (Python); pruebas en hardware ESP32 (firmware)
**Target Platform**: Linux x86_64 (servidor), ESP32 (Xtensa LX6, firmware)
**Project Type**: single (sistema embebido + servidor Python)
**Performance Goals**: 500+ líneas CSI/s a 921600 baud, ~180 bytes/línea
**Constraints**: 2 ESP32 funcionales, ESP-IDF v6.0.1, 921600 baud fijo

## Charter Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No charter conflicts detected. DIR-001 (riesgo académico, sin producción) no se viola — cambios solo afectan formato serial, no despliegue. DIR-002 (sincronización doc/código) requiere actualizar AGENTS.md y DocLatex si los formatos cambian.

## Project Structure

### Documentation (this mission)

```
kitty-specs/[###-mission]/
├── plan.md              # This file (/spec-kitty.plan command output)
├── research.md          # Phase 0 output (/spec-kitty.plan command)
├── data-model.md        # Phase 1 output (/spec-kitty.plan command)
├── quickstart.md        # Phase 1 output (/spec-kitty.plan command)
├── contracts/           # Phase 1 output (/spec-kitty.plan command)
└── tasks.md             # Phase 2 output (/spec-kitty.tasks command - NOT created by /spec-kitty.plan)
```

### Source Code (repository root)

```
ESP32-CSI-Tool/                  # Firmware ESP32
├── active_sta/main/             # TX
├── active_ap/main/              # RX
├── passive/main/                # Monitor
└── _components/                 # Headers C++ compartidos

src/flask_serial/                # Servidor Python
├── models.py                    # CsiLine dataclass
├── parser.py                    # parse_line()
├── reader.py                    # SerialReader
└── commands.py                  # send_settime()

tests/                           # Tests Python
├── test_parser.py
└── test_reader.py

DocLatex/                        # Documentación
└── ...
```

**Structure Decision**: Monorepo existente con firmware ESP32 en `ESP32-CSI-Tool/` y servidor Python en `src/flask_serial/`. No se crean nuevos directorios; solo se modifican archivos existentes.

## Complexity Tracking

*Fill ONLY if Charter Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Implementation Concern Map

*Include this section when the mission has multiple distinct architectural areas that inform how tasks are decomposed.*

> **Note**: Implementation concerns are NOT work packages and are NOT executable units.
> `/spec-kitty.tasks` translates these into executable WPs — one concern may become
> multiple WPs; multiple small concerns may merge into one WP. Do not label concerns
> with WP-style IDs or sequencing language.

### IC-01 — Formato CSI reducido en firmware C++

- **Purpose**: Modificar los 3 roles (active_sta, active_ap, passive) para emitir el nuevo formato de 7 campos en vez de 26
- **Relevant requirements**: FR-001, FR-002, FR-004
- **Affected surfaces**: `ESP32-CSI-Tool/_components/*` (cabeceras compartidas), `ESP32-CSI-Tool/active_sta/main/`, `ESP32-CSI-Tool/active_ap/main/`, `ESP32-CSI-Tool/passive/main/`
- **Sequencing/depends-on**: none
- **Risks**: Los 3 roles comparten código de formateo CSV via cabeceras; cambios deben hacerse en un solo lugar y propagarse

### IC-02 — Parser Python para nuevo formato

- **Purpose**: Actualizar models.py, parser.py para que acepten y validen el formato de 7 campos sin role
- **Relevant requirements**: FR-001, FR-002, FR-005
- **Affected surfaces**: `src/flask_serial/models.py` (CsiLine), `src/flask_serial/parser.py` (parse_line, FIELD_NAMES), `tests/test_parser.py`
- **Sequencing/depends-on**: IC-01 (firmware debe emitir el formato para testear end-to-end)
- **Risks**: Retrocompatibilidad con datasets existentes (26 campos) — FR-006 requiere script de migración

### IC-03 — Script de migración de datasets

- **Purpose**: Proveer script que convierta datasets CSI existentes (26 campos) al nuevo formato de 7 campos
- **Relevant requirements**: FR-006
- **Affected surfaces**: `src/flask_serial/` (nuevo script `migrate_csv.py`)
- **Sequencing/depends-on**: IC-02 (conocer estructura exacta del nuevo formato)
- **Risks**: Bajo — script independiente, una sola vez
