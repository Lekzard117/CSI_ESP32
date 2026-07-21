# Cambio de requisitos: campos CSI, roles y tasa de baudios

## Stakeholder TLDR

Reducir los 26 campos del formato CSI a un subset esencial, eliminar el campo role (MAC como identificador único) y evaluar la tasa de baudios.

## Problem Statement

El formato actual de 26 campos en las líneas CSI_DATA incluye metadatos que no son necesarios para el procesamiento de señales. Además, el campo `role` introduce complejidad redundante porque la dirección MAC del dispositivo es suficiente para identificar cada ESP32. La tasa de baudios actual (921600) puede ser excesiva para la cantidad de datos realmente necesaria.

## Functional Requirements

| FR | Description | Priority |
|----|-------------|----------|
| FR-001 | Definir un subset mínimo de campos del formato CSI_DATA que preserve solo los datos esenciales para el procesamiento de señales | high |
| FR-002 | Eliminar el campo `role` de la línea CSI_DATA; usar dirección MAC como único identificador de dispositivo | high |
| FR-003 | Evaluar y recomendar una tasa de baudios óptima que balancee throughput y confiabilidad serial | high |
| FR-004 | Modificar el firmware (active_ap, active_sta, passive) para emitir el nuevo formato reducido | high |
| FR-005 | Modificar el pipeline Python (parser.py, models.py) para aceptar el nuevo formato | high |
| FR-006 | Mantener retrocompatibilidad con datasets existentes o proveer script de migración | medium |

## Non-Goals

- No se implementará un mecanismo de descubrimiento dinámico de campos
- No se cambiará el protocolo de sincronización de tiempo (SETTIME)
- No se modificará la arquitectura general de tres capas (ESP32 → Flask)
- No se añadirán nuevos campos al formato

## Stakeholders

- Investigador académico (usuario principal)
- Desarrollador de firmware ESP32

## Constraints

- Debe seguir ejecutándose sobre ESP-IDF v6.0.1
- La salida serial debe seguir siendo CSV legible
- Debe seguir funcionando con 2 ESP32 disponibles (active_ap + active_sta o AP + smartphone)
