import sched
import sys
import time
from argparse import ArgumentParser
from typing import List

import requests
from multiversx_sdk_core import Address

from API import execute_order, get_orders, open_order
from utils import *


def parse_arguments(cli_args: List[str]):
    parser = ArgumentParser()
    parser.add_argument("--address", required=True, type=str, help="Your wallet address")
    parser.add_argument("--pem", required=True, type=str, help="Path to your pem file")
    args = parser.parse_args(cli_args)

    return args


def decode_order(value) -> Order:
    # Extracting the hex value of the owner address
    hex_address = value[:32].hex()

    # Converting the hex value to bech32
    owner_address = Address.from_hex(hex_address, "erd").bech32()

    # Extracting the token identifier length and token identifier
    token_in_length = int.from_bytes(value[32:36], byteorder='big')
    token_in = value[36:36 + token_in_length].decode()

    # Extracting the amount in
    amount_in_length = int.from_bytes(value[36 + token_in_length:40 + token_in_length], byteorder='big')
    amount_in = int.from_bytes(value[40 + token_in_length:40 + token_in_length + amount_in_length], byteorder='big')

    # Extracting the token out identifier length and token out identifier
    token_out_length = int.from_bytes(
        value[40 + token_in_length + amount_in_length:
              44 + token_in_length + amount_in_length],
        byteorder='big'
    )
    token_out = value[
                44 + token_in_length + amount_in_length:
                44 + token_in_length + amount_in_length + token_out_length].decode()

    # Extracting the limit
    limit_length = int.from_bytes(
        value[44 + token_in_length + amount_in_length + token_out_length:
              48 + token_in_length + amount_in_length + token_out_length],
        byteorder='big'
    )
    limit = int.from_bytes(
        value[48 + token_in_length + amount_in_length + token_out_length:
              48 + token_in_length + amount_in_length + token_out_length + limit_length],
        byteorder='big'
    )

    # Extracting the minimum amount
    minimum_amount_length = int.from_bytes(
        value[48 + token_in_length + amount_in_length + token_out_length + limit_length:
              52 + token_in_length + amount_in_length + token_out_length + limit_length],
        byteorder='big'
    )
    minimum_amount = int.from_bytes(
        value[52 + token_in_length + amount_in_length + token_out_length + limit_length:
              52 + token_in_length + amount_in_length + token_out_length + limit_length + minimum_amount_length],
        byteorder='big'
    )

    return Order(owner_address, token_in, amount_in, token_out, limit * (10 ** -18), minimum_amount)


def request_price():
    url = "https://devnet-api.multiversx.com/mex/tokens"
    response = requests.request("GET", url)

    egld_map = response.json()[1]

    return round(egld_map["price"], 3)


def check_price(orders: list[Order], nonce: int, sc):
    current_price = request_price()

    if len(orders) == 0:
        print('No orders to execute')
        return

    for index, order in enumerate(orders[:]):
        if current_price >= order.limit:
            execute_order(index + 1, nonce)
            swap_remove(orders, index)
            nonce += 1
            print(f'Order {index + 1} executed')

    print(f'Number of orders left: {len(orders)}')
    print(f'Current Price of WEGLD is {current_price}')

    sc.enter(6, 1, check_price, (orders, nonce, sc,))


def main(cli_args: List[str]):
    # args = parse_arguments(cli_args)
    orders = list(map(decode_order, get_orders()))
    print(len(orders))

    s = sched.scheduler(time.time, time.sleep)
    s.enter(0, 1, check_price, (orders, 355, s,))
    s.run()


if __name__ == '__main__':
    main(sys.argv[1:])


    #open_order()
