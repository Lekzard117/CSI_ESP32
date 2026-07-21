# Contrato: Formato Serial CSI Reducido

## Línea individual (CSV)

```
CSI_DATA,<mac>,<rssi>,<channel>,<local_timestamp>,<ant>,<len>,<csi_bracket>
```

### Ejemplo

```
CSI_DATA,aa:bb:cc:dd:ee:ff,-65,6,12345678,0,52,[+1, +2, -3, +4]
```

### Reglas de validación

1. Prefijo: `CSI_DATA`
2. 8 campos delimitados por comma (7 datos + 1 prefijo = 8 tokens)
3. `mac`: formato `/^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/`
4. `rssi`: entero negativo en dBm
5. `channel`: entero 1-14
6. `local_timestamp`: entero positivo (microsegundos)
7. `ant`: entero 0-1
8. `len`: entero positivo, debe coincidir con número de elementos en `csi_bracket`
9. `csi_bracket`: formato `[+/-]int(,[+/-]int)*` dentro de corchetes

## Tipos

| Campo | Tipo Python | Regex/Tipo C |
|-------|-------------|--------------|
| mac | str | `char[18]` |
| rssi | int | `int8_t` |
| channel | int | `uint8_t` |
| local_timestamp | int | `uint32_t` |
| ant | int | `uint8_t` |
| len | int | `uint16_t` |
| csi_data | list[int] | `int16_t[]` |
