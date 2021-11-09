# UFD & PVPC Extractor

Este script de Python tiene dos utilidades:

1. Extraer la información de consumo real de energía de todos los suministros para clientes de Unión Fenosa
Distribución
2. Extraer la información del precio del PVPC

Esta información es almacenada en dos tablas de InfluxDB con idea de que puedan ser consumidas fácilmente desde 
herramientas de visualización como grafana.

## Uso:

```
usage: main.py [-h] [--pvpc] [--consumption]

optional arguments:
  -h, --help     show this help message and exit
  --pvpc         Update PVPC since last update (or 2021-06-01) until tomorrow
  --consumption  Update consumption since last update (or 2021-06-01) until yesterday
```

### Variables de entorno requeridas:

* `UDF_USER` (`--consumption`): El usuario para logarse en la web de Unión Fenosa Distribución.
* `UDF_PASS` (`--consumption`): La password de acceso para la web de Unión Fenosa Distribución asociada al usuario 
  especificado en la variable `UFD_USER`.
* `REE_TOKEN` (`--pvpc`): El token para acceder a la API de Red Eléctrica Española. Puede obtenerse mandando un email a:
  [consultasios@ree.es](consultasios@ree.es]). +info: https://api.esios.ree.es.