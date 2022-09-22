from custom_elmo_lvpc_donner import Custom_Elmo_LVPC_Donner

class Donner(Custom_Elmo_LVPC_Donner):
    def __init__(
        self, nr_players, bitcoin_fee = 1000000, bitcoin_delay = 3600,
        coins_for_parties = "max_value", base_fee = 20000,
        fee_rate = 0.0004, opening_transaction_size = 121.5,
    ):
        super().__init__(
            "Donner", nr_players, opening_transaction_size, bitcoin_fee,
            bitcoin_delay, coins_for_parties, base_fee, fee_rate
        )
