# UFD & PVPC Extractor

Este script de Python tiene cuatro utilidades:

1. Extraer la información de consumo real de energía de todos los suministros para clientes de Unión Fenosa Distribución
2. Extraer la información del precio del PVPC
3. Calcular los precios en base al consumo el precio del PVPC y cualquier tarifa que quieras configurar
1. Extraer la información de autoconsumo de todos los suministros para clientes de Unión Fenosa Distribución

Esta información es almacenada en tablas de InfluxDB con idea de que puedan ser consumidas fácilmente desde herramientas de visualización como Grafana.

## Uso:

```
usage: main.py [-h] [--pvpc] [--consumption] [--consumption_price] [--self_consumption]

options:
  -h, --help           show this help message and exit
  --pvpc               Update PVPC since last update (or 2021-06-01) until tomorrow
  --consumption        Update consumption since last update (or 2021-06-01) until yesterday
  --consumption_price  Update consumption price since last update (or 2021-06-01) until yesterday
  --self_consumption   Update self-consumption data (generated, surplus, used) since last update
                       until yesterday
```

### Variables de entorno requeridas:

* `UDF_USER` (`--consumption`, `--consumption_price` y `--self_consumption`): El usuario para logarse en la web de Unión Fenosa Distribución.
* `UDF_PASS` (`--consumption`, `--consumption_price` y `--self_consumption`): La password de acceso para la web de Unión Fenosa Distribución asociada al usuario 
  especificado en la variable `UFD_USER`.
* `REE_TOKEN` (`--pvpc` y `--consumption_price`): El token para acceder a la API de Red Eléctrica Española. Puede obtenerse mandando un email a:
  [consultasios@ree.es](consultasios@ree.es]). +info: https://api.esios.ree.es.