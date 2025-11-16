from datetime import datetime, timedelta, date
import os
import requests
from db import Measurement


REE_TOKEN = os.environ.get("REE_TOKEN")


def update_pvpc(influx_client):
    day = influx_client.get_measurement_last_day(Measurement.PVPC) + timedelta(1)
    tomorrow = datetime.combine(date.today() + timedelta(1), datetime.min.time())

    while day <= tomorrow:
        update_pvpc_day(influx_client, day)
        day = day + timedelta(1)


def update_pvpc_day(influx_client, day):
    pvpc_price = get_day_pvpc(day)
    influx_client.insert_stats(Measurement.PVPC, day, pvpc_price)

    day_str = day.strftime("%d/%m/%Y")
    print(f"PVPC for {day_str} processed...")


def get_day_pvpc(day):
    day_str = day.strftime("%Y-%m-%d")
    url = f"https://api.esios.ree.es/indicators/1001?start_date={day_str}T00:00:00.000&end_date={day_str}T23:59:59.000&geo_ids%5B%5D=8741"
    data = requests.get(url, headers={"x-api-key": f"{REE_TOKEN}"}).json()
    return {datetime.fromisoformat(x["datetime"]).hour: x["value"] / 1000 for x in data["indicator"]["values"]}
