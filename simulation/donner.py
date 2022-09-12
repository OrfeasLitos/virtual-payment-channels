from custom_elmo_lvpc_donner import Custom_Elmo_LVPC_Donner

class Donner(Custom_Elmo_LVPC_Donner):
    def __init__(
        self, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600,
        coins_for_parties = "max_value", base_fee = 20000,
        # review: probably need to remove default value `200` from `opening_transaction_size`, possibly even remove `opening_transaction_size` entirely
        fee_rate = 0.0004, opening_transaction_size = 121.5,
        donner_pay_delay = 0.05, donner_new_virtual_channel_delay = 0.05
    ):
    # review: opening_transaction_size = 78.5 + 43*(len(path)-1)
        super().__init__(
            "Donner", nr_players, opening_transaction_size, max_coins, bitcoin_fee, bitcoin_delay,
            coins_for_parties, base_fee, fee_rate, donner_pay_delay, donner_new_virtual_channel_delay
        )
