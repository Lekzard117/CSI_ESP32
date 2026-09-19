# CSI-ESP

Proyecto académico de investigación: Recolección y Procesamiento de Señales WiFi mediante CSI para Detección de Movimiento.

## Estructura del proyecto

```
CSI-ESP/                          # Repo raíz (fresco, cero commits)
  ESP32-CSI-Tool/                 # Fork del repo upstream (tiene su propio .git, historial real)
    active_sta/                   # Transmisor CSI (modo estación, se conecta a un AP)
    active_ap/                    # Receptor CSI (modo AP, otros dispositivos se conectan a él)
    passive/                      # Monitor CSI pasivo (modo promiscuo)
    _components/                  # Headers C++ compartidos entre todos los subproyectos
    python_utils/                 # Utilidades Python para serial
  DocLatex/                       # Reportes LaTeX (avance + final)
  fnts/                           # Artículos de investigación (gitignorados)
  PROJECT_OVERVIEW.md             # Plan de arquitectura (español)
```

## Arquitectura (planeada, parcialmente implementada)

Sistema de tres capas: **Emisor ESP32 → Receptor ESP32 → Servidor Flask**

- `active_sta` — envía paquetes (rol TX)
- `active_ap`  — recibe CSI de estaciones conectadas (rol RX)
- `passive`    — escucha pasivamente en un canal (monitor promiscuo)

Solo la capa de firmware ESP32 tiene código. El servidor Flask y el pipeline de procesamiento CSI (compensación AGC, filtros Hampel/Butterworth/Savitzky-Golay, sustracción de fondo) aún no están implementados.

## Configuración inicial

```bash
# Activar ESP-IDF v6.0.1 (obligatorio antes de cualquier comando idf.py)
source ~/.espressif/tools/activate_idf_v6.0.1.sh

# Las utilidades Python necesitan:
pip install numpy matplotlib
```

## Comandos ESP-IDF

```bash
# Configurar ajustes específicos del proyecto
idf.py menuconfig 

# Limpiar y reconstruir desde cero
idf.py fullclean && idf.py build

# Flashear y monitorear salida serial (921600 si se aplica sdkconfig.defaults)
idf.py -p /dev/ttyUSB0 flash monitor

# Solo flashear
idf.py -p /dev/ttyUSB0 flash

# Salir del monitor: Ctrl+]
```

La configuración vive en `sdkconfig` por subproyecto (no se comparte). Ajustes clave en `menuconfig`:
- `Serial flasher config > Custom baud rate > 921600` (default: 115200 — ver anomalía más abajo)
- `Component config > WiFi > WiFi CSI(Channel State Information)` — debe estar habilitado
- `Component config > FreeRTOS > Tick rate (Hz) > 1000`
- `ESP32 CSI Tool Config` — ajustes específicos del rol

**Baud rate actual**: 115200 (ambos dispositivos). El upstream recomienda 921600 pero requiere `sdkconfig.defaults` para persistir tras limpieza/reconfiguración.

## Mapeo de puertos (verificado 2026-09-07)

| Puerto | Dispositivo | MAC | Baud | Role |
|---|---|---|---|---|
| `/dev/ttyUSB0` | ESP32 #1 | FC:B4:67:F5:23:28 / 08:B6:1F:B9:90:2C | 115200 | **ACTIVE_AP** (receptor) |
| `/dev/ttyUSB1` | ESP32 #2 | 08:B6:1F:B9:90:2D | 115200 | **ACTIVE_STA** (transmisor) |

El STA se conecta a `myssid` (AP del USB0) y genera tráfico UDP. El AP captura CSI del uplink STA→AP.

## Formato de datos CSI

Salida CSV por serial, cada línea prefijada con `CSI_DATA`. Cabecera:
```
type,role,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_state,real_time_set,real_timestamp,len,CSI_DATA
```

Capturar a archivo:
```bash
# Captura cruda
idf.py monitor | grep "CSI_DATA" > experimento.csv

# Con timestamp de PC añadido
idf.py monitor | python ../python_utils/serial_append_time.py > experimento.csv
```

Gráfico de amplitud en vivo:
```bash
idf.py monitor | python ../python_utils/serial_plot_csi_live.py
```

## Correcciones de compatibilidad aplicadas

`active_ap` y `passive` fueron actualizados para ESP-IDF v6.0.1:
- Se reemplazó `#include "esp_spi_flash.h"` (obsoleto) por `#include "esp_flash.h"`
- Se añadió `#include "esp_mac.h"` para las macros MAC2STR/MACSTR

`active_sta` aún usa `esp_spi_flash.h` — potencialmente roto en IDF 6.x.

## Anomalía del baud rate y procedimiento para subir a 921600

### Contexto

El proveedor (README.md líneas 63-72) **recomienda 921600 baud**:
> "The higher baud rate the better! Baud rate is extremely important to achieve high sampling rates without lag!"

A 115200 baud, cada línea CSI_DATA (~500 bytes) limita la tasa real a ~9 CSI/s, muy por debajo del `PACKET_RATE=100` configurado. Subir a 921600 permite ~70-80 CSI/s reales.

### Anomalía

En ESP-IDF v6.0.1, los cambios manuales al `sdkconfig` se pierden al ejecutar:

| Comando | Efecto sobre sdkconfig |
|---|---|
| `idf.py reconfigure` | Regenera desde defaults del Kconfig (115200) |
| `idf.py menuconfig` | Requiere TTY interactivo — no funciona desde CLI |
| `idf.py fullclean` + `idf.py build` | Genera nuevo sdkconfig con defaults (115200) |
| `idf.py flash` | Puede invocar `reconfigure` implícitamente |

El resultado es que los baud rates vuelven a 115200 tras cualquier ciclo de limpieza/reconfiguración.

### Solución: `sdkconfig.defaults`

ESP-IDF mergea `sdkconfig.defaults` sobre el sdkconfig incluso tras `fullclean`. Es la forma correcta de fijar valores que no se pierdan:

```bash
# En el directorio del proyecto (ej. active_ap/)
cat > sdkconfig.defaults << 'EOF'
CONFIG_ESPTOOLPY_MONITOR_BAUD=921600
CONFIG_MONITOR_BAUD=921600
CONFIG_ESP_CONSOLE_UART_BAUDRATE=921600
CONFIG_CONSOLE_UART_BAUDRATE=921600
# CONFIG_SHOULD_COLLECT_ONLY_LLTF is not set
EOF

# Luego limpiar y flashear (con reconfigure implícito, pero sdkconfig.defaults persiste)
idf.py fullclean
idf.py -p /dev/ttyUSB0 flash
```

**Nota**: `idf.py flash` invoca `reconfigure` + `build` + `flash` implícitamente, y los defaults se aplican correctamente.

### Limitaciones verificadas

- CP2102/CH340 en Linux soportan 921600 sin problemas — no hay limitación de hardware
- La dificultad es **exclusivamente del flujo de compilación de ESP-IDF** en entornos no-interactivos
- Si se trabaja desde terminal interactiva, `idf.py menuconfig` es la forma más directa

## Sincronización de tiempo

- El AP difunde su timestamp a las estaciones conectadas automáticamente
- Manual: escribir `SETTIME:<unix_seconds>` en `idf.py monitor` y Enter
- Tubería a través de `serial_append_time.py` añade timestamps de la PC local

## Hardware disponible

Estado actual (reportado 2026-07-07):
- **ESP32 #1**: Operativo — puede flashearse sin problemas
- **ESP32 #2**: Operativo — puede flashearse sin problemas
- **ESP32 #3**: **DADO DE BAJA** — pin TX (GPIO1) dañado o bridge USB-UART defectuoso. Sin respuesta del bootloader vía UART. No recuperable sin adaptador USB-serial externo. (Recovery intentado 2026-07-07, veredicto: no recuperable con herramientas actuales)

### Implicaciones en la arquitectura

Con solo 2 dispositivos ESP32 funcionales no se pueden ocupar los 3 roles (active_sta, active_ap, passive) simultáneamente en hardware dedicado. Las configuraciones disponibles son:

#### Configuración A: AP + smartphone (seleccionada)

| Dispositivo A | Generador de tráfico |
|---|---|
| active_ap (RX) | Smartphone u otro dispositivo WiFi |

El smartphone se conecta al AP del ESP32 y genera tráfico que el firmware captura con CSI. Setup simple, no requiere emisor ESP32 dedicado.

**Ventaja**: No necesita un ESP32 para transmitir — un dispositivo móvil es suficiente.
**Desventaja**: Menos control sobre los parámetros de transmisión (potencia, tasa, MCS).

#### Configuración B: active_sta + active_ap (alternativa)

| Dispositivo A | Dispositivo B | Generador de tráfico |
|---|---|---|
| active_ap (RX) | active_sta (TX) | El propio active_sta |

Ambos ESP32 se utilizan: uno como punto de acceso (active_ap) y otro como estación conectada (active_sta) que genera tráfico. Setup clásico TX/RX con control completo.

**Ventaja**: Control total sobre tráfico (tasa, MCS, intervalo, payload).
**Desventaja**: Consume ambos ESP32; no queda repuesto para passive.

**Nota**: El modo `passive` (promiscuo) no se usará en la configuración inicial — el smartphone se conecta activamente al `active_ap` y genera tráfico que el AP captura con CSI. Esto es un setup válido y común en investigación CSI.

Ambas configuraciones pueden intercambiarse flasheando el firmware correspondiente en cada dispositivo, sin necesidad de hardware adicional.

## Notas

- `active_sta` aún incluye `#include "esp_spi_flash.h"` — puede necesitar la misma correción que `active_ap` y `passive`
- La carpeta `ESP32-CSI-Tool/` tiene su propio `.git` con remote upstream; no confundir con el repo raíz
- `.gitignore` tiene patrones amplios (`.pdf`, `.txt`, `__pycache__/`) que pueden ocultar archivos

<!-- spec-kitty:orientation -->
**Spec Kitty v3.2.1** — project: unknown (healthy)

Two usage patterns:
- **Full mission** (spec → plan → tasks → implement → review → merge):
  trigger: "spec out", "create a mission", "write a spec", "plan this"
  → run `/spec-kitty.specify`
- **Lightweight dispatch** (ad-hoc fix, question, or advice — no mission created):
  trigger: "hey spec kitty", "use spec kitty to", "spec kitty <anything>"
  → **ALWAYS run `spec-kitty dispatch "<request verbatim>"` — do NOT answer directly.**
  If you know the right profile, pass it to skip routing:
  `spec-kitty dispatch "<request verbatim>" --profile <profile-id>`
  Reason: `spec-kitty dispatch` loads governance context, routes the request,
  and opens the Op. Skipping it produces ungoverned, untracked responses.
  After finishing the work, close the Op with the command printed in the capsule
  (`spec-kitty profile-invocation complete --invocation-id <id> --outcome <done|failed|abandoned>`).
<!-- /spec-kitty:orientation -->
