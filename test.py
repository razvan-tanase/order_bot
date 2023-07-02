import sched
import time
from pathlib import Path

import requests
from multiversx_sdk_core import TokenPayment, Address
from multiversx_sdk_core.interfaces import IAddress
from multiversx_sdk_core.transaction_builders import ContractCallBuilder, DefaultTransactionBuildersConfiguration
from multiversx_sdk_network_providers import ApiNetworkProvider
from multiversx_sdk_wallet import UserSigner

from utils import WEGLD_IDENTIFIER, CONTRACT_ADDRESS, USDC_IDENTIFIER, API_URL

contract: IAddress = Address.from_bech32(CONTRACT_ADDRESS)
owner: Address = Address.from_bech32("erd10u02xc9r8kvjrhr922mge0kv53flczzxr2hj620cez8xmzu6422qwzn4za")

config = DefaultTransactionBuildersConfiguration(chain_id="D")
signer = UserSigner.from_pem_file(Path("wallet-test.pem"))

NUMBER_OF_ORDERS = 50
SLEEP_TIME = 30
AMOUNT_IN = 0.01

nonce = 1956
rounds = 1
price = 0
s = sched.scheduler(time.time, time.sleep)


def request_price():
    url = "https://devnet-api.multiversx.com/mex/tokens"
    response = requests.request("GET", url)

    tokens = response.json()
    return round(tokens[1]["price"], 4)


def open_order(limit: int, nonce: int):
    transfers = [
        TokenPayment.fungible_from_amount(WEGLD_IDENTIFIER, AMOUNT_IN, 18)
    ]

    builder = ContractCallBuilder(
        config,
        contract=contract,
        function_name="openOrder",
        caller=owner,
        call_arguments=[USDC_IDENTIFIER, limit],
        gas_limit=10000000,
        esdt_transfers=transfers,
        nonce=nonce
    )

    tx = builder.build()
    tx.signature = signer.sign(tx)

    network_provider = ApiNetworkProvider(API_URL)
    response = network_provider.send_transaction(tx)
    print("Response:", response)


def add_orders():
    global nonce, rounds

    for i in range(0, NUMBER_OF_ORDERS):
        if i % 2 == 0:
            open_order(int('{:.0f}'.format(price * 0.998 * 10 ** 18)), nonce)
        else:
            open_order(int('{:.0f}'.format(price * 1.1 * 10 ** 18)), nonce)

        nonce += 1

    print(f'Round {rounds} finished')
    rounds += 1

    s.enter(SLEEP_TIME, 1, add_orders, ())


if __name__ == '__main__':
    price = request_price()
    print(f'Price: {price}')

    s.enter(0, 1, add_orders, ())
    s.run()
