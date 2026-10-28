# Flask Serial Architecture Diagram

## Current State Flow

```
┌─────────────────┐    UART    ┌──────────────────┐
│  ESP32 Device   │ ──────────> │  Flask Server    │
│  (active_ap)    │             │  (flask_serial)  │
└─────────────────┘             └──────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────┐    Serial      ┌──────────────────┐
│  Serial Port    │ ──────────────> │  reader.py       │
│  /dev/ttyUSB0   │                 │  (SerialReader)  │
└─────────────────┘                 └──────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────┐    Parse CSI     ┌──────────────────┐
│  Line Buffer    │ ──────────────> │  parser.py       │
│  (split by \n)  │                 │  (CsiLine parser)│
└─────────────────┘                 └──────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────┐    Validate &     ┌──────────────────┐
│  CsiLine Object │ ──────────────> │  models.py       │
│  (parsed)       │                 │  (CsiLine dataclass)│
└─────────────────┘                 └──────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────┐    Filter &      ┌──────────────────┐
│  CsiLine Object │ ──────────────> │  stats.py        │
│  (validated)    │                 │  (Statistics)    │
└─────────────────┘                 └──────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────┐    Process       ┌──────────────────┐
│  CsiLine Object │ ──────────────> │  pipeline.py     │
│  (filtered)     │                 │  (Processing)    │
└─────────────────┘                 └──────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────┐    Serve       ┌──────────────────┐
│  Processed      │ ──────────────> │  Flask API       │
│  Data           │                 │  (REST endpoints)│
└─────────────────┘                 └──────────────────┘
```

## Module Interactions

### reader.py (SerialReader)
- Connects to UART port (/dev/ttyUSB0)
- Reads data in chunks (4096 bytes)
- Splits lines by '\n' delimiter
- Handles connection timeouts and reconnection
- Returns CsiLine objects through generator interface

### parser.py 
- Parses raw serial lines into CsiLine objects
- Validates CSV format with 26+ fields
- Converts data types appropriately
- Handles malformed lines gracefully

### models.py
- Defines CsiLine dataclass for CSI data structure
- Defines Role enum (AP, STA, Passive)
- Contains validation logic for parsed data

### stats.py
- Tracks frame statistics (frames_validos, frames_mac_nula)
- Detects stream interruptions
- Provides reporting functionality
- Integrates with reader for real-time updates

### pipeline.py
- Implements CSI processing pipeline
- Applies AGC, Hampel, Butterworth, SG filters
- Performs background subtraction
- Implements movement detection algorithms

## Key Features

1. **MAC Filtering**: Null MAC frames (00:00:00:00:00:00) are filtered out before processing
2. **Statistics Tracking**: Real-time counters for valid and null frames
3. **Stream Interruption Detection**: Detects when stream stops and resumes
4. **Multi-port Support**: Can read from multiple serial ports (SERIAL_PORTS env var)
5. **Error Handling**: Graceful handling of connection issues, timeouts, and malformed data

## Data Flow Example

1. ESP32 sends CSI_DATA line over UART
2. reader.py reads line and splits by '\n'
3. parser.py converts to CsiLine object
4. stats.py checks MAC address and updates counters
5. If MAC is null, frame is filtered out
6. Valid frames pass to pipeline.py for processing
7. Processed data served via Flask API endpoints