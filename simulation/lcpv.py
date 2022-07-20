from paymentmethod import Payment_Network
from network import Network

class LVPC(Payment_Network):
    def __init__(self, nr_players, max_coins=2000000000000000, bitcoin_fee=1000000, bitcoin_delay=3600,
    coins_for_parties="max_value", lvpc_fee = None, opening_transaction_size = 200, lvpc_delay = None):
        super().__init__(nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties)
        # TODO: find value for fee, delay.
        self.lvpc_fee = lvpc_fee
        self.lvpc_delay = lvpc_delay
        self.opening_transaction_size = opening_transaction_size
        # TODO: check what kind of network we need for LVPC
        self.network = Network(nr_players)