import sched
import sys
import time
from argparse import ArgumentParser
from typing import List

from API import execute_order, get_orders, get_orders_count, direct_swap, clear_entry
from utils import *

# Global variables
nonce = 2082
NO_OF_TRIES = 20
last_delay = 0
bot_orders = []
prices = {}  # {token_out: price}
pending_orders = {}  # {bot_order_index: (sc_order_id, no_tries)}
orderbook = {}  # {price: {token_out: (bot_order_index, sc_order_id)}}
executed_orders = []  # [sc_order_id]

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


# def check_fill_against_orderbook(orders: list):
#     global nonce
#
#     for order in orders:
#         new_order = decode_order(order)
#         amount_out = new_order.amount_in * new_order.limit
#
#         if amount_out in orderbook:
#             no_bot_orders = len(bot_orders)
#             for token_out in orderbook[amount_out]:
#                 if token_out != new_order.token_out:
#                     bot_order_index, sc_order_id = orderbook[amount_out][token_out]
#
#                     direct_swap(bot_order_index, no_bot_orders, nonce)
#                     nonce += 1
#
#                     pending_orders[bot_order_index] = (sc_order_id, 0)
#                     bot_orders[bot_order_index] = None
#                     bot_orders.append(new_order)
#
#                     del orderbook[amount_out][token_out]
#                     break
#
#             if no_bot_orders == len(bot_orders):
#                 orderbook[amount_out][new_order.token_out] = (no_bot_orders, new_order.idx)
#         else:
#             orderbook[amount_out] = {new_order.token_out: (len(bot_orders), new_order.idx)}
#             bot_orders.append(new_order)

def update_orders():
    global bot_orders, nonce

    new_bot_orders = []
    for order in bot_orders:
        if order is not None:
            new_bot_orders.append(order.idx)
        else:
            new_bot_orders.append(None)
    print(f'BOT at start: {new_bot_orders}')

    if pending_orders:
        no_sc_orders = get_orders_count()

        if not no_sc_orders:
            pending_orders.clear()
            bot_orders.clear()
            return

        sc_orders = get_orders()
        contract_orders = [decode_order(order).idx for order in sc_orders]
        print(f'CONTRACT: {contract_orders}')
        pending_order_indexes = list(pending_orders)

        for pending_order_index in pending_order_indexes:
            if pending_order_index >= no_sc_orders:
                print(f'{pending_order_index} >= {no_sc_orders}')
                rev_idx = -1
                print(f'pending_order_indexes: {pending_order_indexes}')
                while pending_order_indexes[rev_idx] != pending_order_index:
                    del pending_orders[pending_order_indexes[rev_idx]]
                    rev_idx -= 1

                del pending_orders[pending_order_index]
                bot_orders = bot_orders[:no_sc_orders]

                print(f'pending_orders: {pending_orders}')
                print(f'executed_orders: {executed_orders}')

                new_bot_orders = []
                for order in bot_orders:
                    if order is not None:
                        new_bot_orders.append(order.idx)
                    else:
                        new_bot_orders.append(None)
                print(f'BOT at middle: {new_bot_orders}')

                return

            pending_sc_order_id, no_tries = pending_orders[pending_order_index]
            sc_order_id = int.from_bytes(sc_orders[pending_order_index][:8], byteorder='big')
            if sc_order_id != pending_sc_order_id:
                if sc_order_id not in executed_orders:
                    bot_orders[pending_order_index] = decode_order(sc_orders[pending_order_index])
                    del pending_orders[pending_order_index]
                else:
                    clear_entry(pending_order_index + 1, nonce)
                    nonce += 1
            else:
                no_tries += 1

                if no_tries == NO_OF_TRIES:
                    bot_orders[pending_order_index] = decode_order(sc_orders[pending_order_index])
                    del pending_orders[pending_order_index]
                else:
                    pending_orders[pending_order_index] = (pending_sc_order_id, no_tries)

        bot_orders = bot_orders[:pending_order_indexes[-1] + 1]

    no_bot_orders = len(bot_orders)
    if get_orders_count() > no_bot_orders:
        bot_orders += [decode_order(order) for order in get_orders()[no_bot_orders:]]

    new_bot_orders = []
    for order in bot_orders:
        if order is not None:
            new_bot_orders.append(order.idx)
        else:
            new_bot_orders.append(None)
    print(f'BOT at end: {new_bot_orders}')


# def update_orders():
#     global bot_orders
#
#     no_bot_orders = len(bot_orders)
#     no_sc_orders = get_orders_count()
#
#     sc_orders = None

# if pending_orders:
#     if not no_sc_orders:
#         pending_orders.clear()
#         bot_orders.clear()
#         return
#
#     sc_orders = sc_orders or get_orders()
#
#     if no_sc_orders > no_bot_orders:
#         for pending_order_index in list(pending_orders):
#
#             pending_sc_order_id, no_tries = pending_orders[pending_order_index]
#
#             # print(f'no_bot_orders: {no_bot_orders}, no_sc_orders: {no_sc_orders}, pending_order_index: {pending_order_index}, pending_sc_order_id: {pending_sc_order_id}')
#             if int.from_bytes(sc_orders[pending_order_index][:8], byteorder='big') != pending_sc_order_id:
#                 bot_orders[pending_order_index] = decode_order(sc_orders[pending_order_index])
#                 del pending_orders[pending_order_index]
#             else:
#                 no_tries += 1
#
#                 if no_tries == NO_OF_TRIES:
#                     bot_orders[pending_order_index] = decode_order(sc_orders[pending_order_index])
#                     del pending_orders[pending_order_index]
#                 else:
#                     pending_orders[pending_order_index] = (pending_sc_order_id, no_tries)
#
#         for i in range(-1, -bot_orders - 1, -1):
#             if bot_orders[i] == sc_orders[i - (no_sc_orders - no_bot_orders)]:
#
#                 # Trim the smaller list and append the remainder of the larger list
#                 bot_orders = bot_orders[:i]
#                 bot_orders.extend(sc_orders[i - (no_sc_orders - no_bot_orders):])
#                 break
#
#     for pending_order_index in list(pending_orders):
#         if pending_order_index >= no_sc_orders:
#             del pending_orders[pending_order_index]
#             bot_orders.pop()
#             continue
#
#         pending_sc_order_id, no_tries = pending_orders[pending_order_index]
#
#         # print(f'no_bot_orders: {no_bot_orders}, no_sc_orders: {no_sc_orders}, pending_order_index: {pending_order_index}, pending_sc_order_id: {pending_sc_order_id}')
#         if int.from_bytes(sc_orders[pending_order_index][:8], byteorder='big') != pending_sc_order_id:
#             bot_orders[pending_order_index] = decode_order(sc_orders[pending_order_index])
#             del pending_orders[pending_order_index]
#             # bot_orders.pop()
#         else:
#             no_tries += 1
#
#             if no_tries == NO_OF_TRIES:
#                 bot_orders[pending_order_index] = decode_order(sc_orders[pending_order_index])
#                 del pending_orders[pending_order_index]
#             else:
#                 pending_orders[pending_order_index] = (pending_sc_order_id, no_tries)

# if no_sc_orders > no_bot_orders:
#     # check_fill_against_orderbook(get_orders()[no_bot_orders:])
#     sc_orders = get_orders()
#     bot_orders += [decode_order(order) for order in sc_orders[no_bot_orders:]]


def check_price():
    global nonce

    start_time = time.time()

    if bot_orders:
        request_prices()

        for index, order in enumerate(bot_orders):
            if order is not None and prices[order.token_in] >= order.limit:
                execute_order(index + 1, 100, nonce)
                pending_orders[index] = (order.idx, 0)
                executed_orders.append(order.idx)
                nonce += 1

                print(f'Order {order.idx} executed')

                bot_orders[index] = None
    else:
        print('No orders to execute')

    update_orders()

    elapsed_time = time.time() - start_time
    delay = max(6 - elapsed_time, 0)

    print(f'Elapsed time: {elapsed_time}')

    s.enter(delay, 1, check_price, ())


def main(cli_args: List[str]):
    global bot_orders

    # args = parse_arguments(cli_args)
    if get_orders_count() > 0:
        # check_fill_against_orderbook(get_orders())
        bot_orders = [decode_order(order) for order in get_orders()]

    s.enter(0, 1, check_price, ())
    s.run()


if __name__ == '__main__':
    # main(sys.argv[1:])

    bot_orders = [decode_order(order) for order in get_orders()]
    new_bot_orders = []
    for order in bot_orders:
        if order is not None:
            new_bot_orders.append(order.idx)
        else:
            new_bot_orders.append(None)
    new_bot_orders.sort()
    print(new_bot_orders)

    # price = 27.512
    # count = 0
    # bot_orders = [decode_order(order) for order in get_orders()]
    # for index, order in enumerate(bot_orders):
    #     if price >= order.limit:
    #         count += 1
    #         print(index, order.idx, order.limit)
    #
    # print(count)
