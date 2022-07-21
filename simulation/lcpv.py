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

    # adjusted from Elmo
    # TODO: how are the balances handled?
    def get_new_virtual_channel_option(self, sender, receiver, value, future_payments):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        # this is a simplification. TODO: think if this is what we want.
        anticipated_lock_value = sum_future_payments + value
        cost_and_path = self.network.find_cheapest_path(sender, receiver, anticipated_lock_value, self.lvpc_fee_intermediary)
        if cost_and_path is None:
            return None
        _, path = cost_and_path
        new_virtual_channel_fee = self.get_new_virtual_channel_fee()
        availability_factor = 4
        base_channels_max_lock_values = [
            self.network.graph[path[i]][path[i+1]]['balance'] / availability_factor - value - new_virtual_channel_fee for i in range(len(path)-1)
        ]
        base_channels_max_lock_values
        max_common_lock_value = min(
            base_channels_max_lock_values
        )
        desired_virtual_coins = MULTIPLIER_CHANNEL_BALANCE_LVPC * sum_future_payments
        sender_coins = min(max_common_lock_value, desired_virtual_coins)
        if sender_coins < 0:
            return None
        payment_information = {'kind': 'LVPC-open-virtual-channel', 'data': (path, value, sender_coins)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        new_virtual_channel_time = self.get_new_virtual_channel_time()
        new_virtual_channel_centrality = self.network.get_harmonic_centrality()
        new_virtual_channel_distance = self.get_distances(sender, future_payments)
        self.undo(payment_information)
        return {
            'delay': new_virtual_channel_time,
            'fee': new_virtual_channel_fee,
            'centrality': new_virtual_channel_centrality,
            'distance': new_virtual_channel_distance,
            'payment_information': payment_information
        }

    # copied from elmo
    def get_lvpc_pay_option(self, sender, receiver, value, future_payments):
        payment_information = {'kind': 'LVPC-pay', 'data': (sender, receiver, value)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        centrality_lvpc_pay = self.network.get_harmonic_centrality()
        distance_lvpc_pay = self.get_distances(sender, future_payments)
        self.undo(payment_information)
        return {
            'delay': self.lvpc_pay_delay,
            'fee': 0,
            'centrality': centrality_lvpc_pay,
            'distance': distance_lvpc_pay,
            'payment_information': payment_information
        }

    # copied from Elmo
    def get_payment_options(self, sender, receiver, value, future_payments):
        onchain_option = self.get_onchain_option(sender, receiver, value, future_payments)
        new_channel_option = self.get_new_channel_option(sender, receiver, value, future_payments)
        new_virtual_channel_option = self.get_new_virtual_channel_option(sender, receiver, value, future_payments)
        lvpc_pay_option = self.get_lvpc_pay_option(sender, receiver, value, future_payments)
        options = [onchain_option, new_channel_option, new_virtual_channel_option, lvpc_pay_option]
        return [option for option in options if option is not None]