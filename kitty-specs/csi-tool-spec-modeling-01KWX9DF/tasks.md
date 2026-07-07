# Tasks: ESP32-CSI-Tool: specification and modeling

**Mission**: `csi-tool-spec-modeling-01KWX9DF`
**Branch**: `model-kitty-v1`

## Subtask Index

| ID | Description | WP | Parallel |
|----|-------------|----|----------|
| T001 | Crear directorio `models-v1/` y estructura base | WP01 | — |
| T002 | Crear diagrama C4 de contexto (DD-001) | WP01 | [P] |
| T003 | Crear diagrama de casos de uso (DD-002) | WP02 | [P] |
| T004 | Redactar historias de usuario (DD-003) | WP01 | [P] |
| T005 | Crear diagramas de secuencia (DD-004) | WP02 | — |
| T006 | Crear modelo CIM de requisitos (DD-005) | WP02 | — |

## Work Packages

---

### WP01 — Foundation, Context Diagram and User Stories

**Goal**: Preparar el directorio `models-v1/`, crear el diagrama C4 de contexto del sistema de 3 capas, y redactar las historias de usuario para los 3 roles de firmware.
**Priority**: Alta (base para modelado posterior)
**Prompt**: `tasks/WP01-foundation-context-stories.md`
**Estimated size**: ~250 lines

**Included subtasks**:
- [x] T001 Create `models-v1/` directory and scaffold structure
- [x] T002 Create C4 context diagram (`c4-context-diagram.puml`) for DD-001
- [x] T004 Write user stories (`user-stories.md`) for DD-003

**Implementation notes**:
1. T001: Crear `models-v1/` en raíz del repo con estructura plana; los archivos futuros se agregan sin subdirectorios
2. T002: Modelar las 3 capas (active_sta → active_ap/passive → serial) como C4 contexto; excluir Flask
3. T004: Formato "Como [rol], quiero [acción], para [beneficio]" para active_sta, active_ap, passive

**Parallel opportunities**: T002 y T004 pueden ejecutarse en paralelo tras T001

**Dependencies**: Ninguna

**Risks**: El diagrama C4 debe reflejar el estado actual del firmware sin incluir la capa Flask (postergada)

---

### WP02 — Use Cases, Sequence Diagrams and CIM Model

**Goal**: Crear el diagrama de casos de uso, los diagramas de secuencia del flujo de datos, y el modelo CIM de requisitos.
**Priority**: Alta
**Prompt**: `tasks/WP02-use-cases-sequence-cim.md`
**Estimated size**: ~250 lines

**Included subtasks**:
- [x] T003 Create use case diagram (`use-case-diagram.puml`) for DD-002
- [x] T005 Create sequence diagrams (`sequence-diagrams.puml`) for DD-004
- [ ] T006 Create CIM requirements model (`cim-requirements-model.puml`) for DD-005

**Implementation notes**:
1. T003: Actor "Investigador" con casos de uso para active_sta (transmitir paquetes), active_ap (recibir CSI como AP), passive (monitorear canal promiscuo)
2. T005: Flujo active_sta envía paquete WiFi → receptor captura → serializa CSV con 26 campos → envía por UART a 921600 baud
3. T006: Modelo CIM relacionando actores, casos de uso y componentes del sistema ESP32-CSI-Tool

**Parallel opportunities**: T003 y T005 pueden ejecutarse en paralelo si se comprende el sistema

**Dependencies**: WP01 (contexto del sistema necesario para boundary correcto en secuencia y CIM)

**Risks**: Mantener nivel de abstracción CIM sin derivar a PIM/PSM
