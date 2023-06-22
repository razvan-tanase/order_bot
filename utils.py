import requests

CONTRACT_ADDRESS = "erd1qqqqqqqqqqqqqpgq5mqkduu99vfqlg3qrawf2f4lft6355vn24fqkmenfn"
OWNER_ADDRESS = "erd1y0y733dg0u30ts972m8kca0fk482zczrly984nus25sy43wm24fqxzv6lp"
STORAGE_METHOD = "getOrders"
GET_ORDER_METHOD = "getOrder"
ORDERS_COUNT_METHOD = "getOrdersCount"
API_URL = "https://devnet-api.multiversx.com"

WEGLD_USDC_LIQUIDITY_POOL = "erd1qqqqqqqqqqqqqpgqq67uv84ma3cekpa55l4l68ajzhq8qm3u0n4s20ecvx"
WEGLD_IDENTIFIER = "WEGLD-d7c6bb"
USDC_IDENTIFIER = "USDC-8d4068"

EGLD_AMOUNT = 1
EGLD_VALUE = 32.8466
LIMIT = int('{:.0f}'.format(EGLD_VALUE * 10 ** 18))
MIN_VALUE = int(EGLD_AMOUNT * EGLD_VALUE * 0.9 * 10 ** 6)


class Order:
    def __init__(self, idx, token_in, amount_in, token_out, limit):
        self.idx = idx
        self.token_in = token_in
        self.amount_in = amount_in
        self.token_out = token_out
        self.limit = limit

    def __str__(self):
        return f"Order {self.idx}:\n" \
               f"Token in: {self.token_in}\n" \
               f"Amount in: {self.amount_in}\n" \
               f"Token out: {self.token_out}\n" \
               f"Limit: {self.limit}"
