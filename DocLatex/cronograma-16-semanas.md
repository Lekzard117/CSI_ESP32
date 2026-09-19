# Cronograma Conceptual — 16 Semanas

## Convenciones
- **S**: Semana
- **OE1**: Objetivo Específico 1 (Captura + Transmisión)
- **OE2**: Objetivo Específico 2 (Procesamiento + Detección)
- **Hito (◆)**: Entregable verificable

---

## Fase 0: Fundamentación (S1–S2)

| Semana | Actividades | Producto |
|--------|-------------|----------|
| S1 | Revisión literatura: CSI, ESP32, OFDM, filtrado Hampel/Butterworth, AGC | Marco teórico preliminar |
| S2 | Instalación toolchain (ESP-IDF v6.0.1), familiarización con ESP32-CSI-Tool | Entorno de desarrollo funcional |
| ◆ S2 | **Hito**: Toolchain verificado — `idf.py build` exitoso en active_ap y passive | — |

---

## Fase 1: Captura y Transmisión CSI — OE1 (S3–S8)

| Semana | Actividades | Producto |
|--------|-------------|----------|
| S3 | Flasheo y prueba de los 3 roles (active_sta, active_ap, passive) en HW | Firmware corriendo en ESP32-1 y ESP32-2 |
| S4 | Verificación salida serial: `idf.py monitor \| grep CSI_DATA`, ajuste 921600 baud | Streaming CSV a 921600 baud |
| S5 | **Implementación puente Python (completado)**: `flask_serial` (models, parser, reader, commands) + tests | `src/flask_serial/` — 26 tests pasando |
| S6 | Validación extremo a extremo: ESP32 → UART → SerialReader → CsiLine en PC | Pipeline E2E funcional |
| S7 | Experimentos con configuración AP+smartphone: captura en entorno controlado | Dataset CSI crudo (CSV) |
| S8 | Análisis de tasa de captura, pérdida de paquetes, integridad de formato | Reporte de métricas de captura |
| ◆ S8 | **Hito OE1**: Pipeline de captura funcional — ESP32 envía, Flask/Python recibe y parsea | — |

---

## Fase 2: Pipeline de Procesamiento CSI — OE2 (S9–S14)

| Semana | Actividades | Producto |
|--------|-------------|----------|
| S9 | Implementar compensación AGC: detección de saltos de ganancia + interpolación lineal | Módulo `agc.py` |
| S10 | Implementar filtro Hampel (ventana deslizante, umbral configurable) para outliers | Módulo `filters.py` — Hampel |
| S11 | Implementar filtro Butterworth LPF 10Hz + Savitzky-Golay para suavizado | Módulo `filters.py` — Butterworth + SG |
| S12 | Implementar sustracción de fondo (promedio móvil) + varianza móvil por subportadora | Módulo `background.py` |
| S13 | Validación con datos etiquetados: vacío vs caminar vs gesto. Métricas SSNR/subportadora | Métricas de SNR por subportadora |
| S14 | Integración en servidor Flask: API REST /upload, /stream, configuración de pipeline | `app.py` con endpoint de streaming |
| ◆ S14 | **Hito OE2**: Pipeline de procesamiento completo en Flask — CSI crudo → alerta de movimiento | — |

---

## Fase 3: Validación Experimental (S15–S16)

| Semana | Actividades | Producto |
|--------|-------------|----------|
| S15 | Diseño experimental: escenarios controlados (vacío, 1 persona, 2 personas, NLOS) | Protocolo de pruebas |
| S15 | Recolección de datos etiquetados + ejecución pipeline | Resultados de detección |
| S16 | Análisis: matriz de confusión, tasa aciertos, falsos positivos, latencia | Reporte de rendimiento |
| S16 | Compilación de reporte final + diagramas (PIM, PSM, clases, conceptuales) | Reporte LaTeX + figuras |
| ◆ S16 | **Hito Final**: Reporte completo con resultados experimentales | — |

---

## Diagrama de Gantt (textual)

```
Fase                S01 S02 S03 S04 S05 S06 S07 S08 S09 S10 S11 S12 S13 S14 S15 S16
FUNDAMENTACIÓN      ███ ███
CAPTURA (OE1)              ███ ███ ███ ███ ███ ███
PROCESAMIENTO (OE2)                                    ███ ███ ███ ███ ███ ███
VALIDACIÓN                                                             ███ ███
DOCUMENTACIÓN                                                        ██      ███

Hitos:              ◆2      ◆8                              ◆14             ◆16
```

## Dependencias críticas

| Dependencia | Origen → Destino | Riesgo |
|-------------|------------------|--------|
| Toolchain IDF v6.0.1 | S2 → S3 | Bajo |
| Firmware flasheado | S3 → S4 | Bajo |
| `flask_serial` listo | S5 → S6 | **Completado ✓** |
| Pipeline E2E funcional | S6 → S7..S8 | Medio (pérdida de paquetes) |
| Módulos de filtrado | S9..S12 → S13 | Alto (sintonía de parámetros) |
| Pipeline completo | S14 → S15 | Medio |
| Experimentos | S15 → S16 | Bajo |
