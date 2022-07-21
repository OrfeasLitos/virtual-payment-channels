from paymentmethod import Payment_Network, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE_LVPC
from network import Network_LVPC

class LVPC(Payment_Network):
    def __init__(self, nr_players, max_coins=2000000000000000, bitcoin_fee=1000000, bitcoin_delay=3600,
        coins_for_parties="max_value", lvpc_fee_intermediary = None, opening_transaction_size = 200,
        lvpc_new_virtual_channel_delay = None, lvpc_pay_delay = None
    ):
        super().__init__(nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties)
        # TODO: find value for fee, delay.
        self.lvpc_fee_intermediary = lvpc_fee_intermediary
        self.lvpc_new_virtual_channel_delay = lvpc_new_virtual_channel_delay
        self.lvpc_pay_delay = lvpc_pay_delay
        self.opening_transaction_size = opening_transaction_size
        # TODO: check what kind of network we need for LVPC
        self.network = Network_LVPC(nr_players)

    # TODO: maybe multiply by 2 in accordance with elmo.
    def get_new_virtual_channel_time(self):
        return self.lvpc_new_virtual_channel_delay

    def get_new_virtual_channel_fee(self):
        return self.lvpc_fee_intermediary

    # almost equal to the method for Elmo
    def get_new_channel_option(self, sender, receiver, value, future_payments):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        new_channel_time = self.plain_bitcoin.get_delay() + self.lvpc_pay_delay
        new_channel_fee = self.plain_bitcoin.get_fee(self.opening_transaction_size)
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        sender_coins = min(
            self.plain_bitcoin.coins[sender] - value - new_channel_fee,
            MULTIPLIER_CHANNEL_BALANCE_LVPC * sum_future_payments
        )
        if sender_coins < 0:
            return None
        self.network.add_channel(sender, sender_coins, receiver, value, None)
        new_channel_centrality = self.network.get_harmonic_centrality()
        new_channel_distance = self.get_distances(sender, future_payments)
        self.network.close_channel(sender, receiver)
        return {
            'delay': new_channel_time,
            'fee': new_channel_fee,
            'centrality': new_channel_centrality,
            'distance': new_channel_distance,
            'payment_information': {
                'kind': 'LVPC-open-channel',
                'data': (sender, receiver, value, sender_coins)
            }
        }
