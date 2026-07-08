# Quickstart — Interfaz de Comunicación ESP32 → Flask

## Dependencias

```bash
pip install pyserial
```

## Uso básico

```python
from flask_serial.reader import SerialReader

# Conectar a un puerto
reader = SerialReader('/dev/ttyUSB0', baud=921600)
reader.connect()

# Leer líneas CSI
for line in reader.lines():
    print(f"Rol: {line.role}, MAC: {line.mac}, RSSI: {line.rssi}")
    print(f"  Subportadoras: {len(line.csi_data)} valores I/Q")
```

## Múltiples puertos

```python
# Configurar desde variable de entorno
# SERIAL_PORTS=/dev/ttyUSB0,/dev/ttyUSB1

import os
ports = os.getenv('SERIAL_PORTS', '/dev/ttyUSB0').split(',')

readers = [SerialReader(p) for p in ports]
for reader in readers:
    reader.connect()
```

## Comandos de control

```python
from flask_serial.commands import send_settime, send_reset

send_settime(reader, 1712345678)  # Sincronizar reloj
send_reset(reader)                # Reiniciar ESP32
```
