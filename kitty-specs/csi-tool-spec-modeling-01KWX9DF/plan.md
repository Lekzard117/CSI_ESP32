# Implementation Plan: ESP32-CSI-Tool: specification and modeling

**Branch**: `model-kitty-v1` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/kitty-specs/csi-tool-spec-modeling-01KWX9DF/spec.md`

## Summary

Generar 5 artefactos de documentación y modelado que describan el estado actual del firmware ESP32-CSI-Tool (active_sta, active_ap, passive): diagrama C4 de contexto, diagrama de casos de uso, historias de usuario, diagramas de secuencia y modelo de requisitos CIM. Todos en PlantUML (excepto historias de usuario en markdown), almacenados en `models-v1/` con nombres identificables.

## Technical Context

**Language/Version**: PlantUML (diagramas), Markdown (user stories)
**Primary Dependencies**: PlantUML (rendering externo, no incluido en el repo)
**Storage**: Archivos `.puml` y `.md` en `models-v1/` (raíz del repo)
**Testing**: N/A — verificación visual contra el firmware real
**Target Platform**: N/A (artefactos de documentación)
**Project Type**: documentation
**Performance Goals**: N/A
**Constraints**: Los diagramas deben reflejar fielmente el estado actual del firmware, sin incluir la capa Flask (postergada)
**Scale/Scope**: 5 artefactos de modelado + espacio para artefactos futuros

## Charter Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Charter**: Presente (`.kittify/charter/charter.md`)

| Gate | Status | Notes |
|------|--------|-------|
| Risk boundaries | OK | Proyecto académico, sin producción |
| Documentation policy | OK | La documentación se mantiene sincronizada con el código |
| Testing | OK | Sin testing formal definido |
| Review policy | OK | Sin revisión formal (por definir) |

Sin conflictos detectados entre el charter y el plan propuesto.

## Project Structure

### Documentation (this mission)

```
kitty-specs/csi-tool-spec-modeling-01KWX9DF/
├── plan.md              # Este archivo
├── research.md          # (si se genera)
└── checklists/
    └── requirements.md  # Quality checklist

models-v1/               # Artefactos generados (raíz del repo)
├── c4-context-diagram.puml        # DD-001: C4 de contexto
├── use-case-diagram.puml          # DD-002: Casos de uso
├── user-stories.md                # DD-003: Historias de usuario
├── sequence-diagrams.puml         # DD-004: Diagramas de secuencia
└── cim-requirements-model.puml    # DD-005: Modelo CIM
```

### Source Code (no aplica)

Esta misión no modifica código fuente del firmware. Los artefactos generados son documentación descriptiva del estado actual.

## Implementation Concern Map

### IC-01 — Diagrama C4 de contexto

- **Purpose**: Modelar la arquitectura de 3 capas (active_sta → active_ap/ passive → serial) con sus relaciones
- **Relevant requirements**: DD-001
- **Affected surfaces**: `models-v1/c4-context-diagram.puml`
- **Sequencing/depends-on**: none
- **Risks**: Debe excluir explícitamente la capa Flask (misión futura)

### IC-02 — Diagrama de casos de uso

- **Purpose**: Modelar los actores (investigador) y casos de uso para cada rol: active_sta (transmitir), active_ap (recibir CSI), passive (monitorear canal)
- **Relevant requirements**: DD-002
- **Affected surfaces**: `models-v1/use-case-diagram.puml`
- **Sequencing/depends-on**: none
- **Risks**: Identificar correctamente los límites de cada rol

### IC-03 — Historias de usuario

- **Purpose**: Redactar user stories para los 3 roles de firmware en formato estándar (Como... quiero... para...)
- **Relevant requirements**: DD-003
- **Affected surfaces**: `models-v1/user-stories.md`
- **Sequencing/depends-on**: none
- **Risks**: Ninguno significativo

### IC-04 — Diagramas de secuencia

- **Purpose**: Modelar el flujo de datos extremo a extremo: emisor ESP32 envía paquete WiFi → receptor captura CSI → serializa CSV → envía por UART
- **Relevant requirements**: DD-004
- **Affected surfaces**: `models-v1/sequence-diagrams.puml`
- **Sequencing/depends-on**: IC-01 (contexto ayuda a definir límites del flujo)
- **Risks**: Decidir nivel de detalle apropiado para el flujo serial

### IC-05 — Modelo de requisitos CIM

- **Purpose**: Documentar la relación entre actores, casos de uso y componentes del sistema ESP32-CSI-Tool según el modelo CIM
- **Relevant requirements**: DD-005
- **Affected surfaces**: `models-v1/cim-requirements-model.puml`
- **Sequencing/depends-on**: IC-02 (casos de uso alimentan el modelo CIM)
- **Risks**: Mantener el nivel de abstracción correcto (CIM, no PIM/PSM)
