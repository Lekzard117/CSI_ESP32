# Data Model — CSI Line Protocol

## CsiLine

Entidad que representa una línea CSI parseada.

| Campo             | Tipo       |Posición CSV | Descripción                                                 |
|-------------------|------------|-------------|-------------------------------------------------------------|
| type              | str        | 1           | Prefijo fijo `CSI_DATA` |
| role              | Enum(Role) | 2           | `AP`, `PASSIVE`, `STA` |
| mac               | str        | 3           | MAC origen `XX:XX:XX:XX:XX:XX` |
| rssi              | int        | 4           | -90 a -20 dBm |
| rate              | int        | 5           | Tasa PHY |
| sig_mode          | int        | 6           | 0=non-HT, 1=HT, 3=VHT |
| mcs               | int        | 7           | 0-76 |
| bandwidth         | int        | 8           | 0=20MHz, 1=40MHz |
| smoothing         | bool       | 9           | Suavizado |
| not_sounding      | bool       | 10          | PPDU sounding |
| aggregation       | bool       | 11          | 0=MPDU, 1=AMPDU |
| stbc              | bool       | 12          | Space-Time Block Code |
| fec_coding        | bool       | 13          | LDPC |
| sgi               | bool       | 14          | Short Guard Interval |
| noise_floor       | int        | 15          | Piso de ruido dBm |
| ampdu_cnt         | int        | 16          | Subtramas AMPDU |
| channel           | int        | 17          | Canal 1-13 |
| secondary_channel | int        | 18          | 0=none, 1=above, 2=below |
| local_timestamp   | int        | 19          | Microsegundos ESP32 |
| ant               | int        | 20          | 0=ANT0, 1=ANT1 |
| sig_len           | int        | 21          | Bytes del paquete |
| rx_state          | int        | 22          | 0=ok, !=0=error |
| real_time_set     | bool       | 23          | Reloj sincronizado |
| real_timestamp    | float      | 24          | Segundos steady_clock |
| len               | int        | 25          | Longitud buffer CSI_DATA |
| csi_data          | list[int]  | 26+         | Valores I/Q interleaved int8 entre `[...]`, separados por espacio |

## CsiBuffer

Buffer de acumulación para reconstruir líneas desde el stream.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| buffer | bytearray | Bytes acumulados sin `\n` |
| line_count | int | Contador de líneas parseadas |
| error_count | int | Contador de líneas malformadas |
| last_rx | datetime | Timestamp del último byte recibido |

## Estados del lector serial

| Estado | Descripción |
|--------|-------------|
| DISCONNECTED | Puerto no abierto o desconectado |
| CONNECTING | Intentando abrir puerto |
| STREAMING | Recibiendo datos activamente |
| TIMEOUT | Sin datos por >5 segundos |
| ERROR | Error de puerto irrecuperable |
