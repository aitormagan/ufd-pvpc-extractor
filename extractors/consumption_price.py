from extractors import ufd, pvpc
from db import Measurement
from datetime import datetime, date, timedelta


def update_consumption_price(influx_client):
    ufd_token = ufd.login()
    cupses = ufd.get_cupses(ufd_token)
    day = influx_client.get_measurement_last_day(Measurement.FINAL_COST) + timedelta(1)
    today = datetime.combine(date.today(), datetime.min.time())

    while day < today:
        update_final_cost_day(influx_client, ufd_token, cupses, day)
        day = day + timedelta(1)


def update_final_cost_day(influx_client, ufd_token, cupses, day):
    pvpc_price = pvpc.get_day_pvpc(day)
    naturgy_price = get_naturgy_price(day)
    repsol_price = get_repsol_price(day)

    for cups in cupses:
        consumption_map = ufd.get_day_consumption(ufd_token, cups, day)

        price_pvpc = {x: consumption_map[x] * pvpc_price[x] for x in consumption_map}
        price_naturgy = {x: consumption_map[x] * naturgy_price[x] for x in consumption_map}
        price_repsol = {x: consumption_map[x] * repsol_price[x] for x in consumption_map}

        influx_client.insert_stats(Measurement.FINAL_COST, day, price_pvpc, {"cups": cups, "company": "pvpc"})
        influx_client.insert_stats(Measurement.FINAL_COST, day, price_naturgy, {"cups": cups, "company": "naturgy"})
        influx_client.insert_stats(Measurement.FINAL_COST, day, price_repsol, {"cups": cups, "company": "repsol"})

    day_str = day.strftime("%d/%m/%Y")
    print(f"Consumption for {day_str} processed...")


def get_repsol_price(day):
    return {x: 0.1099 for x in range(0, 24)}


def get_naturgy_price(day):
    if day.weekday() in [5, 6]:
        return {x: 0.077252 for x in range(0, 24)}
    else:
        # Valle
        prices = {x: 0.077252 for x in range(0, 8)}
        # Llano
        prices.update({x: 0.112342 for x in range(8, 10)})
        prices.update({x: 0.112342 for x in range(14, 18)})
        prices.update({x: 0.112342 for x in range(22, 24)})
        # Pico
        prices.update({x: 0.205661 for x in range(10, 14)})
        prices.update({x: 0.205661 for x in range(18, 22)})

        return prices
