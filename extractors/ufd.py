from datetime import datetime, timedelta, date
import os
import requests
from db import Measurement


DNI = os.environ.get("UFD_USER")
PASS = os.environ.get("UFD_PASS")


UFD_HEADERS = {
    "X-Application": "ACUFD",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "X-MessageId": "0/kUKK1Ul1xrbjdMs/1",
    "Access-Control-Allow-Origin": "*",
    "X-AppClient": "ACUFDMI",
    "Origin": "capacitor://localhost",
    "Sec-Fetch-Dest": "empty",
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept",
    "Sec-Fetch-Site": "cross-site",
    "X-AppClientSecret": "102sml3ajvkdjakoh2rhgrfpvjogl4b0or5nqmcmilvt2odpu9ce",
    "Connection": "keep-alive",
    "Accept-Language": "es-ES,es;q=0.9",
    "X-Appclientid": "1f3n1frmnqn14arndr3507lnok",
    "X-Appversion": "1.0.0.0",
    "Accept": "*/*",
    "Sec-Fetch-Mode": "cors",
}

DATE_FORMAT = "%d/%m/%Y"

# Generic

def login():
    res = requests.post("https://api.ufd.es/ufd/v1.0/login", 
                        json={"user": DNI, "password": PASS},
                        headers=UFD_HEADERS, timeout=30)
    return res.json()["accessToken"]


def get_ufd_headers(token):
    headers = {"Authorization": f"Bearer {token}"}
    headers.update(UFD_HEADERS)
    return headers


def get_cupses(token):
    headers = get_ufd_headers(token)
    res = requests.get(f"https://api.ufd.es/ufd/v1.0/supplypoints?filter=documentNumber::{DNI}",
                       headers=headers, timeout=30)
    return [x["cups"] for x in res.json()["supplyPoints"]["items"]]


# Standard Consumption

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

    day_str = day.strftime(DATE_FORMAT)
    print(f"Consumption for {day_str} processed...")


def get_day_consumption(token, cups, day):
    headers = get_ufd_headers(token)
    day_str = day.strftime(DATE_FORMAT)
    res = requests.get(f"https://api.ufd.es/ufd/v1.0/consumptions?filter=nif::{DNI}%7Ccups::{cups}%7CstartDate::{day_str}%7CendDate::{day_str}%7Cgranularity::H%7Cunit::K%7Cgenerator::0%7CisDelegate::N%7CisSelfConsumption::0%7CmeasurementSystem::O",
                       headers=headers, timeout=30)
    consumptions = res.json()["items"][0]["consumptions"]["items"]

    return {int(x["hour"]) - 1: float(x["consumptionValue"].replace(",", ".")) for x in consumptions}


# Self-consumption

def update_self_consumption(influx_client):
    ufd_token = login()
    cupses = get_cupses(ufd_token)
    # day = influx_client.get_measurement_last_day(Measurement.SELF_CONSUMPTION_GENERATED) + timedelta(1)
    day = datetime(2025, 12, 2)
    today = datetime.combine(date.today(), datetime.min.time())

    while day < today:
        update_self_consumption_day(influx_client, ufd_token, cupses, day)
        day = day + timedelta(1)


def update_self_consumption_day(influx_client, ufd_token, cupses, day):
    for cups in cupses:
        self_consumption_data = get_day_self_consumption(ufd_token, cups, day)
        influx_client.insert_stats(Measurement.SELF_CONSUMPTION_GENERATED, day, self_consumption_data["EHNGi"], {"cups": cups})
        influx_client.insert_stats(Measurement.SELF_CONSUMPTION_SURPLUS, day, self_consumption_data["EHEXi"], {"cups": cups})
        influx_client.insert_stats(Measurement.SELF_CONSUMPTION_USED, day, self_consumption_data["EHACi"], {"cups": cups})

    day_str = day.strftime(DATE_FORMAT)
    print(f"Self-consumption for {day_str} processed...")


def get_day_self_consumption(token, cups, day):
    headers = get_ufd_headers(token)
    day_str = day.strftime(DATE_FORMAT)
    res = requests.get(f"https://api.ufd.es/ufd/v1.0/consumptions?filter=nif::{DNI}%7Ccups::{cups}%7CstartDate::{day_str}%7CendDate::{day_str}%7Cgranularity::H%7Cunit::K%7Cgenerator::0%7CisDelegate::N%7CisSelfConsumption::1%7CmeasurementSystem::O",
                       headers=headers, timeout=30)
    self_consumptions = res.json()["selfConsumptions"]["items"]

    ehng_map = {}
    ehex_map = {}
    ehac_map = {}

    for item in self_consumptions:
        hour = int(item["hour"]) - 1
        ehng_map[hour] = float(item["EHNGi"].replace(",", ".")) if item["EHNGi"] else 0.0
        ehex_map[hour] = float(item["EHEXi"].replace(",", ".")) if item["EHEXi"] else 0.0
        ehac_map[hour] = float(item["EHACi"].replace(",", ".")) if item["EHACi"] else 0.0

    return {
        "EHNGi": ehng_map,
        "EHEXi": ehex_map,
        "EHACi": ehac_map
    }
