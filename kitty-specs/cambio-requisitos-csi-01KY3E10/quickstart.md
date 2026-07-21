# Quickstart: Cambio de formato CSI

## Prerequisitos

- ESP-IDF v6.0.1 activado
- Python 3.13+ con pyserial

## Flashear firmware con nuevo formato

```bash
source ~/.espressif/tools/activate_idf_v6.0.1.sh
cd ESP32-CSI-Tool/active_ap
idf.py fullclean && idf.py build && idf.py -p /dev/ttyUSB0 flash
```

## Capturar datos con nuevo formato

```bash
idf.py monitor | grep "CSI_DATA" > experimento.csv
```

## Migrar datasets existentes

```bash
python src/flask_serial/migrate_csv.py --input experimento_antiguo.csv --output experimento_nuevo.csv
```

## Ver formato esperado

```text
CSI_DATA,aa:bb:cc:dd:ee:ff,-65,6,12345678,0,52,[+1, +2, -3, +4]
```
