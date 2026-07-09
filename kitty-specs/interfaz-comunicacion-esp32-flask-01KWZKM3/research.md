# Research — Interfaz de Comunicación ESP32 → Flask

## Decisiones

### Puerto serial configurable
- **Decisión**: Múltiples puertos configurables por variable de entorno `SERIAL_PORTS`
- **Formato**: `SERIAL_PORTS=/dev/ttyUSB0,/dev/ttyUSB1` (lista separada por coma)
- **Alternativa considerada**: Puerto fijo `/dev/ttyUSB0` — descartada porque el usuario requiere soporte multi-puerto
- **Implementación**: El lector serial itera sobre la lista e intenta conectar secuencialmente; reporta los puertos exitosos

### Timing de reconexión
- **Decisión**: Timeout de 5 segundos sin datos → intentar reconectar cada 2 segundos
- **Razón**: La desconexión UART no tiene señalización; el timeout es la única detección posible

### Delimitador de línea
- **Decisión**: `\n` (0x0A) estricto; sin soporte para `\r\n`
- **Razón**: El firmware ESP32-CSI-Tool usa `\n` como terminador único (confirmado en código fuente)
