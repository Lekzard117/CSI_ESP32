# CSI Line Protocol Specification

## Physical Layer

| Parameter | Value |
|-----------|-------|
| Protocol | UART 8N1 (8 bits, no parity, 1 stop) |
| Baud rate | 921600 |
| Voltage | 3.3V TTL |
| Flow control | None |
| Line delimiter | `\n` (0x0A) |
| Encoding | UTF-8 |

## Line Format

```
CSI_DATA,<role>,<mac>,<rssi>,<rate>,<sig_mode>,<mcs>,<bandwidth>,<smoothing>,<not_sounding>,<aggregation>,<stbc>,<fec_coding>,<sgi>,<noise_floor>,<ampdu_cnt>,<channel>,<secondary_channel>,<local_timestamp>,<ant>,<sig_len>,<rx_state>,<real_time_set>,<real_timestamp>,<len>,[<I0> <Q0> <I1> <Q1> ...]
```

26 fields total: 25 comma-separated metadata + 1 bracketed CSI data.

## Fields

| Pos | Name | Type | Description |
|-----|------|------|-------------|
| 1 | `type` | string | Fixed `CSI_DATA` |
| 2 | `role` | enum | `AP`, `PASSIVE`, `STA` |
| 3 | `mac` | string | Source MAC |
| 4 | `rssi` | int | dBm (-90 to -20) |
| 5 | `rate` | int | PHY rate index |
| 6 | `sig_mode` | int | 0=non-HT, 1=HT, 3=VHT |
| 7 | `mcs` | int | 0-76 |
| 8 | `bandwidth` | int | 0=20MHz, 1=40MHz |
| 9-14 | `smoothing`..`sgi` | bool | WiFi flags |
| 15 | `noise_floor` | int | dBm |
| 16 | `ampdu_cnt` | int | AMPDU subframes |
| 17-18 | `channel`, `secondary_channel` | int | WiFi channel |
| 19 | `local_timestamp` | int | ESP32 microseconds |
| 20 | `ant` | int | 0=ANT0, 1=ANT1 |
| 21 | `sig_len` | int | Packet bytes |
| 22 | `rx_state` | int | 0=ok, !=0=error |
| 23 | `real_time_set` | bool | Clock synced |
| 24 | `real_timestamp` | float | Steady clock seconds |
| 25 | `len` | int | CSI buffer length |
| 26 | `csi_data` | int[] | I/Q interleaved, bracket+space |

## Control Commands

| Command | Format | Description |
|---------|--------|-------------|
| SETTIME | `SETTIME:<unix_seconds>\n` | Sync ESP32 clock |
| RESET | `RESET\n` | Software reset |

ESP32 does not ACK commands.

## Source

Format defined in `_components/csi_component.h:27-79` of ESP32-CSI-Tool firmware.
