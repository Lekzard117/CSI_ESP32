# Quickstart — Interfaz de Comunicación ESP32 → Flask

## Dependencies

```bash
pip install pyserial
```

## Uso básico

```python
from flask_serial.reader import SerialReader
from flask_serial.commands import send_settime

# Configurar el puerto
reader = SerialReader('/dev/ttyUSB0', baud=921600)
reader.connect()
print(f"Conectado: {reader.is_connected}")  # → True

# Enviar comando de sincronización
import time
send_settime(reader, int(time.time()))

# Leer líneas CSI
for line in reader.lines():
    print(f"Rol: {line.role}, MAC: {line.mac}, RSSI: {line.rssi}")
    print(f"  Subportadoras: {len(line.csi_data)} valores I/Q")
    if line.csi_data:
        amplitudes = [abs(v) for v in line.csi_data]
        print(f"  Amplitud media: {sum(amplitudes) / len(amplitudes):.1f}")
```

## Múltiples puertos

```python
from flask_serial.reader import create_readers

# export SERIAL_PORTS=/dev/ttyUSB0,/dev/ttyUSB1
for reader in create_readers():
    if reader.connect():
        print(f"OK: {reader.port}")
    else:
        print(f"FAIL: {reader.port}")
```

## Comandos de control

```python
from flask_serial.commands import send_settime, send_reset

send_settime(reader, 1712345678)  # Sincronizar reloj
send_reset(reader)                # Reiniciar ESP32
```
