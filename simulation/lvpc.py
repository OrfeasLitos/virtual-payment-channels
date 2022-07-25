from paymentmethod import sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE
from custom_elmo_lvpc_donner import Custom_Elmo_LVPC_Donner

class LVPC(Custom_Elmo_LVPC_Donner):
    def __init__(self, nr_players, max_coins=2000000000000000, bitcoin_fee=1000000, bitcoin_delay=3600,
        coins_for_parties="max_value", lvpc_fee_intermediary = 10000, opening_transaction_size = 200,
        lvpc_new_virtual_channel_delay = 1, lvpc_pay_delay = 0.05
    ):
        super().__init__(
            "LVPC", nr_players, max_coins, bitcoin_fee, bitcoin_delay, 
            coins_for_parties, lvpc_fee_intermediary, opening_transaction_size, lvpc_pay_delay,
            lvpc_new_virtual_channel_delay
        )

    # adjusted from Elmo
    # TODO: how are the balances handled?
    def get_new_virtual_channel_option(self, sender, receiver, value, future_payments):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        # this is a simplification. TODO: think if this is what we want.
        anticipated_lock_value = sum_future_payments + value
        cost_and_path = self.network.find_cheapest_path_for_new_virtual(sender, receiver, anticipated_lock_value, self.fee_intermediary)
        if cost_and_path is None:
            return None
        hops, path = cost_and_path
        new_virtual_channel_fee = self.get_new_virtual_channel_fee(path)
        # the factor is introduced so that lower channel doesn't end up with 0 balance.
        availability_factor = 4
        base_channels_max_lock_values = [
            self.network.graph[path[i]][path[i+1]]['balance'] / availability_factor - value - new_virtual_channel_fee for i in range(len(path)-1)
        ]
        base_channels_max_lock_values
        max_common_lock_value = min(
            base_channels_max_lock_values
        )
        desired_virtual_coins = MULTIPLIER_CHANNEL_BALANCE * sum_future_payments
        sender_coins = min(max_common_lock_value, desired_virtual_coins)
        if sender_coins < 0:
            return None
        payment_information = {'kind': 'LVPC-open-virtual-channel', 'data': (path, value, sender_coins)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        new_virtual_channel_time = self.get_new_virtual_channel_time(hops)
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
