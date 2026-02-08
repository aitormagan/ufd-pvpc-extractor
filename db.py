import os
import pytz
from enum import Enum
from influxdb import InfluxDBClient
from datetime import datetime


MADRID_TZ = pytz.timezone("Europe/Madrid")


class Measurement(Enum):
    CONSUMPTION = "consumption"
    PVPC = "pvpc"
    FINAL_COST = "final_cost"
    SELF_CONSUMPTION_GENERATED = "self_consumption_generated"
    SELF_CONSUMPTION_SURPLUS = "self_consumption_surplus"
    SELF_CONSUMPTION_USED = "self_consumption_used"


class Influx:

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            host = os.environ.get("INFLUX_HOST", "localhost")
            self._client = InfluxDBClient(host, 8086, None, None, "electricity")

        return self._client

    def insert_stats(self, measurement, date, data, tags=None):
        influx_data = []
        for hour in data:
            complete_date = date.replace(hour=hour)
            complete_date = MADRID_TZ.localize(complete_date)
            influx_data.append({
                "measurement": measurement.value,
                "time": complete_date,
                "fields": {
                    "value": data[hour]
                }
            })

            if tags:
                influx_data[-1]["tags"] = tags

        self.client.write_points(influx_data)

    def get_measurement_last_day(self, measurement: Measurement):
        try:
            query = f"SELECT last(value), time from {measurement.value};"
            result = self.client.query(query)

            return datetime.strptime(list(result.items()[0][1])[0]["time"].split("T")[0], "%Y-%m-%d")
        except IndexError:
            return datetime(2021, 5, 31)
