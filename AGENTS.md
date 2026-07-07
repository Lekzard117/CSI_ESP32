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

# Flashear y monitorear salida serial (921600 baudios recomendado)
idf.py -p /dev/ttyUSB0 flash monitor

# Solo flashear
idf.py -p /dev/ttyUSB0 flash

# Salir del monitor: Ctrl+]
```

La configuración vive en `sdkconfig` por subproyecto (no se comparte). Ajustes clave en `menuconfig`:
- `Serial flasher config > Custom baud rate > 921600`
- `Component config > WiFi > WiFi CSI(Channel State Information)` — debe estar habilitado
- `Component config > FreeRTOS > Tick rate (Hz) > 1000`
- `ESP32 CSI Tool Config` — ajustes específicos del rol

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

## Sincronización de tiempo

- El AP difunde su timestamp a las estaciones conectadas automáticamente
- Manual: escribir `SETTIME:<unix_seconds>` en `idf.py monitor` y Enter
- Tubería a través de `serial_append_time.py` añade timestamps de la PC local

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
