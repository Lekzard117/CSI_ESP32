---
work_package_id: WP01
title: Foundation, Context Diagram and User Stories
dependencies: []
requirement_refs:
- FR-001
- FR-002
- FR-003
- FR-007
- FR-008
tracker_refs: []
planning_base_branch: model-kitty-v1
merge_target_branch: model-kitty-v1
branch_strategy: Planning artifacts for this mission were generated on model-kitty-v1. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into model-kitty-v1 unless the human explicitly redirects the landing branch.
subtasks:
- T001
- T002
- T004
agent: opencode
history:
- timestamp: '2026-07-07T21:26:29Z'
  event: created
agent_profile: curator-carla
authoritative_surface: models-v1/
create_intent:
  - models-v1/c4-context-diagram.puml
  - models-v1/user-stories.md
execution_mode: planning_artifact
owned_files:
- models-v1/c4-context-diagram.puml
- models-v1/user-stories.md
role: implementer
tags: []
---

# WP01 — Foundation, Context Diagram and User Stories

## ⚡ Do This First: Load Agent Profile

Before reading anything else, load your assigned profile:

```
/ad-hoc-profile-load implementer
```

Once loaded, return to this prompt for full context and instructions.

## Objective

Preparar el directorio `models-v1/` en la raíz del repositorio, crear el diagrama C4 de contexto del sistema ESP32-CSI-Tool, y redactar las historias de usuario para los 3 roles de firmware.

## Context

Esta misión documenta el estado actual del firmware **ESP32-CSI-Tool**, compuesto por 3 roles:
- **active_sta** (`ESP32-CSI-Tool/active_sta/`): Transmisor WiFi en modo estación, se conecta a un AP y envía paquetes
- **active_ap** (`ESP32-CSI-Tool/active_ap/`): Receptor en modo AP, captura CSI de estaciones conectadas
- **passive** (`ESP32-CSI-Tool/passive/`): Monitor pasivo en modo promiscuo

La capa de procesamiento Flask NO está en alcance de esta misión. Los diagramas deben reflejar SOLO el estado actual del firmware.

Los artefactos se almacenan en `models-v1/` (raíz del repo) con nombres identificables. El renderizado es externo, solo se entregan archivos fuente (`.puml`, `.md`).

## Subtasks

### T001 — Create models-v1/ directory structure

**Purpose**: Crear el directorio `models-v1/` en la raíz del repositorio como contenedor único para todos los artefactos de modelado de esta misión y futuras.

**Steps**:
1. Crear el directorio `models-v1/` en la raíz del repo (`/home/lekzard117/Documentos/CSI-ESP/models-v1/`)
2. No crear subdirectorios internos — todos los archivos van planos en `models-v1/`
3. Los archivos se nombran con kebab-case identificable (ej. `c4-context-diagram.puml`)

**Files**:
- `models-v1/` (directorio)

**Validation**:
- [ ] `models-v1/` existe en la raíz del repo
- [ ] Contenido inicial del directorio incluye solo `.gitkeep` o está vacío

---

### T002 — Create C4 context diagram (DD-001)

**Purpose**: Crear diagrama C4 de contexto (nivel 1) en PlantUML que muestre la arquitectura de 3 capas del sistema CSI-ESP y sus relaciones externas.

**Required content**:
1. **Sistema central**: `ESP32-CSI-Tool` (el sistema siendo documentado)
2. **Actores externos**: `Investigador` (usuario principal)
3. **Componentes internos del sistema** (como cajas de contexto):
   - `active_sta` — Nodo emisor, transmite paquetes WiFi periódicamente
   - `active_ap` — Nodo receptor (AP), captura CSI de estaciones
   - `passive` — Nodo monitor, captura CSI en modo promiscuo
4. **Flujo de datos**:
   - active_sta → active_ap: paquetes WiFi (CSI)
   - active_ap/passive → serial UART: datos CSI en formato CSV a 921600 baud
5. **Bounded context**: La capa Flask se muestra como sistema externo FUTURO (etiquetada como "Futura" o fuera del alcance)

**PlantUML guidelines**:
- Usar `!include <C4/C4_Context>` o sintaxis C4 estándar
- Los componentes internos se representan con `System_Boundary`
- active_sta, active_ap, passive dentro del boundary del ESP32-CSI-Tool
- Incluir leyenda con `LAYOUT_WITH_LEGEND()`
- Comentario en el código: `' Nota: La capa Flask será especificada en misión futura`

**Source context** (para dibujo preciso del sistema actual):
- `ESP32-CSI-Tool/active_sta/` — firmware TX en modo estación
- `ESP32-CSI-Tool/active_ap/` — firmware RX en modo AP
- `ESP32-CSI-Tool/passive/` — firmware monitor pasivo
- `ESP32-CSI-Tool/_components/` — headers compartidos (CSI, time)
- `ESP32-CSI-Tool/python_utils/` — utilidades Python (parse, plot, append_time)
- `ESP32-CSI-Tool/active_*/main/Kconfig.projbuild` — configuraciones

**Files**:
- `models-v1/c4-context-diagram.puml`

**Validation**:
- [ ] Diagrama renderizable con PlantUML sin errores
- [ ] Muestra active_sta, active_ap, passive como componentes del sistema
- [ ] Muestra al investigador como actor externo
- [ ] Flask está explícitamente fuera del alcance o marcado como futuro
- [ ] Flujo de datos: TX → RX → serial es claro
- [ ] Incluye nota sobre exclusión de Flask

---

### T004 — Write user stories (DD-003)

**Purpose**: Redactar historias de usuario en formato estándar para los 3 roles de firmware del ESP32-CSI-Tool.

**Format**: Cada historia sigue la plantilla:
```
**Como** [rol], **quiero** [acción], **para** [beneficio].
```

**Historias requeridas**:

1. **active_sta** (2 historias):
   - Como investigador, quiero que el active_sta transmita paquetes WiFi periódicamente, para generar tráfico CSI capturable por el receptor.
   - Como investigador, quiero que el active_sta se conecte automáticamente al AP configurado, para iniciar la transmisión sin intervención manual.

2. **active_ap** (2 historias):
   - Como investigador, quiero que el active_ap opere como punto de acceso y capture CSI de estaciones conectadas, para obtener datos del estado del canal.
   - Como investigador, quiero que el active_ap transmita los datos CSI por serial a 921600 baud, para enviarlos al servidor de borde en tiempo real.

3. **passive** (2 historias):
   - Como investigador, quiero que el passive capture CSI en modo promiscuo de todos los paquetes en un canal, para analizar tráfico WiFi existente sin un emisor dedicado.
   - Como investigador, quiero configurar el canal WiFi a monitorear en el passive, para enfocar la captura en la banda de interés.

**Criterios de aceptación por historia**:
- La historia es verificable (se puede probar flasheando el firmware correspondiente)
- El rol (active_sta, active_ap, passive) está claramente identificado
- La acción describe comportamiento observable del firmware
- El beneficio se alinea con el objetivo de investigación académica

**Files**:
- `models-v1/user-stories.md`

**Validation**:
- [ ] 6 historias de usuario (2 por rol)
- [ ] Formato consistente: "Como... quiero... para..."
- [ ] Cada historia es verificable con el firmware actual
- [ ] Archivo markdown válido

## Branch Strategy

- Planning base: `model-kitty-v1`
- Merge target: `model-kitty-v1` (PR a `master`)
- Execution worktrees serán asignados por `finalize-tasks` en `lanes.json`

## Test Strategy

No aplica. Los artefactos son documentación. La validación es visual y de correctitud semántica contra el firmware real.

## Definition of Done

1. `models-v1/` creado en la raíz del repositorio
2. `models-v1/c4-context-diagram.puml` generado y renderizable
3. `models-v1/user-stories.md` con 6 historias de usuario
4. Todos los archivos commiteados en `model-kitty-v1`

## Risks

- El C4 puede quedar impreciso si no se inspecciona el código fuente real del firmware
- No incluir Flask explícitamente excluido puede causar confusión en misiones futuras

## Reviewer Guidance

- Verificar que los diagramas reflejen el estado actual del código, no el deseado
- Confirmar que las user stories son verificables con el firmware existente
- Asegurar que no haya referencia a la capa Flask como parte del sistema actual
