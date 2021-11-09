from datetime import datetime, timedelta, date
import os
import argparse
import requests
from db import Influx, Measurement


DNI = os.environ.get("UFD_USER")
PASS = os.environ.get("UFD_PASS")
influx_client = Influx()
REE_TOKEN = os.environ.get("REE_TOKEN")


UFD_HEADERS = {"X-Appversion": "1.0.0.0", "X-Application": "ACUFD", "X-AppClientSecret": "4CUFDW3b",
               "X-Appclientid": "ACUFDWeb", "X-AppClient": "ACUFDW"}


def get_udf_headers(token):
    headers = {"Authorization": f"Bearer {token}"}
    headers.update(UFD_HEADERS)
    return headers


def login(user, password):
    res = requests.post("https://api.ufd.es/ufd/v1.0/login", json={"user": user, "password": password},
                        headers=UFD_HEADERS)
    return res.json()["accessToken"]


def get_cups(user, token):
    headers = get_udf_headers(token)
    res = requests.get(f"https://api.ufd.es/ufd/v1.0/supplypoints?filter=documentNumber::{user}", headers=headers)
    return [x["cups"] for x in res.json()["supplyPoints"]["items"]]


def get_day_consumption(token, cups, day):
    headers = get_udf_headers(token)
    day_str = day.strftime("%d/%m/%Y")
    res = requests.get(f"https://api.ufd.es/ufd/v1.0/consumptions?filter=nif::{DNI}%7Ccups::{cups}%7CstartDate::{day_str}%7CendDate::{day_str}%7Cgranularity::H%7Cunit::K%7Cgenerator::0%7CisDelegate::N%7CisSelfConsumption::0%7CmeasurementSystem::O",
                       headers=headers)
    consumptions = res.json()["items"][0]["consumptions"]["items"]

    return {x["hour"] - 1: float(x["consumptionValue"].replace(",", ".")) for x in consumptions}


def get_day_pvpc(day):
    day_str = day.strftime("%Y-%m-%d")
    url = f"https://api.esios.ree.es/indicators/1001?start_date={day_str}T00:00:00.000&end_date={day_str}T23:59:59.000&geo_ids%5B%5D=8741"
    data = requests.get(url, headers={"Authorization": f"Token token=\"{REE_TOKEN}\""}).json()
    return {datetime.fromisoformat(x["datetime"]).hour: x["value"] / 1000 for x in data["indicator"]["values"]}


def update_pvpc():
    day = influx_client.get_measurement_last_day(Measurement.PVPC) + timedelta(1)
    tomorrow = datetime.combine(date.today() + timedelta(1), datetime.min.time())

    while day <= tomorrow:
        update_pvpc_day(day)
        day = day + timedelta(1)


def update_pvpc_day(day):
    pvpc_price = get_day_pvpc(day)
    influx_client.insert_stats(Measurement.PVPC, day, pvpc_price)

    day_str = day.strftime("%d/%m/%Y")
    print(f"PVPC for {day_str} processed...")


def update_consumption():
    ufd_token = login(DNI, PASS)
    cupses = get_cups(DNI, ufd_token)
    day = influx_client.get_measurement_last_day(Measurement.CONSUMPTION) + timedelta(1)
    today = datetime.combine(date.today(), datetime.min.time())

    while day < today:
        update_consumption_day(ufd_token, cupses, day)
        day = day + timedelta(1)


def update_consumption_day(ufd_token, cupses, day):
    for cups in cupses:
        consumption_map = get_day_consumption(ufd_token, cups, day)
        influx_client.insert_stats(Measurement.CONSUMPTION, day, consumption_map, {"cups": cups})

    day_str = day.strftime("%d/%m/%Y")
    print(f"Consumption for {day_str} processed...")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pvpc', help='Update PVPC since last update (or 2021-06-01) until tomorrow', action="store_true")
    parser.add_argument('--consumption', help='Update consumption since last update (or 2021-06-01) until yesterday', action="store_true")

    args = parser.parse_args()

    if args.pvpc:
        update_pvpc()

    if args.consumption:
        update_consumption()


if __name__ == '__main__':
    main()
