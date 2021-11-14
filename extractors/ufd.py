from datetime import datetime, timedelta, date
import os
import requests
from db import Measurement


DNI = os.environ.get("UFD_USER")
PASS = os.environ.get("UFD_PASS")


UFD_HEADERS = {"X-Appversion": "1.0.0.0", "X-Application": "ACUFD", "X-AppClientSecret": "4CUFDW3b",
               "X-Appclientid": "ACUFDWeb", "X-AppClient": "ACUFDW"}


def update_consumption(influx_client):
    ufd_token = login()
    cupses = get_cupses(ufd_token)
    day = influx_client.get_measurement_last_day(Measurement.CONSUMPTION) + timedelta(1)
    today = datetime.combine(date.today(), datetime.min.time())

    while day < today:
        update_consumption_day(influx_client, ufd_token, cupses, day)
        day = day + timedelta(1)


def update_consumption_day(influx_client, ufd_token, cupses, day):
    for cups in cupses:
        consumption_map = get_day_consumption(ufd_token, cups, day)
        influx_client.insert_stats(Measurement.CONSUMPTION, day, consumption_map, {"cups": cups})

    day_str = day.strftime("%d/%m/%Y")
    print(f"Consumption for {day_str} processed...")


def login():
    res = requests.post("https://api.ufd.es/ufd/v1.0/login", json={"user": DNI, "password": PASS},
                        headers=UFD_HEADERS)
    return res.json()["accessToken"]


def get_cupses(token):
    headers = get_ufd_headers(token)
    res = requests.get(f"https://api.ufd.es/ufd/v1.0/supplypoints?filter=documentNumber::{DNI}", headers=headers)
    return [x["cups"] for x in res.json()["supplyPoints"]["items"]]


def get_day_consumption(token, cups, day):
    headers = get_ufd_headers(token)
    day_str = day.strftime("%d/%m/%Y")
    res = requests.get(f"https://api.ufd.es/ufd/v1.0/consumptions?filter=nif::{DNI}%7Ccups::{cups}%7CstartDate::{day_str}%7CendDate::{day_str}%7Cgranularity::H%7Cunit::K%7Cgenerator::0%7CisDelegate::N%7CisSelfConsumption::0%7CmeasurementSystem::O",
                       headers=headers)
    consumptions = res.json()["items"][0]["consumptions"]["items"]

    return {x["hour"] - 1: float(x["consumptionValue"].replace(",", ".")) for x in consumptions}


def get_ufd_headers(token):
    headers = {"Authorization": f"Bearer {token}"}
    headers.update(UFD_HEADERS)
    return headers
