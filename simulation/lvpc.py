from paymentmethod import sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE
from custom_elmo_lvpc_donner import Custom_Elmo_LVPC_Donner

class LVPC(Custom_Elmo_LVPC_Donner):
    def __init__(self, nr_players, max_coins=2000000000000000, bitcoin_fee=1000000, bitcoin_delay=3600,
        coins_for_parties="max_value", base_fee = 20000, fee_rate = 0,
        opening_transaction_size = 200, lvpc_new_virtual_channel_delay = 1, lvpc_pay_delay = 0.05
    ):
        super().__init__(
            "LVPC", nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties,
            base_fee, fee_rate, opening_transaction_size, lvpc_pay_delay,
            lvpc_new_virtual_channel_delay
        )
