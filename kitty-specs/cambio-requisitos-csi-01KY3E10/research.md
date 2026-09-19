# Research: Cambio de requisitos CSI

## Campos esenciales

### Análisis de cada campo del formato original (26 campos)

| #  | Campo | Utilidad | Decisión |
|----|-------|----------|----------|
| 0  | type | Siempre "data" para CSI | Eliminar |
| 1  | role | Identificador de rol | Eliminar (MAC suficiente) |
| 2  | mac | Dirección MAC del dispositivo | **Conservar** — identificador único |
| 3  | rssi | Potencia de señal (dBm) | **Conservar** — filtro de calidad + detección complementaria |
| 4  | rate | Tasa de datos WiFi | Eliminar |
| 5  | sig_mode | Modo de señal | Eliminar |
| 6  | mcs | Modulation Coding Scheme | Eliminar |
| 7  | bandwidth | Ancho de banda | Eliminar |
| 8  | smoothing | Smoothing flag | Eliminar |
| 9  | not_sounding | Sounding flag | Eliminar |
| 10 | aggregation | Agregación | Eliminar |
| 11 | stbc | STBC flag | Eliminar |
| 12 | fec_coding | FEC coding | Eliminar |
| 13 | sgi | Short Guard Interval | Eliminar |
| 14 | noise_floor | Piso de ruido | Eliminar |
| 15 | ampdu_cnt | Conteo A-MPDU | Eliminar |
| 16 | channel | Canal WiFi | **Conservar** — necesario para interpretar subportadoras |
| 17 | secondary_channel | Canal secundario | Eliminar |
| 18 | local_timestamp | Timestamp ESP32 (µs) | **Conservar** — esencial para sincronización |
| 19 | ant | Antena receptora | **Conservar** — CSI difiere por antena |
| 20 | sig_len | Longitud de señal | Eliminar |
| 21 | rx_state | Estado del receptor | Eliminar |
| 22 | real_time_set | Timestamp PC (set) | Eliminar (post-procesamiento) |
| 23 | real_timestamp | Timestamp PC (real) | Eliminar (post-procesamiento) |
| 24 | len | Número de valores I/Q | **Conservar** — necesario para leer CSI_DATA |
| 25 | CSI_DATA | Valores I/Q crudos | **Conservar** — núcleo del análisis |

### Formato propuesto (7 campos)

```
mac,rssi,channel,local_timestamp,ant,len,CSI_DATA
```

### Tasa de baudios

- **Decisión**: Mantener 921600 baud
- **Justificación**: El formato reducido (7 campos, ~180 bytes/línea) vs 26 campos (~400 bytes) reduce el ancho de banda necesario. A 921600 baud (~92 KB/s) caben ~500 líneas/s, suficiente para CSI a 100 Hz.
- **Alternativa considerada**: 115200 baud — insuficiente para ráfagas de datos CSI
