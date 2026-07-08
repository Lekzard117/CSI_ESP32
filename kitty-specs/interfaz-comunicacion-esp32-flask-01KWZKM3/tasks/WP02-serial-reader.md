---
work_package_id: WP02
title: Serial Reader and Bufferization
dependencies:
- WP01
requirement_refs:
- FR-001
- FR-004
- FR-006
- FR-008
tracker_refs: []
subtasks:
- T006
- T007
- T008
- T009
- T010
history: []
authoritative_surface: src/flask_serial/
create_intent: []
execution_mode: code_change
owned_files:
- src/flask_serial/reader.py
- tests/test_reader.py
tags: []
---

## ⚡ Do This First: Load Agent Profile

Before reading anything else, load the **implementer** profile:

```
/ad-hoc-profile-load
```

This activates the identity, governance scope, and initialization declaration for this work package.

---

## Objective

Implement the `SerialReader` class that reads CSI data from the ESP32's UART port, accumulates bytes into lines, parses them via the parser from WP01, and yields `CsiLine` objects. Includes error handling (timeout, disconnection, reconnection) and multi-port support.

---

## Context

This is WP02 of 3 for the ESP32-Flask communication interface. It depends on WP01 (models + parser) already being complete and committed.

The `SerialReader` is the entry point of the data pipeline. It reads raw bytes from `/dev/ttyUSB0` (or another port) at 921600 baud, reconstructs lines by splitting on `\n`, and delegates parsing to `flask_serial.parser.parse_line()`.

### Physical layer parameters

| Parameter | Value |
|-----------|-------|
| Protocol | UART 8N1 (8 bits, no parity, 1 stop) |
| Baud rate | 921600 |
| Voltage | 3.3V TTL |
| TX pin (ESP32) | GPIO1 (TXD0) |
| Flow control | None |
| Line delimiter | `\n` (0x0A) |
| Line encoding | UTF-8 |

### Architecture pattern

**Repository** pattern: `SerialReader` is a concrete implementation of a data source. Future implementations could read from a file (playback) or from a mock (testing).

**Polling** pattern: The reader polls `serial.read(4096)` in a loop.

**Store and Forward** pattern: Bytes accumulate in a `bytearray` buffer until `\n` is found.

### Reference implementation

A prototype exists in `kitty-specs/interfaz-comunicacion-esp32-flask-01KWZKM3/contracts/reader.py`. The final implementation should follow the same structure but with proper error handling, logging, and robustness.

---

## Subtasks

### T006 — Implement `reader.py` core: connect/disconnect/lines()

**Purpose**: Create the `SerialReader` class with connection lifecycle management.

**File**: `src/flask_serial/reader.py`

**Interface**:

```python
class SerialReader:
    def __init__(self, port: str, baud: int = 921600):
        ...

    def connect(self) -> bool:
        """Open the serial port. Returns True on success, False on failure."""
        ...

    def disconnect(self):
        """Close the serial port if open."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if the port is open."""
        ...

    def lines(self) -> Generator[CsiLine, None, None]:
        """Generator yielding parsed CsiLine objects from the serial stream."""
        ...
```

**Serial port configuration**:
```python
import serial
ser = serial.Serial(
    port=port,
    baudrate=baud,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1,  # 1 second read timeout for polling
)
```

**Logging**: Use `logging.getLogger(__name__)` — log connection success/failure, line count, error count.

**Attributes**:
- `self._ser: Optional[serial.Serial]` — the port handle
- `self._buffer: bytearray` — accumulation buffer
- `self.line_count: int` — successful parse counter
- `self.error_count: int` — failed parse counter
- `self.last_rx: float` — `time.time()` of last received byte (for timeout detection)

**Validation**:
- [ ] `connect()` returns `True` when port opens successfully
- [ ] `connect()` returns `False` on `SerialException` (port not found, permission denied)
- [ ] `is_connected` is `False` before `connect()` and `True` after successful `connect()`
- [ ] `disconnect()` works even if already disconnected (no exception)

---

### T007 — Implement bufferización con reconstrucción de líneas por `\n`

**Purpose**: Accumulate incoming bytes in a buffer and extract complete lines delimited by `\n`.

**Method**: `_flush_lines()` — internal generator called from `lines()`.

**Algorithm**:
```python
def _flush_lines(self) -> Generator[CsiLine, None, None]:
    while b"\n" in self._buffer:
        raw_bytes, self._buffer = self._buffer.split(b"\n", 1)
        raw_str = raw_bytes.decode("utf-8", errors="replace").strip()
        if not raw_str:
            continue  # skip empty lines
        try:
            line = parse_line(raw_str)
            self.line_count += 1
            yield line
        except ValueError as e:
            self.error_count += 1
            logger.warning(f"Parse error on {self.port}: {e}")
```

**Integration in `lines()`**:
```python
def lines(self) -> Generator[CsiLine, None, None]:
    if not self._ser or not self._ser.is_open:
        raise RuntimeError("Not connected. Call connect() first")

    while True:
        try:
            data = self._ser.read(4096)
            if data:
                self.last_rx = time.time()
                self._buffer.extend(data)
                yield from self._flush_lines()
            else:
                # read() returned empty bytes (timeout)
                if time.time() - self.last_rx > TIMEOUT_SECONDS:
                    logger.warning(f"Timeout on {self.port}")
                    self.reconnect()
        except serial.SerialException as e:
            logger.error(f"Serial error on {self.port}: {e}")
            self.reconnect()
```

**Validation**:
- [ ] Partial line in buffer (no `\n`) stays accumulated
- [ ] Multiple lines in one `read()` call all get yielded
- [ ] Empty line (just `\n` or spaces then `\n`) is silently skipped
- [ ] `line_count` increments only for successful parses
- [ ] `error_count` increments only for parse failures

---

### T008 — Manejo de errores: líneas malformadas, timeout, reconexión

**Purpose**: Implement robust error recovery per FR-006, FR-008.

**Behavior per spec**:

| Scenario | Behavior |
|----------|----------|
| Malformed line | Discard, log warning, continue streaming |
| Línea vacía | Ignore silently |
| Buffer saturated | Data loss — no ESP32 block or retry |
| UART disconnection | Detect timeout after 5s, attempt reconnect every 2s |
| GPIO1 damaged (TX) | No communication — reader reports dead port |

**Constants**:
```python
RECONNECT_DELAY = 2  # seconds between reconnect attempts
TIMEOUT_SECONDS = 5   # seconds without data before declaring timeout
```

**Reconnection loop**:
```python
def reconnect(self):
    self.disconnect()
    time.sleep(RECONNECT_DELAY)
    self.connect()
```

**Note**: `disconnect()` must handle the case where `self._ser` is already `None` or already closed.

**Edge cases**:
- Port disconnected while in `lines()` generator → catch `SerialException`, log, and attempt reconnect
- Repeated reconnection failures → log error but keep trying (don't crash)
- Port comes back after N attempts → transparent recovery

**Validation**:
- [ ] Malformed lines cause `error_count++` and continue, not crash
- [ ] Timeout triggers reconnect attempt
- [ ] `SerialException` during `read()` triggers reconnect attempt

---

### T009 — Soporte multi-puerto via SERIAL_PORTS env var

**Purpose**: Allow multiple serial ports to be monitored simultaneously via environment variable.

**Function**: `create_readers()` — returns a list of `SerialReader` instances.

**Implementation**:
```python
import os
from typing import List

def create_readers() -> List[SerialReader]:
    ports_str = os.getenv("SERIAL_PORTS", "/dev/ttyUSB0")
    readers = []
    for port in ports_str.split(","):
        port = port.strip()
        if port:
            readers.append(SerialReader(port, baud=921600))
    return readers
```

**Note**: Individual readers must be connected manually by the caller. This function just creates them.

**Validation**:
- [ ] `SERIAL_PORTS` not set → returns `[SerialReader("/dev/ttyUSB0")]`
- [ ] `SERIAL_PORTS=/dev/ttyUSB0,/dev/ttyUSB1` → returns 2 readers
- [ ] `SERIAL_PORTS=/dev/ttyUSB0,` → trailing comma handled (skips empty segment)

---

### T010 — Write `test_reader.py` con mock de puerto serial

**Purpose**: Comprehensive test suite for the reader module using mocked serial port.

**File**: `tests/test_reader.py`

**Testing approach**: Use `unittest.mock.patch` to replace `serial.Serial`:

```python
import pytest
from unittest.mock import MagicMock, patch
from flask_serial.reader import SerialReader, create_readers

@pytest.fixture
def mock_serial():
    with patch("flask_serial.reader.serial.Serial") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance
```

**Test cases**:

1. **`test_connect_success`** — `SerialReader("/dev/ttyUSB0").connect()` returns True, serial port opened with correct parameters
2. **`test_connect_failure`** — `serial.Serial()` raises `SerialException`, `connect()` returns False
3. **`test_connect_failure`** — mock raises `SerialException`
4. **`test_disconnect`** — disconnect closes port
5. **`test_disconnect_already_closed`** — disconnect when already disconnected doesn't raise
6. **`test_lines_yields_parsed_lines`** — feed bytes through mock read, verify CsiLine yielded
7. **`test_lines_skips_empty_lines`** — empty lines don't yield anything
8. **`test_lines_handles_malformed_lines`** — malformed lines increment error_count
9. **`test_lines_timeout_triggers_reconnect`** — no data for 5s triggers reconnect
10. **`test_create_readers_default`** — no env var → single default reader
11. **`test_create_readers_multi`** — SERIAL_PORTS with 2 ports → 2 readers
12. **`test_is_connected_property`** — true after connect, false after disconnect

**Mock setup for stream testing**:
```python
# Simulate receiving CSI data
mock_serial.read.side_effect = [
    b"CSI_DATA,AP,AA:BB:CC:DD:EE:FF,-65,1,0,1,1,0,0,0,0,-90,0,6,0,12345678,0,100,0,1,1712345678.500,128,[12 -5 34]\n",
    b"",  # timeout
    b"CSI_DATA,AP,...\n",  # after reconnect
]
```

**Validation**:
- [ ] `pytest tests/test_reader.py -v` — all tests pass
- [ ] Edge cases covered: timeout, reconnect, malformed data, multi-port

---

## Definition of Done

- [ ] `src/flask_serial/reader.py` implemented with `SerialReader` class
- [ ] `tests/test_reader.py` with ≥12 test cases, all passing
- [ ] Bufferization works: partial lines accumulate, full lines yield
- [ ] Error handling: malformed lines logged and skipped, timeout triggers reconnect
- [ ] Multi-port support: `create_readers()` parses `SERIAL_PORTS` env var
- [ ] `pytest tests/test_reader.py -v` passes
- [ ] Code imports cleanly: `from flask_serial.reader import SerialReader`

## Risks

- At 921600 baud, 4096 bytes fills in ~35ms — the polling loop must keep up
- Without hardware flow control, data loss at high throughput is possible
- `serial.read(4096)` with `timeout=1` may return empty bytes in normal operation (not just timeout) — distinguish between "no data yet" and "genuine timeout"

## Reviewer Guidance

Verify:
1. `lines()` generator is robust to serial errors (doesn't crash on transient failures)
2. Empty bytes from `read()` are handled correctly (not mistaken for disconnection)
3. Reconnection loop doesn't spin (has sleep delay)
4. Buffer doesn't grow unbounded (split removes processed bytes)
5. All mock tests are deterministic (no real hardware needed)
