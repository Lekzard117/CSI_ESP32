---
work_package_id: WP02
title: Use Cases, Sequence Diagrams and CIM Model
dependencies:
- WP01
requirement_refs:
- FR-004
- FR-005
- FR-006
- FR-009
- FR-010
tracker_refs: []
planning_base_branch: model-kitty-v1
merge_target_branch: model-kitty-v1
branch_strategy: Planning artifacts for this mission were generated on model-kitty-v1. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into model-kitty-v1 unless the human explicitly redirects the landing branch.
subtasks:
- T003
- T005
- T006
agent: "opencode:unknown:curator-carla:reviewer"
shell_pid: "20660"
history:
- timestamp: '2026-07-07T21:26:29Z'
  event: created
agent_profile: curator-carla
authoritative_surface: models-v1/
create_intent:
  - models-v1/use-case-diagram.puml
  - models-v1/sequence-diagrams.puml
  - models-v1/cim-requirements-model.puml
execution_mode: planning_artifact
owned_files:
- models-v1/use-case-diagram.puml
- models-v1/sequence-diagrams.puml
- models-v1/cim-requirements-model.puml
- models-v1/cim-requirements-model.puml
role: implementer
tags: []
---

# WP02 — Use Cases, Sequence Diagrams and CIM Model

## ⚡ Do This First: Load Agent Profile

Before reading anything else, load your assigned profile:

```
/ad-hoc-profile-load implementer
```

Once loaded, return to this prompt for full context and instructions.

## Objective

Crear el diagrama de casos de uso, los diagramas de secuencia del flujo de datos extremo a extremo, y el modelo CIM de requisitos para el sistema ESP32-CSI-Tool.

## Context

Este WP asume que WP01 ya creó `models-v1/` y el diagrama C4 de contexto. Los artefactos aquí generados refinan el modelado del sistema con mayor detalle.

Los 3 roles de firmware documentados:
- **active_sta**: Transmisor WiFi en modo estación
- **active_ap**: Receptor que captura CSI como AP
- **passive**: Monitor pasivo en modo promiscuo

Datos CSI: 26 campos CSV, campo 26 contiene valores I/Q interleaved `[I0 Q0 I1 Q1 ...]` (64 o 192 subcarriers). Ver sección Data Model en `spec.md` para referencia completa.

## Subtasks

### T003 — Create use case diagram (DD-002)

**Purpose**: Crear diagrama de casos de uso en PlantUML que modele las interacciones entre el actor principal (investigador) y los 3 roles de firmware.

**Required content**:

1. **Actor**: `Investigador` (usuario del sistema)
2. **Casos de uso**:

   **active_sta**:
   - `Configurar active_sta` — flashear firmware, configurar SSID del AP
   - `Transmitir paquetes WiFi` — el firmware envía paquetes periódicamente
   - `Verificar conexión al AP` — confirmar que el active_sta está asociado

   **active_ap**:
   - `Configurar active_ap como AP` — flashear firmware, iniciar modo AP
   - `Capturar CSI de estaciones` — recibir paquetes y extraer CSI
   - `Transmitir datos por serial` — enviar CSV a 921600 baud por UART
   - `Sincronizar timestamp` — difundir timestamp a estaciones o vía SETTIME

   **passive**:
   - `Configurar passive en canal` — flashear firmware, seleccionar canal WiFi
   - `Monitorear canal en modo promiscuo` — capturar CSI de todo el tráfico
   - `Transmitir datos por serial` — mismo formato que active_ap

3. **Relaciones**:
   - `<<include>>`: Capturar CSI incluye transmisión serial
   - `<<extend>>`: Sincronizar timestamp extiende la captura CSI

**PlantUML guidelines**:
- Usar sintaxis estándar PlantUML: `left to right direction`, `actor`, `usecase`
- Los casos de uso se agrupan visualmente por rol con `rectangle` o notas
- Incluir leyenda del sistema

**Files**:
- `models-v1/use-case-diagram.puml`

**Validation**:
- [ ] Diagrama renderizable sin errores
- [ ] Actor "Investigador" presente
- [ ] Mínimo 8 casos de uso distribuidos entre los 3 roles
- [ ] Relaciones include/extend correctas

---

### T005 — Create sequence diagrams (DD-004)

**Purpose**: Crear diagramas de secuencia en PlantUML que modelen el flujo de datos extremo a extremo del sistema ESP32-CSI-Tool, desde la transmisión del paquete WiFi hasta la salida serial.

**Required content**:

**Diagrama 1: Flujo active_sta → active_ap → serial**
- **Lifelines**: Investigador, active_sta, active_ap (ESP32), WiFi Medium, UART Serial, PC/Laptop
- **Flujo**:
  1. Investigador → active_sta: `Flashea firmware active_sta`
  2. active_sta → AP WiFi: `Asociación y autenticación`
  3. AP WiFi → active_sta: `Respuesta asociación`
  4. active_sta → WiFi Medium: `Transmite paquete de datos (loop)`
  5. WiFi Medium → active_ap: `Paquete recibido en ANT0/ANT1`
  6. active_ap → active_ap: `Callback wifi_csi_cb()` — extrae rx_ctrl, MAC, buf CSI
  7. active_ap → active_ap: `Serializa 26 campos CSV con prefijo CSI_DATA`
  8. active_ap → UART Serial: `Línea CSI_DATA escrita a 921600 baud`
  9. UART Serial → PC/Laptop: `Datos recibidos en monitor serial`
  10. PC/Laptop → PC/Laptop: `(Opcional) grep "CSI_DATA" > experimento.csv`
  11. PC/Laptop → PC/Laptop: `(Opcional) serial_plot_csi_live.py` grafica en vivo

**Diagrama 2: Flujo passive → serial** (similar, reemplazando active_ap con passive)
- Misma estructura pero el passive escucha en modo promiscuo sin asociación a AP

**Detalles técnicos a incluir**:
- Timestamps: `local_timestamp` (timer ESP32 en µs) y `real_timestamp` (steady_clock)
- Formato CSI_DATA: `[I0 Q0 I1 Q1 ...]` con 64 valores int8 (LLTF) o 384 (full)
- Tasa: 921600 baud

**PlantUML guidelines**:
- Usar `actor` para Investigador, `participant`/`actor` para dispositivos
- Notas laterales para explicar formato de datos (`note right:`)
- Líneas `activate`/`deactivate` para mostrar duración de procesos
- Bucle para transmisión periódica: `loop [cada N ms]`

**Files**:
- `models-v1/sequence-diagrams.puml`

**Validation**:
- [ ] Diagrama renderizable sin errores
- [ ] Mínimo 2 diagramas (active_sta→active_ap→serial, passive→serial)
- [ ] Incluye flujo completo: TX WiFi → recepción → serialización → UART
- [ ] Menciona el formato de 26 campos y CSI_DATA I/Q interleaved
- [ ] Incluye nota sobre exclusión de la capa Flask

---

### T006 — Create CIM requirements model (DD-005)

**Purpose**: Crear modelo CIM (Computation Independent Model) en PlantUML que documente la relación entre actores, casos de uso y componentes del sistema ESP32-CSI-Tool, manteniendo el nivel de abstracción de negocio/dominio sin detalles de implementación.

**Required content**:

El modelo CIM debe representar:

1. **Actores del dominio**:
   - `Investigador` — usuario académico que opera el sistema
   - `Sistema ESP32-CSI-Tool` — el sistema siendo modelado

2. **Funcionalidades de negocio** (derivadas de user stories y casos de uso):
   - `Generación de tráfico WiFi` — active_sta
   - `Captura de CSI` — active_ap y passive
   - `Transmisión serial de datos` — active_ap y passive
   - `Sincronización temporal` — active_ap
   - `Monitoreo de canal` — passive

3. **Relaciones**:
   - Actor `Investigador` se relaciona con todas las funcionalidades
   - Las funcionalidades se agrupan por rol de firmware
   - Conectores que indiquen `<<uso>>`, `<<ejecuta>>`, `<<captura>>`

4. **Diagramas adicionales dentro del modelo CIM** (opcional, mismo archivo):
   - Un diagrama de clases conceptual (nivel CIM, sin atributos técnicos)
   - Entidades de dominio: `PaqueteWiFi`, `DatoCSI`, `Subportadora`, `Canal`, `Experimento`

**PlantUML guidelines**:
- Usar sintaxis `class` o `rectangle` para componentes conceptuales
- Las relaciones usan flechas con estereotipos semánticos (`<<realiza>>`, `<<usa>>`)
- NO incluir detalles de implementación (no tipos de dato técnicos, no frameworks)
- El nivel de abstracción debe ser comprensible para un stakeholder no técnico

**Files**:
- `models-v1/cim-requirements-model.puml`

**Validation**:
- [ ] Diagrama renderizable sin errores
- [ ] Modelo CIM (no PIM/PSM) — sin detalles de implementación técnica
- [ ] Incluye actores del dominio y funcionalidades de negocio
- [ ] Relaciones semánticas claras entre actores y funcionalidades
- [ ] Alineado con user stories de WP01

## Branch Strategy

- Planning base: `model-kitty-v1`
- Merge target: `model-kitty-v1` (PR a `master`)
- Depends on WP01 habiendo creado `models-v1/`

## Test Strategy

No aplica. Artefactos de documentación. Validación visual y de correctitud semántica.

## Definition of Done

1. `models-v1/use-case-diagram.puml` — diagrama de casos de uso renderizable
2. `models-v1/sequence-diagrams.puml` — 2+ diagramas de secuencia renderizables
3. `models-v1/cim-requirements-model.puml` — modelo CIM renderizable
4. Todos los archivos commiteados en `model-kitty-v1`

## Risks

- Los diagramas de secuencia pueden ser demasiado detallados (caer en PSM). Mantener nivel CIM/PIM
- El modelo CIM puede confundirse con un diagrama de clases técnico. Reforzar que es conceptual
- Dependencia de WP01 para la estructura de directorio `models-v1/`

## Activity Log

- 2026-07-07T22:02:31Z – opencode:unknown:curator-carla:implementer – shell_pid=20299 – Started implementation via action command
- 2026-07-07T22:02:45Z – opencode:unknown:curator-carla:implementer – shell_pid=20299 – All 3 subtasks implemented: use case diagram, sequence diagrams, CIM requirements model. Ready for review.
- 2026-07-07T22:02:49Z – opencode:unknown:curator-carla:reviewer – shell_pid=20660 – Started review via action command
- 2026-07-07T22:03:11Z – user – shell_pid=20660 – Review passed: use case diagram (DD-002) covers 3 roles + utils, sequence diagrams (DD-004) model both active→AP and passive flows, CIM model (DD-005) maps all 10 FRs, 4 NFRs, and 6 components with traceable relationships.
