from pathlib import Path

from multiversx_sdk_core import ContractQueryBuilder, Address, TokenPayment
from multiversx_sdk_core.interfaces import IAddress
from multiversx_sdk_core.transaction_builders import DefaultTransactionBuildersConfiguration, \
    ContractCallBuilder
from multiversx_sdk_network_providers import ApiNetworkProvider
from multiversx_sdk_wallet import UserSigner

from utils import *

contract: IAddress = Address.from_bech32(CONTRACT_ADDRESS)
owner: Address = Address.from_bech32(OWNER_ADDRESS)
pool_address: IAddress = Address.from_bech32(WEGLD_USDC_LIQUIDITY_POOL)

config = DefaultTransactionBuildersConfiguration(chain_id="D")
signer = UserSigner.from_pem_file(Path("wallet-owner.pem"))


def open_order(nonce: int, limit: int):
    transfers = [
        TokenPayment.fungible_from_amount(WEGLD_IDENTIFIER, EGLD_AMOUNT, 18)
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

    build_and_sign_order(builder)


def execute_order(index: int, amount_out_min: int, nonce: int):
    builder = ContractCallBuilder(
        config,
        contract=contract,
        function_name="executeOrder",
        caller=owner,
        call_arguments=[index, pool_address, amount_out_min],
        gas_limit=600000000,
        nonce=nonce
    )

    build_and_sign_order(builder)


def direct_swap(order1_index: int, order2_index: int, nonce: int):
    builder = ContractCallBuilder(
        config,
        contract=contract,
        function_name="executeOrder",
        caller=owner,
        call_arguments=[order1_index, order2_index],
        gas_limit=600000000,
        nonce=nonce
    )

    build_and_sign_order(builder)


def get_orders() -> list[bytes]:
    builder = ContractQueryBuilder(
        contract=contract,
        function=STORAGE_METHOD,
        call_arguments=[],
        caller=owner
    )

    query = builder.build()

    network_provider = ApiNetworkProvider(API_URL)
    response = network_provider.query_contract(query)

    return response.get_return_data_parts()


def get_order(index: int):
    builder = ContractQueryBuilder(
        contract=contract,
        function=GET_ORDER_METHOD,
        call_arguments=[index],
        caller=owner
    )

    query = builder.build()

    network_provider = ApiNetworkProvider(API_URL)
    response = network_provider.query_contract(query)

    print(response.get_return_data_parts())


def get_orders_count() -> int:
    builder = ContractQueryBuilder(
        contract=contract,
        function=ORDERS_COUNT_METHOD,
        call_arguments=[],
        caller=owner
    )

    query = builder.build()

    network_provider = ApiNetworkProvider(API_URL)
    response = network_provider.query_contract(query)

    return int.from_bytes(response.get_return_data_parts()[0], byteorder='big')


def build_and_sign_order(builder: ContractCallBuilder):
    tx = builder.build()
    tx.signature = signer.sign(tx)

    print("Transaction:", tx.to_dictionary())

    network_provider = ApiNetworkProvider(API_URL)
    response = network_provider.send_transaction(tx)
    print("Response:", response)
