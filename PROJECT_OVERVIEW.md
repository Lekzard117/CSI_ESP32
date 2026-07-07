
# Tema de Poryecto: Recolección y Procesamiento de Señales WiFi mediante CSI para Detección de Movimiento.
# Línea y sublínea de investigación: Tecnologías de la Computación para la Innovación Tecnológica, Desarrollo Sostenible y la Transformación Digital Sublinea 3.1 Internet de las Cosas (IoT) y Sistemas Ciber-físicos

## Pregunta de investigación:  ¿Cual es el indice de mitigación del ruido tecnico de los dispositivos ESP32 que se logra con el procesamiento de la Información del Estado del Canal (CSI) en un servidor de borde (Flask) comparado con el uso de señales crudas empleadas para la deteccion de movimiento en espacios cerrados?

## Objetivo General:
    Diseñar una arquitectura de tres capas (emisor ESP32, receptor ESP32 y servidor Flask) para la recolección y procesamiento de Channel State Information (CSI) que integre un proceso de sanitización y filtrado digital en un servidor Flask para la detección de movimiento en espacios cerrados.
## Objetivos Especificos:
    * Implementar un nodo receptor ESP32 que sea identificable por dirección MAC que capture CSI de paquetes provenientes de al menos un nodo emisor ESP32, transmitiendo los datos al servidor Flask a través del puerto serial a una tasa mayor o igual de 921600 baudios sin importar el indice de perdida de paquetes.
    * Componer una línea de procesamiento en el servidor Flask que mitigue las no linealidades del hardware ESP32 mediante compensación dinámica de ganancia (AGC) y sanitización de fase, realice un filtrado digital multietapa (Hampel, Butterworth) para la depuración de ruido técnico y ambiental, y aplique la sustracción de fondo para identificar perturbaciones asociadas al movimiento


## Actividades por objetivo #1
    **Configuracion de Firmware:** Flashear los dispositivos con el ESP32-CSI-Tool, configurando el nodo emisor en modo activo y el receptor en modo pasivo monitor, asegurando la asignación de roles mediante la dirección MAC.
    **Ajuste de la interfaz serial:** Configurar los parámetros del componente monitor y el puerto UART de consola del ESP32 a una tasa de 921600 baudios para evitar latencia en el flujo masivo de datos.
    **Desarrollo del puente de datos:** Programar un script en Python que lea el puerto serial, extraiga los campos de amplitud y fase de las subportadoras (típicamente 52 o 114) y los envíe de forma asíncrona al servidor Flask para su lectura y almacenamiento en formato CSV o MAT

## Actividades por objetivo #2
    **Mitigación de hardware:** Programar el algoritmo en Flask para la compensación de los saltos de amplitud inducidos por el AGC y de la corrección lineal de la fase mediante regresión por subportadora.
    **Filtrado multietapa:** Integrar una secuencia de limpieza que incluya el filtro Hampel para valores atípicos, Butterworth para ruido ambiental y Savitzky-Golay para suavizado de trayectorias.
    **Selección de datos:** Crear un script de identificación y procesamiento de las subportadoras con mayor SSNR y aplique la sustracción de la línea base estática para resaltar el componente dinámico del movimiento encontrado.

