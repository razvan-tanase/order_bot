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


def open_order():
    transfers = [
        TokenPayment.fungible_from_amount(WEGLD_IDENTIFIER, EGLD_AMOUNT, 18)
    ]

    builder = ContractCallBuilder(
        config,
        contract=contract,
        function_name="openOrder",
        caller=owner,
        call_arguments=[USDC_IDENTIFIER, LIMIT, MIN_VALUE],
        gas_limit=10000000,
        esdt_transfers=transfers,
        nonce=361
    )

    build_and_sign_order(builder)


def execute_order(index: int, nonce: int):
    builder = ContractCallBuilder(
        config,
        contract=contract,
        function_name="executeOrder",
        caller=owner,
        call_arguments=[index, pool_address],
        gas_limit=600000000,
        nonce=nonce
    )

    build_and_sign_order(builder)


def get_orders():
    builder = ContractQueryBuilder(
        contract=contract,
        function=STORAGE_FUNCTION,
        call_arguments=[],
        caller=owner
    )

    query = builder.build()

    network_provider = ApiNetworkProvider(API_URL)
    response = network_provider.query_contract(query)

    return response.get_return_data_parts()


def build_and_sign_order(builder: ContractCallBuilder):
    tx = builder.build()
    tx.signature = signer.sign(tx)

    print("Transaction:", tx.to_dictionary())
    print("Transaction data:", tx.data)

    # network_provider = ApiNetworkProvider(API_URL)
    # response = network_provider.send_transaction(tx)
    # print("Response:", response)
