# Decision Moment `01KY3F6JD1TMR2B80QTEJMRAWG`

- **Mission:** `cambio-requisitos-csi-01KY3E10`
- **Origin flow:** `plan`
- **Slot key:** `plan.performance.tasa-baudios`
- **Input key:** `tasa_baudios`
- **Status:** `resolved`
- **Created:** `2026-07-21T23:11:58.881164+00:00`
- **Resolved:** `2026-07-21T23:14:34.556540+00:00`
- **Opened by:** `cli`
- **Other answer:** `false`

## Question

Sobre la tasa de baudios: actualmente usas 921600. Quieres: (a) probar bajar a 115200 y medir si el throughput alcanza, (b) hacerla configurable via menuconfig/parametro, o (c) evaluar experimentalmente las 3 tasas comunes (115200, 460800, 921600) y documentar resultados?

## Options

- (c) Evaluar las 3 tasas experimentalmente y documentar
- (b) Hacerla configurable, que el usuario elija
- (a) Probar 115200 y ver si funciona
- Aun no lo se

## Final answer

Mantener 921600 pero configurable. Evaluar impacto en serial y procesamiento

## Rationale

_(none)_

## Change log

- `2026-07-21T23:11:58.881164+00:00` — opened
- `2026-07-21T23:14:34.556540+00:00` — resolved (final_answer="Mantener 921600 pero configurable. Evaluar impacto en serial y procesamiento")
