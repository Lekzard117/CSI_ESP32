---
work_package_id: WP03
title: Control Commands and Quickstart
dependencies:
- WP02
requirement_refs:
- FR-007
tracker_refs: []
planning_base_branch: model-kitty-v1
merge_target_branch: model-kitty-v1
branch_strategy: Planning artifacts for this mission were generated on model-kitty-v1. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into model-kitty-v1 unless the human explicitly redirects the landing branch.
subtasks:
- T011
- T012
- T014
history:
- state: implemented
  timestamp: "2026-07-09T02:20:00Z"
  agent: opencode:deepseek-v4-flash-free:python-pedro:implementer
- state: done
  timestamp: "2026-07-09T02:30:00Z"
  agent: opencode:deepseek-v4-flash-free:python-pedro:implementer
authoritative_surface: src/flask_serial/
create_intent:
- src/flask_serial/commands.py
execution_mode: code_change
owned_files:
- src/flask_serial/commands.py
tags: []
agent_profile: python-pedro
role: implementer
agent: general
---

## ⚡ Do This First: Load Agent Profile

Before reading anything else, load the **implementer** profile:

```
/ad-hoc-profile-load
```

This activates the identity, governance scope, and initialization declaration for this work package.

---

## Objective

Implement the host-to-ESP32 control commands (`SETTIME`, `RESET`) and produce a working `quickstart.md` that demonstrates the full communication pipeline end-to-end.

---

## Context

This is WP03 (final) of 3 for the ESP32-Flask communication interface. It depends on WP02 (SerialReader) being complete. WP01 (Models + Parser) is also required transitively.

The ESP32 firmware accepts two commands over UART:

| Command | Format | Description |
|---------|--------|-------------|
| SETTIME | `SETTIME:<unix_seconds>\n` | Sync ESP32 clock to Unix timestamp |
| RESET   | `RESET\n` | Software reset the ESP32 |

**Critical constraint**: The ESP32 firmware does NOT send ACK/NACK responses to commands. There is no way to confirm delivery. Commands may be lost if the ESP32 is busy transmitting CSI data.

### Architecture

The commands module follows a **Command** pattern: each function encapsulates a command string and sends it over the serial connection.

```
User code → commands.send_settime(reader, ts) → reader._ser.write(cmd)
                                                        ↓
                                                  ESP32 UART RX
```

---

## Subtasks

### T011 — Implement `commands.py`

**Purpose**: Provide Python functions to send control commands to the ESP32.

**File**: `src/flask_serial/commands.py`

**Functions**:

```python
from flask_serial.reader import SerialReader
import logging

logger = logging.getLogger(__name__)

def send_settime(reader: SerialReader, unix_seconds: int) -> None:
    """
    Send SETTIME command to ESP32 to synchronize its clock.
    
    Args:
        reader: Connected SerialReader instance
        unix_seconds: Unix timestamp (seconds since epoch)
    
    Raises:
        RuntimeError: If reader is not connected
        serial.SerialException: If write fails
    """
    if not reader.is_connected:
        raise RuntimeError("Reader not connected")
    cmd = f"SETTIME:{unix_seconds}\n"
    reader._ser.write(cmd.encode("utf-8"))
    logger.info(f"SETTIME sent: {unix_seconds}")


def send_reset(reader: SerialReader) -> None:
    """
    Send RESET command to ESP32 for software reboot.
    
    Args:
        reader: Connected SerialReader instance
    
    Raises:
        RuntimeError: If reader is not connected
        serial.SerialException: If write fails
    """
    if not reader.is_connected:
        raise RuntimeError("Reader not connected")
    cmd = "RESET\n"
    reader._ser.write(cmd.encode("utf-8"))
    logger.info("RESET sent")
```

**Important**: The function accesses `reader._ser` directly. This is intentional — `SerialReader` is a thin wrapper and exposing a `write()` passthrough would add unnecessary indirection. The `_ser` attribute is not part of the public API but is stable within this project scope.

**Validation**:
- [ ] `send_settime(reader, 1712345678)` writes `b"SETTIME:1712345678\n"` to serial
- [ ] `send_reset(reader)` writes `b"RESET\n"` to serial
- [ ] Calling either without a connected reader raises `RuntimeError`
- [ ] Functions handle `SerialException` gracefully (log and re-raise)

---

### T012 — Manejo de error: log sin ACK

**Purpose**: Since the ESP32 doesn't ACK commands, log the outcome but don't wait for confirmation.

**Behavior**:
- Log the command string at INFO level before sending
- Log success at INFO level after write completes without exception
- Log failure at ERROR level if write raises `SerialException`
- Do NOT wait for or expect any response from the ESP32

**Edge cases**:
- ESP32 is in the middle of CSI streaming → command bytes may interleave with CSI data → ESP32 firmware is responsible for parsing commands from the stream
- ESP32 is not connected → `reader.is_connected` check catches this
- Serial write times out → `SerialException` raised and logged

**Validation**:
- [ ] Log output shows "SETTIME sent" on successful write
- [ ] Log output shows "SETTIME failed" on write error

---

### T014 — Update `quickstart.md`

**Purpose**: Provide a complete, working quickstart that demonstrates the full pipeline.

**File**: `kitty-specs/interfaz-comunicacion-esp32-flask-01KWZKM3/quickstart.md`

**Full example**:
```markdown
# Quickstart — Interfaz de Comunicación ESP32 → Flask

## Dependencies

```bash
pip install pyserial
```

## Uso básico

```python
from flask_serial.reader import SerialReader
from flask_serial.commands import send_settime

# Configurar el puerto
reader = SerialReader('/dev/ttyUSB0', baud=921600)
reader.connect()
print(f"Conectado: {reader.is_connected}")  # → True

# Enviar comando de sincronización
import time
send_settime(reader, int(time.time()))

# Leer líneas CSI
for line in reader.lines():
    print(f"Rol: {line.role}, MAC: {line.mac}, RSSI: {line.rssi}")
    print(f"  Subportadoras: {len(line.csi_data)} valores I/Q")
    if line.csi_data:
        amplitudes = [abs(v) for v in line.csi_data]
        print(f"  Amplitud media: {sum(amplitudes) / len(amplitudes):.1f}")
```

## Múltiples puertos

```python
import os
from flask_serial.reader import create_readers

# SERIAL_PORTS=/dev/ttyUSB0,/dev/ttyUSB1
for reader in create_readers():
    if reader.connect():
        print(f"OK: {reader.port}")
    else:
        print(f"FAIL: {reader.port}")
```

## Comandos de control

```python
from flask_serial.commands import send_settime, send_reset

send_settime(reader, 1712345678)  # Sincronizar reloj
send_reset(reader)                # Reiniciar ESP32
```
```

**Ensure**:
- All import paths are correct (`flask_serial.reader`, `flask_serial.commands`)
- Example uses realistic values
- Code is copy-paste ready (no placeholder values)
- Error handling is minimal in examples (for readability), but mentions production patterns

**Validation**:
- [ ] `quickstart.md` shows working connection, read, and command examples
- [ ] All imports match the actual package structure
- [ ] Code can be copied and run with a real ESP32

---

## Definition of Done

- [ ] `src/flask_serial/commands.py` implemented with `send_settime()` and `send_reset()`
- [ ] Command functions validate connection state before writing
- [ ] Quickstart updated with complete working examples
- [ ] `python -c "from flask_serial.commands import send_settime, send_reset"` succeeds

## Risks

- No ACK protocol means no delivery guarantee — the user must verify commands manually (e.g., check ESP32 log output)
- Writing to serial while the ESP32 is streaming CSI may cause interleaved data — firmware parses commands from the same UART, so this is expected behavior, not a bug

## Reviewer Guidance

Verify:
1. Command functions handle the no-ACK constraint correctly (no blocking wait for response)
2. Connection validation prevents writing to closed ports
3. Quickstart example actually works when followed step by step
4. `send_settime` uses the correct format `SETTIME:<seconds>\n` (not `SETTIME <seconds>` or other variants)

## Activity Log

- 2026-07-09T02:18:00Z – opencode:deepseek-v4-flash-free:python-pedro:implementer – Implemented: commands.py (send_settime, send_reset), quickstart.md
- 2026-07-09T02:20:00Z – opencode:deepseek-v4-flash-free:python-pedro:implementer – Committed and marked done
