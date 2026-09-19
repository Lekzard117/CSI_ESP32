# Patrones de Análisis Aplicados al Diseño CSI-ESP

Mapeo de patrones arquitectónicos y de diseño a los 18 problemas identificados
en el análisis de diseño. Cada entrada documenta: nombre, problema específico
en el dominio, y solución contextualizada.

---

## Resumen de Correspondencia Problema → Patrón

| Prob. | Descripción | Patrón(es) Asignados |
|-------|-------------|----------------------|
| 1.1 | `commands` accede a `reader._ser` (privado) | **Facade**, Law of Demeter |
| 1.2 | `CsiLine` monolítico 26 campos sin tipo por rol | **Tagged Union**, **Visitor** |
| 1.3 | `SerialReader` mezcla 4 responsabilidades | **Facade**, **Single Responsibility** |
| 1.4 | `parse_line()` es función global sin configuración | **Strategy** |
| 2.1 | Cadena rígida commands→reader→parser | **Dependency Injection** |
| 2.2 | `create_readers()` acoplada a `os.getenv` | **Abstract Factory**, **Dependency Injection** |
| 2.3 | `Role` enum sin comportamiento | **Strategy**, **Visitor** |
| 3.1 | Sin interfaz `DataSource` abstracta | **Bridge**, **Adapter** |
| 3.2 | Sin interfaz `CsiProcessor` para pipeline | **Pipeline**, **Decorator** |
| 4.1 | Reintento infinito en reconnect | **Circuit Breaker**, **Retry** |
| 4.2 | Buffer sin límite de crecimiento | **Bounded Buffer** |
| 4.3 | Líneas anómalas sin protección de tamaño | **Guard Clause** |
| 5.1 | Parseo síncrono en mismo hilo que lectura | **Producer-Consumer** |
| 5.2 | Constructor de 25 kwargs posicionales | **Builder**, **Fluent Interface** |
| 5.3 | `len` sombrea built-in | Refactor: *Rename Field* |
| 6.1 | Ruta SD es código muerto en firmware | **Strategy** |
| 6.2 | `vTaskDelay(0)` dentro de mutex | **RAII**, **Scoped Lock** |
| 6.3 | Formato CSV sin invariante documentada | **Interpreter**, **Memento** |

---

## Patrón 1 — Facade

### Problema que resuelve (1.1, 1.3)

**1.1**: `send_settime()` y `send_reset()` en `commands.py:17,29` acceden a
`reader._ser` como atributo privado. Cualquier cambio interno en `SerialReader`
(ej. migrar de `pyserial` a `aiofiles` o añadir buffer de escritura) obliga a
modificar `commands.py`.

**1.3**: `SerialReader` (`reader.py:20-101`) concentra 4 responsabilidades:
gestión de conexión, bufferización de bytes, reconstrucción de líneas, y
detección de timeout. No hay separación entre la interfaz pública (lo que
necesitan los consumidores) y la implementación interna.

### Solución planteada

**Facade**: `SerialReader` se convierte en una fachada que delega cada
responsabilidad a componentes internos, y expone una interfaz pública limpia:

```
SerialReader (Facade)
├── ConnectionManager    (connect / disconnect / reconnect / is_connected)
├── LineBuffer           (acumular bytes, partir por \\n)
├── CsiParser            (parsear raw_str → CsiLine)
└── write(bytes)         (método público nuevo)
```

```python
class SerialReader:
    def __init__(self, port, baud):
        self._conn = ConnectionManager(port, baud)
        self._buf = LineBuffer()
        self._parser = CsiParser()

    def connect(self) -> bool:
        return self._conn.connect()

    @property
    def is_connected(self) -> bool:
        return self._conn.is_connected

    def write(self, data: bytes) -> None:
        self._conn.write(data)       # ← commands.py usa esto

    def reconnect(self):
        self._conn.reconnect()

    def lines(self) -> Generator[CsiLine]:
        if not self._conn.is_connected:
            raise RuntimeError("Not connected")
        while True:
            raw = self._conn.read(4096)
            self._buf.feed(raw)
            yield from self._parser.parse_all(self._buf.drain_lines())
```

**Justificación**: La fachada reduce el acoplamiento a 1 interfaz pública,
elimina la violación de encapsulamiento (reader._ser ya no es accesible), y
permite cambiar la implementación interna sin afectar consumidores.

---

## Patrón 2 — Strategy

### Problema que resuelve (1.4, 2.3, 6.1)

**1.4**: `parse_line()` es función global. No admite configuraciones distintas
(ej. modo estricto donde campos inválidos elevan excepción vs modo permisivo
que asigna `None`).

**2.3**: `Role` enum (`models.py:8-11`) tiene valores `AP`, `PASSIVE`, `STA`
pero ningún comportamiento. La lógica "si role==AP, el campo secondary_channel
es relevante" queda dispersa en los consumidores.

**6.1**: En firmware, `outprintf()` (`sd_component.h:82-97`) está diseñada para
serial+SD, pero `printf()` se usa directamente en `csi_component.h:81`. No
hay un punto único para elegir el destino de salida.

### Solución planteada

**Strategy**: Encapsular algoritmos intercambiables detrás de una interfaz
común, y seleccionarlos en tiempo de construcción.

```python
# Para 1.4 — ParserConfig como estrategia
@dataclass
class ParserConfig:
    strict_mode: bool = False
    expected_fields: int = 26
    csi_delimiter: str = "bracket_space"   # bracket_space | comma | raw

class CsiParser:
    def __init__(self, config: ParserConfig):
        self._config = config

    def parse_line(self, raw: str) -> CsiLine:
        # usa self._config.strict_mode, etc.
        ...
```

```python
# Para 2.3 — Role con métodos Strategy
class Role(Enum):
    AP = "AP"
    PASSIVE = "PASSIVE"
    STA = "STA"

    def is_receiver(self) -> bool:
        return self in {Role.AP, Role.PASSIVE}

    def csv_field_count(self) -> int:
        return 26  # igual para todos en formato actual

    def uses_secondary_channel(self) -> bool:
        return self == Role.AP   # solo AP usa secondary_channel
```

```cpp
// Para 6.1 — OutputStrategy en firmware
typedef void (*OutputStrategy)(const char *fmt, va_list args);

void serial_only(const char *fmt, va_list args) {
    vprintf(fmt, args);
}

void serial_and_sd(const char *fmt, va_list args) {
    vprintf(fmt, args);
    if (f != NULL) vfprintf(f, fmt, args);
}

OutputStrategy current_output = serial_only;

void set_output_strategy(OutputStrategy s) { current_output = s; }
```

**Justificación**: Strategy desacopla algoritmo de contexto. Permite cambiar
comportamiento (formato de parseo, interpretación de rol, destino de salida)
sin modificar el código que los usa. Cada variante es testeable de forma
independiente.

---

## Patrón 3 — Dependency Injection

### Problema que resuelve (2.1, 2.2)

**2.1**: `reader.py:12` importa `parse_line` estáticamente. `commands.py:7`
importa `SerialReader` estáticamente. La cadena de dependencias es rígida:
commands → reader → parser. Cambiar parser requiere modificar reader.

**2.2**: `create_readers()` (`reader.py:104-111`) llama a `os.getenv()`
directamente. No se pueden inyectar puertos desde configuración externa
(solo vía `monkeypatch` en tests).

### Solución planteada

**Dependency Injection**: Las dependencias se pasan como parámetros en lugar
de ser resueltas internamente.

```python
# Para 2.1 — Inyectar parse_line en SerialReader
from typing import Callable
from flask_serial.models import CsiLine

class SerialReader:
    def __init__(self, port: str, baud: int = 921600,
                 parser: Callable[[str], CsiLine] = parse_line):
        self._parser = parser
        ...

    def _flush_lines(self):
        while b"\\n" in self._buffer:
            raw_bytes, self._buffer = self._buffer.split(b"\\n", 1)
            raw_str = raw_bytes.decode("utf-8", errors="replace").strip()
            if not raw_str:
                continue
            try:
                line = self._parser(raw_str)   # ← usa la inyectada
                ...
```

```python
# Para 2.2 — Inyectar configuración de puertos
def create_readers(ports: Optional[str] = None) -> List[SerialReader]:
    ports_str = ports if ports is not None else os.getenv("SERIAL_PORTS", "/dev/ttyUSB0")
    # ... mismo código interno
```

**Justificación**: DI invierte el control de creación de dependencias. Las
pruebas unitarias pueden inyectar `parser` mockeado en `SerialReader` sin
parchear imports. `create_readers()` puede recibir puertos desde `app.config`,
variables de entorno, o CLI sin cambios.

---

## Patrón 4 — Bridge

### Problema que resuelve (3.1)

**3.1**: No hay abstracción `DataSource`. `SerialReader` es la única
implementación. No se puede crear un `FileReader` para playback de datos
grabados, ni un `MockReader` para tests del pipeline de procesamiento, sin
cambiar el código cliente.

### Solución planteada

**Bridge**: Separar la abstracción (qué hace una fuente de datos) de la
implementación (cómo lo hace). Ambas pueden variar independientemente.

```python
from abc import ABC, abstractmethod
from typing import Generator
from flask_serial.models import CsiLine

class DataSource(ABC):
    @abstractmethod
    def lines(self) -> Generator[CsiLine, None, None]:
        ...

    @abstractmethod
    def connect(self) -> bool:
        ...

    @abstractmethod
    def disconnect(self):
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        ...

class SerialDataSource(DataSource):
    def __init__(self, port, baud=921600, parser=parse_line):
        self._impl = SerialReader(port, baud, parser)

    def lines(self) -> Generator[CsiLine, None, None]:
        yield from self._impl.lines()

    def connect(self) -> bool:
        return self._impl.connect()

    def disconnect(self):
        self._impl.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._impl.is_connected

class CsvFileDataSource(DataSource):
    def __init__(self, path: str, parser=parse_line):
        self._path = path
        self._parser = parser
        self._connected = False

    def connect(self) -> bool:
        self._connected = os.path.isfile(self._path)
        return self._connected

    def disconnect(self):
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def lines(self) -> Generator[CsiLine, None, None]:
        with open(self._path) as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                yield self._parser(raw)

class MockDataSource(DataSource):
    def __init__(self, lines: List[CsiLine]):
        self._lines = lines
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def lines(self) -> Generator[CsiLine, None, None]:
        yield from self._lines
```

**Justificación**: Bridge permite que el pipeline de procesamiento (OE2) opere
contra `DataSource` abstracta. Los tests usan `MockDataSource` sin hardware.
Playback usa `CsvFileDataSource`. Producción usa `SerialDataSource`. La
jerarquía de abstracción y las implementaciones evolucionan independientemente.

---

## Patrón 5 — Pipeline / Chain of Responsibility

### Problema que resuelve (3.2)

**3.2**: El pipeline de procesamiento CSI (AGC → Hampel → Butterworth →
Savitzky-Golay → Sustracción de fondo → Detección) se implementará como una
secuencia lineal. Sin una abstracción, reordenar etapas, saltar etapas, o
inyectar nuevas etapas requiere reescribir el flujo completo.

### Solución planteada

**Pipeline** (Chain of Responsibility): Cada etapa implementa una interfaz
`CsiProcessor` con un método `process(frame: CsiFrame) → CsiFrame`. Las
etapas se componen en una cadena invocable y reconfigurable.

```python
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class CsiFrame:
    raw_iq: np.ndarray          # [n_subcarriers, 2] — I/Q interleaved
    amplitude: Optional[np.ndarray] = None   # magnitud por subportadora
    phase: Optional[np.ndarray] = None       # fase por subportadora
    metadata: Optional[CsiLine] = None       # línea original (RSSI, MCS, etc.)
    motion_score: float = 0.0
    is_motion: bool = False

class CsiProcessor(ABC):
    @abstractmethod
    def process(self, frame: CsiFrame) -> CsiFrame:
        ...

class AgcCompensation(CsiProcessor):
    def __init__(self, threshold: float = 3.0):
        self._threshold = threshold

    def process(self, frame: CsiFrame) -> CsiFrame:
        # Detecta saltos de ganancia por cambios bruscos
        # en amplitud promedio entre frames consecutivos
        # Aplica interpolación lineal para suavizar
        return frame

class HampelFilter(CsiProcessor):
    def __init__(self, window: int = 5, n_sigmas: float = 3.0):
        self._window = window
        self._n_sigmas = n_sigmas

    def process(self, frame: CsiFrame) -> CsiFrame:
        # Reemplaza outliers con mediana local
        return frame

class CsiPipeline:
    def __init__(self, stages: List[CsiProcessor]):
        self._stages = stages

    def process(self, frame: CsiFrame) -> CsiFrame:
        for stage in self._stages:
            frame = stage.process(frame)
        return frame

    def with_stage(self, stage: CsiProcessor, index: int = -1) -> "CsiPipeline":
        new_stages = self._stages.copy()
        new_stages.insert(index if index >= 0 else len(new_stages), stage)
        return CsiPipeline(new_stages)

# Uso:
pipeline = CsiPipeline([
    AgcCompensation(),
    HampelFilter(window=5, n_sigmas=3.0),
    ButterworthFilter(cutoff=10.0, fs=100.0, order=4),
    SavgolFilter(window_length=7, polyorder=2),
    BackgroundSubtraction(window=100),
    MotionDetector(threshold=2.5),
])
```

**Justificación**: Pipeline permite componer, reordenar y extender etapas sin
modificar el flujo base. Cada etapa es testeable aisladamente. `with_stage()`
permite crear variantes del pipeline por inyección (ej. pipeline más simple
para pruebas, pipeline completo para producción).

---

## Patrón 6 — Circuit Breaker

### Problema que resuelve (4.1)

**4.1**: `reconnect()` en `reader.py:62-65` se ejecuta sin límite. Si el
puerto serial está muerto (GPIO1 dañado, ESP32 desconectado), el bucle es
infinito. El servidor Flask nunca recibe una señal de "dead port".

### Solución planteada

**Circuit Breaker**: Monitorear fallos de conexión. Después de N fallos
consecutivos, abrir el circuito (dejar de intentar) y elevar una excepción.
Reintentar después de un tiempo de espera (half-open).

```python
class CircuitBreaker:
    def __init__(self, max_failures: int = 5, reset_timeout: float = 30.0):
        self._failures = 0
        self._max = max_failures
        self._reset_timeout = reset_timeout
        self._last_failure = 0.0
        self._state = "closed"  # closed | open | half_open

    def call(self, fn: Callable, *args, **kwargs):
        if self._state == "open":
            if time.time() - self._last_failure > self._reset_timeout:
                self._state = "half_open"
            else:
                raise RuntimeError("Circuit breaker open: port unavailable")

        try:
            result = fn(*args, **kwargs)
            if self._state == "half_open":
                self._state = "closed"
                self._failures = 0
            return result
        except SerialException as e:
            self._failures += 1
            self._last_failure = time.time()
            if self._failures >= self._max:
                self._state = "open"
                logger.critical(f"Port dead after {self._max} failures")
                raise RuntimeError(f"Port unavailable: {e}") from e
            raise
```

**Justificación**: Circuit Breaker evita reintentos infinitos, proporciona
degradación graceful (el servidor Flask puede reportar "ESP32 offline" en
lugar de quedarse colgado), y permite recuperación automática cuando el
dispositivo vuelve (half-open → closed).

---

## Patrón 7 — Bounded Buffer / Guard Clause

### Problema que resuelve (4.2, 4.3)

**4.2**: `self._buffer` (`reader.py:25`) es `bytearray` sin límite. Un bug de
firmware que no envíe `\n` causa OOM.

**4.3**: `_flush_lines()` procesa cualquier `raw_str` sin verificar tamaño.
Una línea CSI gigante (millones de subportadoras) consume CPU/memoria sin
control.

### Solución planteada

**Bounded Buffer + Guard Clause**: El buffer tiene capacidad máxima. Las
líneas individuales tienen tamaño máximo. Se descartan entradas que excedan
los límites.

```python
class BoundedLineBuffer:
    MAX_BUFFER_SIZE = 1_000_000    # 1 MB
    MAX_LINE_LENGTH = 100_000      # 100 KB por línea

    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data: bytes):
        if len(self._buffer) + len(data) > self.MAX_BUFFER_SIZE:
            logger.warning("Buffer overflow: discarding oldest data")
            self._buffer.clear()
        self._buffer.extend(data)

    def drain_lines(self) -> List[bytes]:
        lines = []
        while b"\\n" in self._buffer:
            raw_bytes, self._buffer = self._buffer.split(b"\\n", 1)
            if len(raw_bytes) > self.MAX_LINE_LENGTH:
                logger.warning(f"Line too long ({len(raw_bytes)} bytes), discarding")
                continue
            lines.append(raw_bytes)
        return lines
```

**Justificación**: Bounded Buffer evita OOM con límite fijo y predecible.
Guard Clause en líneas anómalas previene DoS por datos malformados. Ambas
son protecciones necesarias en un sistema de streaming que opera 24/7.

---

## Patrón 8 — Producer-Consumer

### Problema que resuelve (5.1)

**5.1**: `lines()` (reader.py:81-101) lee y parsea en el mismo hilo. A
921600 baud (~92 KB/s), el parseo puede rezagarse si hay contención de CPU
(Flask atendiendo requests, escritura a disco, etc.). El buffer crece.

### Solución planteada

**Producer-Consumer**: Dos hilos separados por una cola. El productor lee
bytes del serial y los pone en la cola. El consumidor los parsea y produce
`CsiLine`. La cola actúa como buffer acotado.

```python
import threading
from queue import Queue

class AsyncSerialReader(DataSource):
    def __init__(self, port, baud=921600, max_queue=1000):
        self._reader = SerialReader(port, baud)
        self._queue: Queue[CsiLine] = Queue(maxsize=max_queue)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def connect(self) -> bool:
        if not self._reader.connect():
            return False
        self._thread = threading.Thread(target=self._produce, daemon=True)
        self._thread.start()
        return True

    def _produce(self):
        for line in self._reader.lines():
            if self._stop_event.is_set():
                break
            self._queue.put(line)

    def lines(self) -> Generator[CsiLine, None, None]:
        while not self._stop_event.is_set():
            try:
                yield self._queue.get(timeout=1.0)
            except Exception:
                continue

    def disconnect(self):
        self._stop_event.set()
        self._reader.disconnect()
        if self._thread:
            self._thread.join(timeout=2.0)
```

**Justificación**: Producer-Consumer desacopla I/O (bloqueante) de CPU
(parseo). La cola limita el backlog. El pipeline de procesamiento (OE2) puede
consumir `CsiLine` desde la cola sin bloquear la lectura serial. El servidor
Flask mantiene capacidad de respuesta.

---

## Patrón 9 — Builder

### Problema que resuelve (5.2)

**5.2**: `parser.py:18-45` construye `CsiLine` con 25 argumentos posicionales.
Si el firmware cambia el orden de campos, el constructor debe reordenarse
manualmente. Frágil y propenso a desalineación.

### Solución planteada

**Builder**: Separar la construcción del objeto de su representación. Usar
un diccionario de mapeo campo→posición para construir `CsiLine` sin
argumentos posicionales.

```python
FIELD_NAMES = [
    "type", "role", "mac", "rssi", "rate", "sig_mode", "mcs",
    "bandwidth", "smoothing", "not_sounding", "aggregation", "stbc",
    "fec_coding", "sgi", "noise_floor", "ampdu_cnt", "channel",
    "secondary_channel", "local_timestamp", "ant", "sig_len",
    "rx_state", "real_time_set", "real_timestamp", "len",
]

FIELD_PARSERS: dict[str, Callable[[str], Any]] = {
    "type": str,
    "role": lambda v: Role(v) if v in {"AP", "PASSIVE", "STA"} else None,
    "mac": lambda v: v if v else None,
    "rssi": _int,
    "rate": _int,
    "sig_mode": _int,
    "mcs": _int,
    "bandwidth": _int,
    "smoothing": _bool,
    "not_sounding": _bool,
    "aggregation": _bool,
    "stbc": _bool,
    "fec_coding": _bool,
    "sgi": _bool,
    "noise_floor": _int,
    "ampdu_cnt": _int,
    "channel": _int,
    "secondary_channel": _int,
    "local_timestamp": _int,
    "ant": _int,
    "sig_len": _int,
    "rx_state": _int,
    "real_time_set": _bool,
    "real_timestamp": _float,
    "len": _int,
}

def parse_line(raw: str) -> CsiLine:
    parts = raw.strip().split(",")
    if len(parts) < 26:
        raise ValueError(...)
    if parts[0] != "CSI_DATA":
        raise ValueError(...)

    raw_values = dict(zip(FIELD_NAMES, parts[:25]))
    parsed = {name: FIELD_PARSERS[name](raw_values[name])
              for name in FIELD_NAMES}

    csi_data = _parse_csi_bracket(parts[25])

    return CsiLine(csi_data=csi_data, **parsed)
```

**Justificación**: Builder con mapeo explícito elimina dependencia del orden
posicional. Agregar/quitar campos solo requiere modificar `FIELD_NAMES` y
`FIELD_PARSERS`. El mapeo es verificable por inspección directa contra el
formato del firmware (`csi_component.h:27-79`).

---

## Patrón 10 — Interpreter

### Problema que resuelve (6.3)

**6.3**: El formato CSV del firmware no tiene una gramática formal. El
separador es `,` para metadatos y espacio dentro de `[...]` para CSI. No
hay validación de invariantes. Cualquier cambio en el firmware puede romper
el parser silenciosamente.

### Solución planteada

**Interpreter**: Definir una gramática formal para la línea CSI y un parser
que la interprete. La gramática es la especificación ejecutable del formato.

```
Línea       := Prefijo ',' Metadatos ',' CSI_Data
Prefijo     := "CSI_DATA"
Metadatos   := Campo (',' Campo){24}
Campo       := String | Entero | Real | Booleano
CSI_Data    := '[' Entero (Espacio Entero)* ']' | '[' ']'
Entero      := ['-']? Dígito+
Real        := Entero '.' Dígito+
Booleano    := "0" | "1"
```

```python
class CsiGrammar:
    """Define la gramática de la línea CSI como especificación ejecutable."""

    PREFIX = "CSI_DATA"
    FIELD_COUNT = 25          # metadatos
    CSI_DELIMITER_OPEN = "["
    CSI_DELIMITER_CLOSE = "]"
    CSI_SEPARATOR = " "        # espacio entre I/Q
    CSV_SEPARATOR = ","

    @classmethod
    def validate_line(cls, raw: str) -> bool:
        """Valida que raw cumpla la gramática sin parsear."""
        parts = raw.strip().split(cls.CSV_SEPARATOR)
        if len(parts) < 26:
            return False
        if parts[0] != cls.PREFIX:
            return False
        csi = parts[25].strip()
        if not (csi.startswith(cls.CSI_DELIMITER_OPEN) and
                csi.endswith(cls.CSI_DELIMITER_CLOSE)):
            return False
        return True
```

**Justificación**: Interpreter convierte el formato CSV en una especificación
ejecutable y verificable. Los cambios en el firmware se reflejan modificando
la gramática (un solo punto de cambio). `validate_line()` permite detectar
líneas malformadas antes del parseo completo.

---

## Patrón 11 — Visitor

### Problema que resuelve (1.2, 2.3)

**1.2**: `CsiLine` con 26 campos donde la semántica varía por role
(AP/PASSIVE/STA). Un campo puede significar cosas distintas según el rol.

**2.3**: `Role` enum sin operaciones asociadas. La lógica condicional
"if role == AP: ... elif role == PASSIVE: ..." se replica en cada módulo.

### Solución planteada

**Visitor**: Separar las operaciones (que varían por rol) de los datos.
Cada operación es un visitor que se aplica a un `CsiLine` y produce un
resultado según el `Role`.

```python
from abc import ABC, abstractmethod

class CsiVisitor(ABC):
    @abstractmethod
    def visit_ap(self, line: CsiLine):
        ...

    @abstractmethod
    def visit_passive(self, line: CsiLine):
        ...

    @abstractmethod
    def visit_sta(self, line: CsiLine):
        ...

class CsiLine:
    def accept(self, visitor: CsiVisitor):
        if self.role == Role.AP:
            return visitor.visit_ap(self)
        elif self.role == Role.PASSIVE:
            return visitor.visit_passive(self)
        elif self.role == Role.STA:
            return visitor.visit_sta(self)
        raise ValueError(f"Unknown role: {self.role}")

class SubcarrierExtractor(CsiVisitor):
    def visit_ap(self, line: CsiLine) -> np.ndarray:
        # AP: 52 subportadoras de datos (HT-LTF)
        return self._extract_ht_subcarriers(line.csi_data)

    def visit_passive(self, line: CsiLine) -> np.ndarray:
        # PASSIVE: puede ser 52 o 114 según ancho de banda
        bw = line.bandwidth or 0
        return self._extract_vht_subcarriers(line.csi_data, bw)

    def visit_sta(self, line: CsiLine) -> np.ndarray:
        # STA: no captura CSI directamente
        return np.array([])
```

**Justificación**: Visitor centraliza la lógica condicional por rol en
visitors específicos. Agregar una nueva operación (ej. "calcular SSNR por
subportadora") solo requiere crear un nuevo visitor, no modificar `CsiLine`.
Cada visitor es testeable aisladamente por rol.

---

## Patrón 12 — RAII / Scoped Lock

### Problema que resuelve (6.2)

**6.2**: En el firmware, `csi_component.h:20,81-84` toma `mutex` y hace
`vTaskDelay(0)` dentro de la sección crítica. Si el delay causa un cambio
de contexto, otro hilo que espera el mutex puede sufrir starvation.

### Solución planteada

**RAII (Resource Acquisition Is Initialization)**: Usar un scoped lock en C++
que adquiere el mutex al crearse y lo libera al destruirse, minimizando la
sección crítica y eliminando el riesgo de liberación manual incorrecta.

```cpp
// csi_component.h — antes
void _wifi_csi_cb(void *ctx, wifi_csi_info_t *data) {
    xSemaphoreTake(mutex, portMAX_DELAY);
    // ... procesamiento ...
    vTaskDelay(0);           // yield dentro del mutex ← MAL
    // ... más procesamiento ...
    xSemaphoreGive(mutex);
}

// csi_component.h — después
class ScopedLock {
    SemaphoreHandle_t _sem;
public:
    ScopedLock(SemaphoreHandle_t sem) : _sem(sem) {
        xSemaphoreTake(_sem, portMAX_DELAY);
    }
    ~ScopedLock() { xSemaphoreGive(_sem); }
};

void _wifi_csi_cb(void *ctx, wifi_csi_info_t *data) {
    ScopedLock lock(mutex);               // RAII
    // ... procesamiento (mínimo necesario) ...
    // vTaskDelay(0) fuera de la sección crítica
}
// vTaskDelay(0) aquí, después de liberar el mutex
```

**Justificación**: RAII garantiza liberación del mutex incluso en
excepciones o returns tempranos. La sección crítica se reduce al mínimo
indispensable. El yield se mueve fuera del lock. Elimina la posibilidad de
starvation y deadlock.

---

## Patrón 13 — Tagged Union / Algebraic Data Type

### Problema que resuelve (1.2)

**1.2** (alternativa a Visitor): `CsiLine` con 26 campos planos donde la
validez de cada campo depende del role. Sin tipo estático que refleje esta
variación.

### Solución planteada

**Tagged Union**: Modelar la línea CSI como un tipo suma (sum type) donde
cada variante tiene solo los campos relevantes para ese role.

```python
from dataclasses import dataclass
from typing import Union, List, Optional

@dataclass
class ApCsiLine:
    mac: str                    # MAC de la estación conectada
    rssi: int
    channel: int
    secondary_channel: int      # solo relevante en AP
    csi_data: List[int]
    # ... otros campos específicos de AP

@dataclass
class PassiveCsiLine:
    mac: str                    # MAC del transmisor (cualquiera en el canal)
    rssi: int
    channel: int
    csi_data: List[int]
    # sin secondary_channel (no aplica en modo promiscuo)

@dataclass
class StaCsiLine:
    rssi: int
    # sin csi_data (active_sta no captura CSI por serial)

CsiLine = Union[ApCsiLine, PassiveCsiLine, StaCsiLine]
```

**Justificación**: Tagged Union elimina campos `Optional` que no aplican en
ciertos roles. El type checker (mypy/pyright) puede verificar que el código
cliente maneja todas las variantes (exhaustiveness checking con `match`).
Cada variante es un DTO específico con solo los campos necesarios.

---

## Patrón 14 — Adapter

### Problema que resuelve (3.1, variante)

**3.1** (variante a Bridge): Se necesita que `SerialReader` (existente) sea
utilizable donde se espera `DataSource` (nueva abstracción), sin modificar
`SerialReader`.

### Solución planteada

**Adapter**: Envolver `SerialReader` para que implemente `DataSource` sin
cambiar su código.

```python
class SerialReaderAdapter(DataSource):
    def __init__(self, reader: SerialReader):
        self._reader = reader

    def connect(self) -> bool:
        return self._reader.connect()

    def disconnect(self):
        self._reader.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._reader.is_connected

    def lines(self) -> Generator[CsiLine, None, None]:
        yield from self._reader.lines()
```

**Justificación**: Adapter permite integrar código existente con nuevas
abstracciones sin refactor. Útil si `SerialReader` ya está en uso en otros
lugares del sistema.

---

## Matriz de Correspondencia Completa

| Patrón | Problemas | Tipo | Ámbito |
|--------|-----------|------|--------|
| Facade | 1.1, 1.3 | Estructural | Python |
| Strategy | 1.4, 2.3, 6.1 | Comportamiento | Python + C++ |
| Dependency Injection | 2.1, 2.2 | Estructural | Python |
| Bridge | 3.1 | Estructural | Python |
| Pipeline / CoR | 3.2 | Comportamiento | Python |
| Circuit Breaker | 4.1 | Comportamiento | Python |
| Bounded Buffer | 4.2, 4.3 | Concurrencia | Python |
| Producer-Consumer | 5.1 | Concurrencia | Python |
| Builder | 5.2 | Creacional | Python |
| Interpreter | 6.3 | Comportamiento | Python |
| Visitor | 1.2, 2.3 | Comportamiento | Python |
| RAII / Scoped Lock | 6.2 | Concurrencia | C++ |
| Tagged Union (ADT) | 1.2 | Estructural | Python |
| Adapter | 3.1 | Estructural | Python |
| Refactor: Rename Field | 5.3 | — | Python |

---

## Prioridad de Implementación

| Prioridad | Patrón(es) | Justificación |
|-----------|------------|---------------|
| **Alta** | Bridge (3.1), Pipeline (3.2) | Sin estas abstracciones, el pipeline de procesamiento (OE2) no se puede implementar ni probar sin hardware |
| **Alta** | Circuit Breaker (4.1), Bounded Buffer (4.2-4.3) | Seguridad del sistema: reintentos infinitos y OOM son fallos críticos en servidor 24/7 |
| **Media** | Facade (1.1, 1.3), Dependency Injection (2.1, 2.2) | Mejoran testabilidad y encapsulamiento, pero el código actual funciona |
| **Media** | Strategy (1.4, 2.3), Builder (5.2) | Preparan el código para cambios futuros en el formato del firmware |
| **Baja** | Visitor (1.2), Tagged Union (1.2), RAII (6.2), Interpreter (6.3) | Refinamientos que mejoran mantenibilidad pero no bloquean funcionalidad |
| **Cosmética** | Rename Field (5.3) | Confusión menor, sin impacto funcional |
