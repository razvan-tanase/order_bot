import sched
import sys
import time
from argparse import ArgumentParser
from typing import List
from itertools import islice

from API import execute_order, get_orders, get_orders_count, direct_swap, open_order
from utils import *

# Global variables
nonce = 596
bot_orders = []
prices: dict[str:float] = {}    # {token_out: price}
pending_orders: dict[int:int] = {}  # {bot_order_index: sc_order_id}
orderbook: dict[float: dict[str: (int, int)]] = {}  # {price: {token_out: (bot_order_index, sc_order_id)}}

s = sched.scheduler(time.time, time.sleep)


def parse_arguments(cli_args: List[str]):
    parser = ArgumentParser()
    parser.add_argument("--address", required=True, type=str, help="Your wallet address")
    parser.add_argument("--pem", required=True, type=str, help="Path to your pem file")
    args = parser.parse_args(cli_args)

    return args


def decode_order(b) -> Order:
    # Unpack the index of the order
    object_index = int.from_bytes(b[:8], byteorder='big')
    b = b[8:]

    # Unpack the length of the token_in identifier
    token_in_length = int.from_bytes(b[:4], byteorder='big')
    b = b[4:]

    # Unpack the token_in string identifier
    token_in = b[:token_in_length].decode('ascii')
    b = b[token_in_length:]

    # Unpack the number of how many bytes the next number will be
    amount_in_length = int.from_bytes(b[:4], byteorder='big')
    b = b[4:]

    # Unpack the amount in
    amount_in = int.from_bytes(b[:amount_in_length], byteorder='big')
    b = b[amount_in_length:]

    # Unpack the length of the token_out identifier
    token_out_length = int.from_bytes(b[:4], byteorder='big')
    b = b[4:]

    # Unpack the token_out string identifier
    token_out = b[:token_out_length].decode('ascii')
    b = b[token_out_length:]

    # Unpack the number of how many bytes the next number will be
    limit_length = int.from_bytes(b[:4], byteorder='big')
    b = b[4:]

    # Unpack the limit
    limit = int.from_bytes(b[:limit_length], byteorder='big')

    return Order(object_index, token_in, amount_in * (10 ** -18), token_out, limit * (10 ** -18))


def request_prices():
    url = "https://devnet-api.multiversx.com/mex/tokens"
    response = requests.request("GET", url)

    tokens = response.json()
    for token in tokens:
        prices[token["id"]] = round(token["price"], 4)


def check_fill_against_orderbook(orders: [Order]):
    global nonce

    for order in orders:
        new_order = decode_order(order)
        amount_out = new_order.amount_in * new_order.limit

        if amount_out in orderbook:
            no_bot_orders = len(bot_orders)
            for token_out in orderbook[amount_out]:
                if token_out != new_order.token_out:
                    bot_order_index, sc_order_id = orderbook[amount_out][token_out]

                    direct_swap(bot_order_index, no_bot_orders, nonce)
                    nonce += 1

                    pending_orders[bot_order_index] = sc_order_id
                    bot_orders[bot_order_index] = None
                    bot_orders.append(new_order)

                    del orderbook[amount_out][token_out]
                    break

            if no_bot_orders == len(bot_orders):
                orderbook[amount_out][new_order.token_out] = (no_bot_orders, new_order.idx)
        else:
            orderbook[amount_out] = {new_order.token_out: (len(bot_orders), new_order.idx)}
            bot_orders.append(new_order)


def update_orders():
    no_bot_orders = len(bot_orders)

    if no_bot_orders == 0:
        if get_orders_count() > 0:
            check_fill_against_orderbook(get_orders())

        return

    if pending_orders:
        sc_orders = get_orders()
        no_sc_orders = len(sc_orders)

        if no_sc_orders:
            pending_order_indexes = list(islice(pending_orders, no_sc_orders))
            for pending_order_index in pending_order_indexes:
                sc_order_id = int.from_bytes(sc_orders[pending_order_index][:8], byteorder='big')
                if sc_order_id != pending_orders[pending_order_index]:
                    bot_orders[pending_order_index] = decode_order(sc_orders[pending_order_index])
                    del pending_orders[pending_order_index]
                    bot_orders.pop()

            if len(sc_orders) > len(bot_orders):
                check_fill_against_orderbook(sc_orders[no_bot_orders:])

            return

    # If I didn't execute any orders in the previous iteration, I check for any newly added orders.
    no_sc_orders = get_orders_count()
    if no_sc_orders > no_bot_orders:
        check_fill_against_orderbook(get_orders()[no_bot_orders:])


# def f():
#     for index, order in enumerate(bot_orders):
#         if order is not None:
#             if prices[order.token_in] >= order.limit:
#                 execute_order(index + 1, int(order.amount_in * order.limit * 0.9 * 10 ** 6), nonce)
#                 pending_orders[index] = order.idx
#                 nonce += 1
#
#                 print(f'Order {index + 1} executed')
#
#                 if index == len(bot_orders) - 1:
#                     bot_orders.pop()
#                 else:
#                     bot_orders[index] = None

def check_price():
    global nonce

    start_time = time.time()

    if bot_orders:
        request_prices()

        for index, order in enumerate(bot_orders):
            if order is not None:
                if prices[order.token_in] >= order.limit:
                    execute_order(index + 1, int(10 ** 6), nonce)
                    pending_orders[index] = order.idx
                    nonce += 1

                    print(f'Order {index + 1} executed')

                    if index == len(bot_orders) - 1:
                        bot_orders.pop()
                    else:
                        bot_orders[index] = None
    else:
        print('No orders to execute')

    update_orders()

    elapsed_time = time.time() - start_time
    delay = max(6 - elapsed_time, 0)

    print(f'Elapsed time: {elapsed_time}')

    s.enter(delay, 1, check_price, ())


def main(cli_args: List[str]):
    # args = parse_arguments(cli_args)
    if get_orders_count() > 0:
        check_fill_against_orderbook(get_orders())

    s.enter(0, 1, check_price, ())
    s.run()


if __name__ == '__main__':
    main(sys.argv[1:])

    # value = EGLD_VALUE
    # limit = int('{:.0f}'.format(value * 10 ** 18))
    #
    # for i in range(2):
    #     open_order(nonce, limit)
    #     nonce += 1
    #     value += 0.0001
    #     limit = int('{:.0f}'.format(value * 10 ** 18))
    #
    # value = 27.8480
    # limit = int('{:.0f}'.format(value * 10 ** 18))
    # for i in range(3):
    #     open_order(nonce, limit)
    #     nonce += 1
    #     value += 0.0001
    #     limit = int('{:.0f}'.format(value * 10 ** 18))
