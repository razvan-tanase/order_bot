CONTRACT_ADDRESS = "erd1qqqqqqqqqqqqqpgqkm92zsh55uz8mwn93ftw22g7r9k4d6z224fqvu2ydt"
OWNER_ADDRESS = "erd1y0y733dg0u30ts972m8kca0fk482zczrly984nus25sy43wm24fqxzv6lp"
STORAGE_FUNCTION = "getOrders"
API_URL = "https://devnet-api.multiversx.com"

WEGLD_USDC_LIQUIDITY_POOL = "erd1qqqqqqqqqqqqqpgqq67uv84ma3cekpa55l4l68ajzhq8qm3u0n4s20ecvx"
WEGLD_IDENTIFIER = "WEGLD-d7c6bb"
USDC_IDENTIFIER = "USDC-8d4068"

EGLD_AMOUNT = 2
EGLD_VALUE = 32.81
LIMIT = int('{:.0f}'.format(EGLD_VALUE * 10 ** 18))
MIN_VALUE = int(EGLD_AMOUNT * EGLD_VALUE * 0.98703 * 10 ** 6)


class Order:
    def __init__(self, owner, token_in, amount_in, token_out, limit, amount_out_min):
        self.owner = owner
        self.token_in = token_in
        self.amount_in = amount_in
        self.token_out = token_out
        self.limit = limit
        self.amount_out_min = amount_out_min

    def __str__(self):
        return "Order: owner: {}, token_in: {}, amount_in: {}, token_out: {}, limit: {}, amount_out_min: {}".format(
            self.owner, self.token_in, self.amount_in, self.token_out, self.limit, self.amount_out_min)
