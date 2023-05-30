from multiversx_sdk_core import ContractQueryBuilder, Address
from multiversx_sdk_core.interfaces import IAddress
from multiversx_sdk_network_providers import ApiNetworkProvider


def main():
    contract: IAddress = Address.from_bech32("erd1qqqqqqqqqqqqqpgqkm92zsh55uz8mwn93ftw22g7r9k4d6z224fqvu2ydt")
    owner: Address = Address.from_bech32("erd1y0y733dg0u30ts972m8kca0fk482zczrly984nus25sy43wm24fqxzv6lp")

    builder = ContractQueryBuilder(
        contract=contract,
        function="getOrders",
        call_arguments=[],
        caller=owner
    )

    query = builder.build()

    network_provider = ApiNetworkProvider("https://devnet-api.multiversx.com")
    response = network_provider.query_contract(query)

    print("Return code:", response.return_code)
    print("Return data:", response.return_data)
    print("Return message:", response.return_message)
    print("Return data parts:", response.get_return_data_parts())
    print("Return data as dictionary:", response.to_dictionary())


def decode_value(value):
    # Extracting the length of the string
    length = int.from_bytes(value[:4], byteorder='big')

    # Extracting the string
    string = value[4:4 + length].decode()

    # Extracting the length of the value
    value_length = int.from_bytes(value[4 + length:4 + length + 4], byteorder='big')

    # Extracting the value
    encoded_value = int.from_bytes(value[4 + length + 4:4 + length + 4 + value_length], byteorder='big')

    return string, encoded_value

if __name__ == '__main__':
    main()

    # Example usage
    # value = b'\x00\x00\x00\x0cWEGLD-d7c6bb\x00\x00\x00\x08\x1b\xc1mgN\xc8\x00\x00'
    # value = \
    #     b'#\xc9\xe8\xc5\xa8\x7f"\xf5\xc0\xbeV\xcflu\xe9\xb5N\xa1`C\xf9\nz\xcf\x90U J\xc5\xdbUR' \
    #     b'\x00\x00\x00\x0cWEGLD-d7c6bb\x00\x00\x00\x08\x1b\xc1mgN\xc8\x00\x00' \
    #     b'\x00\x00\x00\x0bUSDC-8d4068\x00\x00\x00\x03z\x12\x00'
    # result = decode_value(value)
    # print(result)

    # value = b'#\xc9\xe8\xc5\xa8\x7f"\xf5\xc0\xbeV\xcflu\xe9\xb5N\xa1`C\xf9\nz\xcf\x90U J\xc5\xdbUR'
    # hex_value = value.hex()
    # print(hex_value)
    # print(Address.from_hex(hex_value, "erd").bech32())
