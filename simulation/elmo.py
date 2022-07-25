import math
import operator
from paymentmethod import PlainBitcoin, Payment_Network, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE_ELMO
from network import Network_Elmo
from custom_elmo_lvpc_donner import Custom_Elmo_LVPC_Donner

class Elmo(Custom_Elmo_LVPC_Donner):
    # TODO: find reasonable value for fee_intermediary, opening_transaction_size, elmo_delay
    def __init__(
        self, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600, 
        coins_for_parties = "max_value", fee_intermediary = 10000,
        opening_transaction_size = 200, elmo_pay_delay = 0.05,
        elmo_new_virtual_channel_delay = 1
    ):
        super().__init__(
            "Elmo", nr_players, max_coins = 2000000000000000, bitcoin_fee = 1000000,
            bitcoin_delay = 3600,  coins_for_parties = "max_value", fee_intermediary = 10000,
            opening_transaction_size = 200, pay_delay = 0.05, new_virtual_channel_delay = 1
        )
