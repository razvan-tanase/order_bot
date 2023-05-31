from argparse import ArgumentParser
from typing import List

import requests
from multiversx_sdk_core import Address

from API import execute_order
from utils import *


def parse_arguments(cli_args: List[str]):
    parser = ArgumentParser()
    parser.add_argument("--address", required=True, type=str, help="Your wallet address")
    args = parser.parse_args(cli_args)

    return args


def decode_order(value):
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

    return Order(owner_address, token_in, amount_in, token_out, limit, minimum_amount)


def request_price():
    url = "https://devnet-api.multiversx.com/mex/tokens"
    response = requests.request("GET", url)

    return round(response.json()[1]['price'], 3)


def check_price(orders: list[Order], sc):
    current_price = request_price()

    for order in orders:
        if current_price >= order.limit:
            execute_order(order)
            return

    print(f'Current Price of WEGLD is {current_price}')

    sc.enter(6, 1, check_price, (orders, sc,))


def main(cli_args: List[str]):
    # args = parse_arguments(cli_args)
    # open_order()
    # orders = get_orders()
    #
    # map(decode_order, orders)
    #
    # s = sched.scheduler(time.time, time.sleep)
    # s.enter(0, 1, check_price, (orders, s,))
    # s.run()

    execute_order(1)


if __name__ == '__main__':
    # main(sys.argv[1:])

    # open_order()
    execute_order(2)

    # Example usage
    # value = b'\x00\x00\x00\x0cWEGLD-d7c6bb\x00\x00\x00\x08\x1b\xc1mgN\xc8\x00\x00'
    # value = \
    #     b'#\xc9\xe8\xc5\xa8\x7f"\xf5\xc0\xbeV\xcflu\xe9\xb5N\xa1`C\xf9\nz\xcf\x90U J\xc5\xdbUR' \
    #     b'\x00\x00\x00\x0cWEGLD-d7c6bb\x00\x00\x00\x08\x1b\xc1mgN\xc8\x00\x00' \
    #     b'\x00\x00\x00\x0bUSDC-8d4068\x00\x00\x00\x03z\x12\x00'
    # result = decode_order(value)
    # print(result)

    # value = b'#\xc9\xe8\xc5\xa8\x7f"\xf5\xc0\xbeV\xcflu\xe9\xb5N\xa1`C\xf9\nz\xcf\x90U J\xc5\xdbUR' \
    #         b'\x00\x00\x00\x0cWEGLD-d7c6bb\x00\x00\x00\x08\x1b\xc1mgN\xc8\x00\x00' \
    #         b'\x00\x00\x00\x0bUSDC-8d4068\x00\x00\x00\x01%' \
    #         b'\x00\x00\x00\x04\x08v\xbf\x80'
    #
    # order = decode_order(value)
    # print(order)
