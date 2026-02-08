import argparse
from db import Influx
from extractors import ufd, pvpc, consumption_price


influx_client = Influx()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pvpc', help='Update PVPC since last update (or 2021-06-01) until tomorrow', action="store_true")
    parser.add_argument('--consumption', help='Update consumption since last update (or 2021-06-01) until yesterday', action="store_true")
    parser.add_argument('--consumption_price', help='Update consumption price since last update (or 2021-06-01) until yesterday', action="store_true")
    parser.add_argument('--self_consumption', help='Update self-consumption data (generated, surplus, used) since last update until yesterday', action="store_true")

    args = parser.parse_args()

    if args.pvpc:
        pvpc.update_pvpc(influx_client)

    if args.consumption:
        ufd.update_consumption(influx_client)

    if args.consumption_price:
        consumption_price.update_consumption_price(influx_client)

    if args.self_consumption:
        ufd.update_self_consumption(influx_client)


if __name__ == '__main__':
    main()
