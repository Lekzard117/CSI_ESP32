# Data Model: Formato CSI Reducido

## CsiLine (7 campos)

```
mac: str          — Dirección MAC del dispositivo (XX:XX:XX:XX:XX:XX)
rssi: int         — Potencia de señal recibida en dBm
channel: int      — Canal WiFi (1-14)
local_timestamp: int — Timestamp interno ESP32 en microsegundos
ant: int          — Antena que recibió la trama (0 o 1)
len: int          — Número de valores I/Q en CSI_DATA
csi_data: List[int] — Valores I/Q de subportadoras
```

### Invariante

- `len` debe coincidir con `len(csi_data)`
- `rssi` debe estar en rango [-120, 0] dBm
- `mac` debe ser una MAC válida (formato XX:XX:XX:XX:XX:XX)

## Formato CSV

```
CSI_DATA,mac,rssi,channel,local_timestamp,ant,len,[+1, +2, ...]
```

## Role

Eliminado. La MAC identifica el dispositivo. El firmware ya no incluye `role` en la línea serial.

## Migración

Script `migrate_csv.py` para convertir datasets existentes (26 campos → 7 campos):
- Lee cabecera original, extrae solo los 7 campos, descarta el resto
- Reordena al nuevo orden: mac, rssi, channel, local_timestamp, ant, len, CSI_DATA
