# CSI Line Protocol Specification

## Physical Layer

| Parameter | Value |
|-----------|-------|
| Protocol | UART 8N1 (8 bits, no parity, 1 stop) |
| Baud rate | 921600 |
| Voltage | 3.3V TTL |
| TX pin (ESP32) | GPIO1 (TXD0) |
| Flow control | None |
| Line delimiter | `\n` (0x0A) |
| Encoding | UTF-8 |

## Line Format

Each CSI data line follows this structure:

```
CSI_DATA,<role>,<mac>,<rssi>,<rate>,<sig_mode>,<mcs>,<bandwidth>,<smoothing>,<not_sounding>,<aggregation>,<stbc>,<fec_coding>,<sgi>,<noise_floor>,<ampdu_cnt>,<channel>,<secondary_channel>,<local_timestamp>,<ant>,<sig_len>,<rx_state>,<real_time_set>,<real_timestamp>,<len>,[<I0> <Q0> <I1> <Q1> ...]
```

### Fields

| Pos | Name | Type | Description |
|-----|------|------|-------------|
| 1 | `type` | string | Fixed prefix `CSI_DATA` |
| 2 | `role` | enum | `AP`, `PASSIVE`, or `STA` |
| 3 | `mac` | string | Source MAC address (`XX:XX:XX:XX:XX:XX`) |
| 4 | `rssi` | int | RSSI in dBm (-90 to -20) |
| 5 | `rate` | int | PHY rate index |
| 6 | `sig_mode` | int | 0=non-HT, 1=HT, 3=VHT |
| 7 | `mcs` | int | MCS index (0-76) |
| 8 | `bandwidth` | int | 0=20MHz, 1=40MHz |
| 9 | `smoothing` | bool | Channel smoothing |
| 10 | `not_sounding` | bool | PPDU sounding |
| 11 | `aggregation` | bool | 0=MPDU, 1=AMPDU |
| 12 | `stbc` | bool | Space-Time Block Code |
| 13 | `fec_coding` | bool | LDPC |
| 14 | `sgi` | bool | Short Guard Interval |
| 15 | `noise_floor` | int | Noise floor in dBm |
| 16 | `ampdu_cnt` | int | AMPDU subframe count |
| 17 | `channel` | int | WiFi channel (1-13) |
| 18 | `secondary_channel` | int | 0=none, 1=above, 2=below |
| 19 | `local_timestamp` | int | ESP32 microsecond counter |
| 20 | `ant` | int | 0=ANT0, 1=ANT1 |
| 21 | `sig_len` | int | Packet length in bytes |
| 22 | `rx_state` | int | 0=ok, !=0=error |
| 23 | `real_time_set` | bool | Clock synchronization flag |
| 24 | `real_timestamp` | float | Steady clock seconds |
| 25 | `len` | int | CSI buffer length |
| 26 | `csi_data` | int[] | I/Q interleaved values (bracket+space) |

### CSI Data Encoding

The 26th field contains interleaved I/Q samples:

- Format: `[I0 Q0 I1 Q1 ... In Qn]`
- Delimiter: space-separated inside brackets
- Type: `int8` values (-128 to 127)
- Empty: `[]` (no CSI data)

### Role Identification

| Role | CSV Value | Firmware | UART Active |
|------|-----------|----------|-------------|
| Access Point | `AP` | active_ap | Yes |
| Station | `STA` | active_sta | No (UART not used) |
| Passive | `PASSIVE` | passive | Yes |

## Control Commands

| Command | Format | Description |
|---------|--------|-------------|
| SETTIME | `SETTIME:<unix_seconds>\n` | Sync ESP32 clock |
| RESET | `RESET\n` | Software reset ESP32 |

The ESP32 does NOT send ACK/NACK responses. Commands are fire-and-forget.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Malformed line | Discard, log warning, continue streaming |
| Empty line | Skip silently |
| Buffer saturation | Data loss (no flow control) |
| UART disconnection | 5s timeout, then reconnect every 2s |
| Dead port | Reader reports error, keeps retrying |

## Source Reference

The firmware format is defined in `_components/csi_component.h:27-79` of the ESP32-CSI-Tool repository.
