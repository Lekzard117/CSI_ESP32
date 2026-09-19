## Sistema de detección de movimiento mediante CSI con arquitectura de tres capas:
    1. Nodo emisor ESP32 (activo) que transmite paquetes WiFi
    2. Nodo receptor ESP32 (monitor) que captura CSI y envía por serial
    3. Servidor Flask que procesa las señales y detecta movimiento

## Requisitos funcionales:
    - El receptor debe ser identificable por MAC y capturar CSI de al menos un emisor
    - Pipeline de procesamiento: compensación AGC → sanitización de fase → filtrado Hampel → filtrado Butterworth → sustracción de fondo
    - Identificación de subportadoras con mayor SSNR
    - Almacenamiento de datos en CSV/MAT

## Requisitos no funcionales:
    - Procesamiento en tiempo real (baja latencia en servidor Flask)
    - Reproducibilidad de experimentos
    - Documentación del pipeline de procesamiento
    - Operación en espacios cerrados con múltiples trayectorias

## Entregables de documentación, Modelo de Requisitos (CIM) 
    + Modelado debe ser entregado en PlantUML
    - Modelos de contexto (diagramas C4 o similares)
    - Diagramas de casos de uso
    - Historias de usuario para cada componente
    - Diagramas de secuencia para el flujo de datos
