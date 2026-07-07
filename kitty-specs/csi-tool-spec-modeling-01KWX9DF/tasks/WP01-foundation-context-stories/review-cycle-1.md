# Review Feedback — WP01 (Cycle 1)

## Anti-pattern checklist

| Item | Verdict | Notes |
|------|---------|-------|
| 1. Dead code | N/A | Documentación, sin código |
| 2. Synthetic-fixture test | N/A | Sin tests |
| 3. Silent empty return | N/A | Sin código |
| 4. FR coverage | PASS | FR-001, FR-002, FR-003, FR-007, FR-008 cubiertos |
| 5. Frozen surface | PASS | No se modificaron archivos congelados |
| 6. Locked decision | PASS | Sin contradicciones con spec/plan |
| 7. Shared-file ownership | PASS | models-v1/ compartido con WP02, sin conflictos |
| 8. Production fragility | N/A | Sin código |

## Issues

### Issue 1: Flask ausente en C4 diagram (T002)
El prompt requiere explícitamente que la capa Flask se muestre como sistema externo etiquetado "Futura" o "Fuera de alcance". El diagrama actual no menciona Flask en absoluto. También falta la nota `' Nota: La capa Flask será especificada en misión futura` en el código PlantUML.

**Fix**: Agregar elemento Flask como sistema externo con etiqueta "Futura — fuera del alcance actual" y añadir la nota en el código.

### Issue 2: User stories exceden alcance de WP01 (T004)
WP01 solicita 6 historias (2 por rol). Se entregaron 11, incluyendo:
- US-004, US-006, US-007, US-008: Pertenecen a WP02 (formato CSI, sincronización)
- US-010, US-011: Utilidades Python (no son firmware, fuera de alcance)

Las historias extra no son incorrectas, pero exceden el scope de WP01 y duplican cobertura que corresponde a WP02.

**Fix**: Mantener solo las 6 historias requeridas por WP01. Las adicionales pueden documentarse en WP02 o en misión de utilidades Python.

### Issue 3: Falta historia "configurar canal" para passive (T004)
El prompt pide explícitamente: "Como investigador, quiero configurar el canal WiFi a monitorear en el passive, para enfocar la captura en la banda de interés." No está presente en las historias entregadas.

**Fix**: Agregar la historia faltante para passive.

## Verdict

**Rechazado**. Corregir Issues 1-3 y re-enviar para revisión.
