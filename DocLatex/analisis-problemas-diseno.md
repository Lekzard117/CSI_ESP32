# Análisis de Problemas de Diseño — CSI-ESP

Basado en el código actual (`src/flask_serial/`, firmware `ESP32-CSI-Tool/_components/`)
y la arquitectura planeada.

---

## 1. Asignación de Responsabilidades

### 1.1 Acoplamiento `commands.py` → `reader._ser`

- **Archivo**: `src/flask_serial/commands.py:17,29`
- **Problema**: `send_settime()` y `send_reset()` acceden a `reader._ser` (atributo privado) directamente.
- **Consecuencia**: Si `SerialReader` cambia su implementación interna (ej. uso de `aiofiles` asíncrono o pipes), `commands.py` se rompe. Viola encapsulamiento.
- **Solución**: Añadir método público `SerialReader.write(bytes)`.

### 1.2 `CsiLine` como DTO monolítico

- **Archivo**: `src/flask_serial/models.py:14-41`
- **Problema**: `CsiLine` tiene 26 campos planos. La responsabilidad de _transportar datos_ y _validar formato_ están mezcladas — cualquier campo puede ser `None`, pero la semántica de cada campo depende del role (AP vs PASSIVE vs STA).
- **Consecuencia**: El consumidor debe revisar `line.role` antes de interpretar `line.mac` o `line.rssi`. No hay tipos diferenciados por contexto.
- **Solución**: Modelar subtipos: `ApCsiLine`, `PassiveCsiLine`, `StaCsiLine` con constructores específicos, o usar un Tagged Union. Alternativa: `CsiLine` como DTO puro + `RoleContext` aplicado en el pipeline.

### 1.3 `SerialReader` mezcla transporte y estado

- **Archivo**: `src/flask_serial/reader.py:20-101`
- **Problema**: `SerialReader` maneja conexión (`connect`/`disconnect`), bufferización (`_buffer`), parseo (`_flush_lines`), conteo (`line_count`, `error_count`) y timeout. Al menos 4 responsabilidades distintas en una clase.
- **Consecuencia**: Si se requiere un lector asíncrono o basado en archivos, no hay interfaz separable. El acoplamiento a `pyserial` es fuerte.
- **Solución**: Extraer `LineBuffer` (responsabilidad de acumular bytes y partir por `\n`), `ConnectionManager` (conectar/reconectar), y que `SerialReader` sea una fachada simple.

### 1.4 `CsiParser` no existe como módulo

- **Archivo**: `src/flask_serial/parser.py:6`
- **Problema**: `parse_line()` es una función suelta, no un objeto con estado. No permite inyección de configuraciones (ej. modo estricto vs permisivo, formato alternativo de brackets).
- **Consecuencia**: No se puede tener dos instancias con configuraciones distintas sin recurrir a kwargs en cada llamada.
- **Solución**: Clase `CsiParser(config: ParserConfig)` que permita variaciones del formato sin modificar la función global.

---

## 2. Relaciones entre Clases / Componentes

### 2.1 Dependencia cíclica potencial: `commands` ↔ `reader`

- **Archivos**: `commands.py:7` → `from flask_serial.reader import SerialReader`; `reader.py:12` → `from flask_serial.parser import parse_line`
- **Problema**: Aunque no hay ciclo directo (`commands → reader → parser`), la cadena crea un acoplamiento descendente rígido. Cualquier cambio en `parser` propaga a `reader` y potencialmente a `commands`.
- **Consecuencia**: Dificulta pruebas unitarias aisladas y sustitución de componentes (ej. mockear parser para probar reader requiere parches profundos).
- **Solución**: Invertir dependencias: `SerialReader` recibe `parse_line` como dependencia inyectada (`Callable[[str], CsiLine]`).

### 2.2 `create_readers()` acoplada a variable de entorno

- **Archivo**: `src/flask_serial/reader.py:104-111`
- **Problema**: `create_readers()` lee `os.getenv("SERIAL_PORTS")` directamente. No hay forma de pasar configuraciones desde Flask o desde tests sin parchear `os.environ`.
- **Consecuencia**: Tests de integración requieren `monkeypatch.setenv`, y el servidor Flask no puede leer puertos desde su propia configuración (ej. `config.py`).
- **Solución**: `create_readers(ports: Optional[str] = None)` que reciba el string como parámetro, delegando la obtención al llamador.

### 2.3 `Role` enum infrautilizado

- **Archivo**: `src/flask_serial/models.py:8-11`
- **Problema**: `Role` tiene 3 valores pero ningún comportamiento asociado. En el firmware, `project_type` determina el formato CSV, la frecuencia de captura y los comandos disponibles. En el modelo, `role` solo es un tag pasivo.
- **Consecuencia**: Cualquier lógica condicional basada en rol (ej. "si es PASSIVE, ignorar campo X") queda dispersa en los consumidores.
- **Solución**: Métodos en `Role` como `Role.is_receiver() → bool`, `Role.csv_field_count() → int`, o usar un `RoleContext` que encapsule las diferencias.

---

## 3. Falta de Abstracción / Interfaces

### 3.1 Sin interfaz `DataSource`

- **Archivo**: `src/flask_serial/reader.py`
- **Problema**: No hay una interfaz abstracta para la fuente de datos. `SerialReader` es concreto. No se puede implementar un `FileReader`, `MockReader` o `WebSocketReader` sin cambiar el código cliente.
- **Consecuencia**: Las pruebas unitarias del pipeline de procesamiento (OE2) requieren un ESP32 real o mocks complejos.
- **Solución**: Definir `protocol DataSource: def lines() -> Generator[CsiLine]` e implementar `SerialReader`, `MockReader`, `CsvFileReader` contra ella.

### 3.2 Sin interfaz `CsiProcessor`

- **Problema**: No existe una abstracción para el pipeline de procesamiento. Cada etapa (AGC, Hampel, Butterworth, sustracción de fondo) debería implementar `CsiProcessor(stage: StageConfig)` con un método `process(frame: CsiFrame) → CsiFrame`.
- **Consecuencia**: El pipeline será una secuencia lineal de llamadas sin posibilidad de reordenar, saltar etapas, o componer dinámicamente.
- **Solución**: Patrón Pipeline/Chain of Responsibility con etapas configurables y reutilizables.

---

## 4. Manejo de Errores / Casos Borde

### 4.1 Reintento infinito en `reconnect()`

- **Archivo**: `src/flask_serial/reader.py:62-65,84-88,96-101`
- **Problema**: `lines()` llama a `reconnect()` en timeout y en `SerialException`, y `reconnect()` a su vez llama a `connect()` sin límite de intentos. Si el puerto está muerto (GPIO1 dañado), el bucle es infinito.
- **Consecuencia**: El servidor Flask nunca detecta un "dead port" y sigue intentando para siempre.
- **Solución**: Añadir `max_retries: int = 5` con conteo; si se excede, elevar `RuntimeError` en lugar de reintentar.

### 4.2 Buffer sin límite máximo

- **Archivo**: `src/flask_serial/reader.py:25-68`
- **Problema**: `self._buffer` es un `bytearray` sin límite de crecimiento. Si el ESP32 envía datos sin `\n` (firmware bug), el buffer crece sin control (OOM).
- **Consecuencia**: El servidor puede quedarse sin memoria.
- **Solución**: Añadir `MAX_BUFFER_SIZE = 1_000_000` bytes; si se excede, descartar y loguear advertencia.

### 4.3 `_flush_lines()` no protege contra líneas anómalas largas

- **Archivo**: `src/flask_serial/reader.py:67-79`
- **Problema**: Si `raw_str` es extremadamente larga (ej. `[I Q...]` con miles de valores I/Q por un bug de firmware), el decode y parseo pueden consumir recursos excesivos.
- **Consecuencia**: Potencial DoS por una línea malformada gigante.
- **Solución**: Descartar líneas que excedan `MAX_LINE_LENGTH = 1_000_000` caracteres.

---

## 5. Problemas de Rendimiento

### 5.1 Parseo síncrono en el mismo hilo que lectura

- **Archivo**: `src/flask_serial/reader.py:81-101`
- **Problema**: `lines()` es un generador que parsea en el mismo hilo que lee. A 921600 baud (~92000 bytes/segundo), el parseo puede rezagarse si el CPU está ocupado.
- **Consecuencia**: El buffer crece porque el parseo no da abasto.
- **Solución**: Productor/consumidor con dos hilos: uno lee bytes y acumula, otro parsea. O usar `asyncio` con `aiofiles` para I/O no bloqueante.

### 5.2 Construcción de `CsiLine` con kwargs expandidos por posición

- **Archivo**: `src/flask_serial/parser.py:18-45`
- **Problema**: La construcción de `CsiLine` pasa 25 argumentos posicionales. Cualquier cambio en el orden de campos del firmware (ej. nueva versión de ESP32-CSI-Tool) requiere reorden manual de todo el constructor.
- **Consecuencia**: Mantenimiento frágil y propenso a errores de desalineación.
- **Solución**: Mapear por nombre de campo usando un dict intermedio: `field_names = ["type","role","mac",...]` y `kwargs = dict(zip(field_names, parts[:25]))`.

### 5.3 `len` como nombre de campo sombrea built-in

- **Archivo**: `src/flask_serial/models.py:40`
- **Problema**: El campo `len` sombrea la función `len()`. Aunque es válido (el built-in no se pierde dentro de la clase), cualquier código fuera de `CsiLine` que haga `from flask_serial.models import len` sería ambiguo.
- **Consecuencia**: Riesgo bajo pero confusión en el código cliente.
- **Solución**: Renombrar a `csi_len` o `data_len` en el modelo, manteniendo el mapeo CSV original.

---

## 6. Firmware ESP32-CSI-Tool

### 6.1 Ruta de salida a SD es código muerto

- **Archivo**: `ESP32-CSI-Tool/_components/sd_component.h:82-97`
- **Problema**: `outprintf()` está diseñada para enviar a serial + SD simultáneamente, pero `_wifi_csi_cb` (`csi_component.h:81`) llama a `printf()` directamente. La SD nunca recibe datos CSI.
- **Solución**: Cambiar `printf()` por `outprintf()` en el callback, o eliminar el path SD si no se usará.

### 6.2 `vTaskDelay(0)` dentro de mutex

- **Archivo**: `ESP32-CSI-Tool/_components/csi_component.h:81-84`
- **Problema**: Se hace `vTaskDelay(0)` (cooperative yield) mientras se sostiene `mutex`. Esto puede causar starvation de tareas de mayor prioridad que esperan el mutex.
- **Solución**: Mover `vTaskDelay` fuera de la sección crítica, después de `xSemaphoreGive`.

### 6.3 Formato de línea sin escape de comas en campo CSI

- **Archivo**: `ESP32-CSI-Tool/_components/csi_component.h:61-78`
- **Problema**: Si `CSI_RAW` produce valores negativos con signo, la línea CSV se vuelve ambigua (comas vs signos). El bracket `[...]` delimita el campo, pero no hay validación.
- **Consecuencia**: El parseo por `split(",")` separaría valores si hubiera comas dentro del bracket. Actualmente no hay comas (solo espacios), pero es frágil.
- **Solución**: Documentar como invariante que el campo CSI no contiene comas, o escapar.

---

## Resumen por Categoría

| Categoría | Problemas | Severidad |
|-----------|-----------|-----------|
| Asignación de responsabilidades | 1.1, 1.2, 1.3, 1.4 | Media |
| Relaciones entre clases | 2.1, 2.2, 2.3 | Media |
| Falta de abstracciones/interfaces | 3.1, 3.2 | Alta |
| Manejo de errores/casos borde | 4.1, 4.2, 4.3 | Alta |
| Rendimiento | 5.1, 5.2, 5.3 | Media-baja |
| Firmware | 6.1, 6.2, 6.3 | Media |

**Prioridad de corrección sugerida**: 3.1, 4.1, 4.2 → 1.1, 2.2, 5.2 → 1.2, 2.1, 5.3 → resto.
