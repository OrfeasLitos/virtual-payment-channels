from paymentmethod import Payment_Network
from network import Network_LVPC

class LVPC(Payment_Network):
    def __init__(self, nr_players, max_coins=2000000000000000, bitcoin_fee=1000000, bitcoin_delay=3600,
        coins_for_parties="max_value", lvpc_fee_intermediary = None, opening_transaction_size = 200,
        lvpc_new_virtual_channel_delay = None
    ):
        super().__init__(nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties)
        # TODO: find value for fee, delay.
        self.lvpc_fee_intermediary = lvpc_fee_intermediary
        self.lvpc_new_virtual_channel_delay = lvpc_new_virtual_channel_delay
        self.opening_transaction_size = opening_transaction_size
        # TODO: check what kind of network we need for LVPC
        self.network = Network_LVPC(nr_players)

    # TODO: maybe multiply by 2 in accordance with elmo.
    def get_new_virtual_channel_time(self):
        return self.lvpc_new_virtual_channel_delay

    def get_new_virtual_channel_fee(self):
        return self.lvpc_fee_intermediary
