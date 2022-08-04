from custom_elmo_lvpc_donner import Custom_Elmo_LVPC_Donner

class Donner(Custom_Elmo_LVPC_Donner):
    # TODO: find reasonable value for base_fee, opening_transaction_size, delay
    def __init__(
        self, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600, 
        coins_for_parties = "max_value", base_fee = 20000,
        fee_rate = 0, opening_transaction_size = 200,
        donner_pay_delay = 0.05, donner_new_virtual_channel_delay = 1
    ):
        super().__init__(
            "Donner", nr_players, max_coins, bitcoin_fee, bitcoin_delay,  coins_for_parties, base_fee,
            fee_rate, opening_transaction_size, donner_pay_delay, donner_new_virtual_channel_delay
        )
