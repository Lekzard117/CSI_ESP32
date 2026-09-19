# Decisión: mantener formato de 26 campos y adoptar parser Cython

**Fecha**: 2026-08-06
**Estado**: Resuelta
**Contexto**: Tras evaluar TinyCSI, CSIKit y csiread, se probó `csiread` 1.4.1 contra `ESP32-CSI-Tool/python_utils/example_csi.csv` (captura real):
- Parsea los 13 paquetes del archivo de ejemplo correctamente (CSI shape, MAC, RSSI, noise_floor) y de forma instantánea (Cython).
- Falla con `IndexError` sobre una línea reducida a 7 campos (formato planeado por esta misión).

**Decisión**: Mantener el formato CSI estándar de 26 campos del ESP32-CSI-Tool y usar `csiread` (o CSIKit) como parser Cython en el pipeline Python. Esto descarta la reducción a 7 campos planeada en la misión `cambio-requisitos-csi-01KY3E10`.

**Impacto en la misión**:
- FR-001 (subset mínimo), FR-002 (eliminar role), FR-004 (firmware reducido), FR-005 (parser reducido) quedan **obsoletos**.
- FR-003 (tasa de baudios) y FR-006 (retrocompatibilidad) quedan sin objeto directo.
- La misión estaba `not_started` (plan completado, sin trabajo ejecutado).

**Alternativa descartada**: parser propio en Flask para formato de 7 campos — pierde la velocidad de Cython y obliga a mantener un fork del firmware divergente del upstream.
