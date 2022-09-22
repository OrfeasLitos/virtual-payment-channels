import math
import operator
import numpy as np
import networkx as nx
from paymentmethod import (
    Payment_Network, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE,
    DUMMY_PAYMENT_VALUE
)
from network import Network_Elmo, Network_LVPC, Network_Donner

MULTIPLIER_BALANCE_RECURSION_LVPC = 1.5
AVAILABILITY_FACTOR = 4

class Custom_Elmo_LVPC_Donner(Payment_Network):
    def __init__(
        self, method_name, nr_players, opening_transaction_size,
        bitcoin_fee = 1000000, bitcoin_delay = 3600,
        coins_for_parties = "max_value", base_fee = 20000, fee_rate = 0.0004,
    ):
        super().__init__(nr_players, bitcoin_fee, bitcoin_delay, coins_for_parties)
        self.method_name = method_name
        self.opening_transaction_size = opening_transaction_size
        self.open_channel_string = method_name + "-open-channel"
        self.open_virtual_channel_string = method_name + "-open-virtual-channel"
        self.pay_string = method_name + "-pay"
        if method_name == "Elmo":
            self.network = Network_Elmo(nr_players)
        elif method_name == "LVPC":
            self.network = Network_LVPC(nr_players)
        elif method_name == "Donner":
            self.network = Network_Donner(nr_players)
        else:
            raise ValueError

        self.base_fee = base_fee
        self.fee_rate = fee_rate
        # delay for opening new virtual channel (per hop)
        self.pay_delay = 1.5 * self.base_delay

    def get_distances_and_paths_from_source(self, source, future_payments):
        """
        Returns weighted distances to the future parties and to parties not occuring in future payments.
        Muiltiple payments to same party give multiple distances.
        """
        distances = []
        # weight if we are endpoint
        weight_endpoint = 100
        # weight if we are possible intermediary
        weight_intermediary = 10
        # weight for other parties
        weight_other = 1
        encountered_parties = set({source})
        dummy_lock_value = MULTIPLIER_CHANNEL_BALANCE * DUMMY_PAYMENT_VALUE
        fee_intermediary = self.base_fee + dummy_lock_value * self.fee_rate
        cheapest_paths_from_sender = self.network.find_cheapest_paths_from_sender(source, dummy_lock_value, fee_intermediary)
        calculated_cheapest_paths = {}
        #near_parties = nx.single_source_shortest_path_length(self.network.graph, source, 5)
        path_data = []
        for future_sender, future_receiver, value in future_payments:
            encountered_parties.add(future_sender)
            encountered_parties.add(future_receiver)
            dummy_lock_value = MULTIPLIER_CHANNEL_BALANCE * DUMMY_PAYMENT_VALUE + value
            # TODO:
            # I commented the part after the next if. And it made the simulation much much faster.
            # The bottleneck seems to be the find_cheapest_path method.
            # We precompute cheapest_paths_from_sender and use it where possible
            # if we also want to calculate the distances for the payments in which we are intermediaries
            # we either have to call find_cheapest_path every time or we have to precompute all shortest_paths
            # in the network which probably doesn't scale well. But I haven't yet tested how it scales.
            if future_sender != source: #and future_sender in near_parties:
                if (future_sender, source) not in calculated_cheapest_paths:
                    cheapest_path = self.network.find_cheapest_path(
                        future_sender, source, dummy_lock_value, self.base_fee + dummy_lock_value * self.fee_rate
                    )
                    calculated_cheapest_paths[(future_sender, source)] = cheapest_path
                else:
                    cheapest_path = calculated_cheapest_paths[(future_sender, source)]
                path_data.append((
                    weight_endpoint if future_receiver == source else weight_intermediary,
                    cheapest_path
                ))
            if future_receiver != source:
                path_data.append((
                    weight_endpoint if future_sender == source else weight_intermediary,
                    cheapest_paths_from_sender.get(future_receiver)
                ))

        dummy_lock_value = MULTIPLIER_CHANNEL_BALANCE * DUMMY_PAYMENT_VALUE
        for party in (set(self.network.graph.nodes()).difference(encountered_parties)):
            path_data.append((
                weight_other,
                cheapest_paths_from_sender.get(party)
            ))

        for weight, cheapest_path in path_data:
            if cheapest_path is None:
                distances.append((weight, math.inf))
            else:
                distances.append((weight, len(cheapest_path)-1))

        return distances, cheapest_paths_from_sender

    # review: after all, the `new_virtual_channel_delay` parameter is useless, because the situation is more complicated:
    # Donner: (hops+1)*BASE_DELAY
    # Elmo: (12*hops-12)*BASE_DELAY
    # LVPC: (8*hops-7)*BASE_DELAY
    def get_new_virtual_channel_time(self, hops):
        if self.method_name == "LVPC":
            return (8 * hops - 7) * self.base_delay
        elif self.method_name == "Elmo":
            return (12 * hops - 12) * self.base_delay
        else:
            return (hops + 1) * self.base_delay

    def get_new_virtual_channel_fee(self, path, coins_to_lock):
        """
        Returns the correct values for Elmo and Donner.
        And the correct values for LVPC for path of length 3.
        Fees for longer paths in LVPC are calculated recursively using this function.
        """
        return (self.base_fee + coins_to_lock * self.fee_rate) * (len(path) - 2)

    def get_new_channel_option(self, sender, receiver, value, knowledge_sender):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        future_payments, num_payments_sender, num_total_payments = knowledge_sender
        num_unknown_payments = num_total_payments - len(future_payments)
        num_unknown_payments_sender = (
            num_payments_sender - 
            len([payment for payment in future_payments if payment[0] == sender])
        )
        new_channel_time = self.plain_bitcoin.get_delay() + self.pay_delay
        new_channel_fee = self.plain_bitcoin.get_fee(self.opening_transaction_size)
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        sender_coins = min(
            self.plain_bitcoin.coins[sender] - value - new_channel_fee,
            (
                sum_future_payments + MULTIPLIER_CHANNEL_BALANCE * value
            )
        )
        if sender_coins < 0:
            return None
        self.network.add_channel(sender, sender_coins, receiver, value, None)
        new_channel_distance, cheapest_paths_from_sender = self.get_distances_and_paths_from_source(sender, future_payments)
        new_channel_centrality = self.network.get_centrality(sender, cheapest_paths_from_sender)
        self.network.close_channel(sender, receiver)
        return {
            'delay': new_channel_time,
            'fee': new_channel_fee,
            'centrality': new_channel_centrality,
            'distance': new_channel_distance,
            'payment_information': {
                'kind': self.open_channel_string,
                'data': (sender, receiver, value, sender_coins)
            }
        }

    def determine_sender_coins(self, value, path, desired_sender_coins, available_balances):
        """
        This method enables the sender to determine the amount of coins to put on a
        new virtual channel.
        """
        fee_for_value = self.get_new_virtual_channel_fee(path, value)
        # here we calculate how much balance remains after transferring value and a part of
        # the fee to the next intermediary
        # (this gives a lower bound on the remaining balances as fee_for_value is an upper bound on how
        # much of the fee has to be transferred to the next intermediary)
        # available_balances should be a np.array.
        remaining_balances = available_balances - value - fee_for_value
        # now we use the remaining balances to determine how much the sender can possibly put
        # on new virtual channel
        smallest_remaining_balance = min(remaining_balances)
        # we want to put exactly (if desired coins are more than remaining balance) so much on the new channel
        # such that sender_coins + fee_sender_coins = smallest_remaining_balance
        # where fee_sender_coins = fee_rate * sender_coins * (len(path) - 2)
        sender_coins = min(desired_sender_coins, smallest_remaining_balance / (1 + self.fee_rate * (len(path) - 2)))
        return sender_coins

    def get_new_virtual_channel_option(self, sender, receiver, value, knowledge_sender):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        future_payments, num_payments_sender, num_total_payments = knowledge_sender
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        # this is a simplification to calculate cheapest paths
        anticipated_lock_value = sum_future_payments + value
        if self.method_name == "Elmo" or self.method_name == "LVPC":
            cost_and_path = self.network.find_cheapest_path(
                sender, receiver, anticipated_lock_value, self.base_fee
            )
        elif self.method_name == "Donner":
            cost_and_path = self.network.find_cheapest_path(
                sender, receiver, anticipated_lock_value, self.base_fee,
                function="new_virtual_donner"
            )
        else:
            raise ValueError
            
        if cost_and_path is None:
            return None
        hops, path = cost_and_path
        # the factor is introduced so that lower channel doesn't end up with 0 balance.
        available_balances = np.array([
            self.network.graph[path[i]][path[i+1]]['balance'] / AVAILABILITY_FACTOR for i in range(len(path)-1)
        ])
        desired_virtual_coins = sum_future_payments + MULTIPLIER_CHANNEL_BALANCE * value
        sender_coins = self.determine_sender_coins(value, path, desired_virtual_coins, available_balances)
        if sender_coins < 0:
            return None
        payment_information = {'kind': self.open_virtual_channel_string, 'data': (path, value, sender_coins)}
        try:
            new_virtual_channel_fee = self.do(payment_information)
        except ValueError:
            return None
        new_virtual_channel_time = self.get_new_virtual_channel_time(hops)
        new_virtual_channel_distance, cheapest_paths_from_sender = self.get_distances_and_paths_from_source(sender, future_payments)
        new_virtual_channel_centrality = self.network.get_centrality(sender, cheapest_paths_from_sender)
        self.undo(payment_information)
        return {
            'delay': new_virtual_channel_time,
            'fee': new_virtual_channel_fee,
            'centrality': new_virtual_channel_centrality,
            'distance': new_virtual_channel_distance,
            'payment_information': payment_information
        }

    def get_pay_option(self, sender, receiver, value, knowledge_sender):
        future_payments, num_payments_sender, num_total_payments = knowledge_sender
        payment_information = {'kind': self.pay_string, 'data': (sender, receiver, value)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        distance_pay, cheapest_paths_from_sender = self.get_distances_and_paths_from_source(sender, future_payments)
        centrality_pay = self.network.get_centrality(sender, cheapest_paths_from_sender)
        self.undo(payment_information)
        return {
            'delay': self.pay_delay,
            'fee': 0,
            'centrality': centrality_pay,
            'distance': distance_pay,
            'payment_information': payment_information
        }

    def get_payment_options(self, sender, receiver, value, knowledge_sender):
        onchain_option = self.get_onchain_option(sender, receiver, value, knowledge_sender)
        new_channel_option = self.get_new_channel_option(sender, receiver, value, knowledge_sender)
        new_virtual_channel_option = self.get_new_virtual_channel_option(sender, receiver, value, knowledge_sender)
        pay_option = self.get_pay_option(sender, receiver, value, knowledge_sender)
        options = [onchain_option, new_channel_option, new_virtual_channel_option, pay_option]
        return [option for option in options if option is not None]

    def update_balances_new_virtual_channel(self, path, value, sender_coins, new_channel = False):
        # the new_channel argument tells whether this corresponds to making a payment
        # or undoing it.
        # all the "speaking names" like op_take, received, etc are in the case of a payment
        # in case of undoing they do the opposite.
        op_take, op_give = (operator.add, operator.sub) if new_channel else (operator.sub, operator.add)
        num_intermediaries = len(path) - 2
        sender = path[0]
        fee_intermediary = self.base_fee + self.fee_rate * (value + sender_coins)
        cost_sender = num_intermediaries * fee_intermediary
        if cost_sender > self.network.graph[sender][path[1]]['balance'] and new_channel == True:
            raise ValueError
        # update the balances of the intermediaries.
        for i in range(1, num_intermediaries + 1):
            received = (num_intermediaries - (i-1)) * fee_intermediary
            transfered = received - fee_intermediary
            new_taker_balance = op_take(self.network.graph[path[i]][path[i-1]]['balance'], received)
            new_giver_balance = op_give(self.network.graph[path[i]][path[i+1]]['balance'], transfered)
            # we test just for new_giver_balance < 0 as in case of new virtual channel only giver_balance gets smaller
            # In case of undoing it, there was a payment done before, so there shouldn't occur numbers < 0.
            if new_giver_balance < 0:
                for j in range(1, i):
                    received = (num_intermediaries - (j-1)) * fee_intermediary
                    transfered = received - fee_intermediary
                    new_taker_balance = op_give(self.network.graph[path[j]][path[j-1]]['balance'], received)
                    new_giver_balance = op_take(self.network.graph[path[j]][path[j+1]]['balance'], transfered)
                raise ValueError
            self.network.graph[path[i]][path[i-1]]['balance'] = new_taker_balance
            self.network.graph[path[i]][path[i+1]]['balance'] = new_giver_balance
        self.network.graph[sender][path[1]]['balance'] = op_give(self.network.graph[sender][path[1]]['balance'], cost_sender)


    def pay(self, sender, receiver, value):
        if self.network.graph.get_edge_data(sender, receiver) is None:
            raise ValueError
        elif self.network.graph[sender][receiver]['balance'] < value:
            raise ValueError
        self.network.graph[sender][receiver]['balance'] = self.network.graph[sender][receiver]['balance'] - value
        self.network.graph[receiver][sender]['balance'] = self.network.graph[receiver][sender]['balance'] + value

    def do(self, payment_information):
        if payment_information['kind'] == 'onchain':
            self.plain_bitcoin.pay(payment_information['data'])
        elif payment_information['kind'] == self.open_channel_string:
            sender, receiver, value, sender_coins = payment_information['data']
            self.network.add_channel(sender, sender_coins, receiver, value, None)
            # next update the coins of sender
            amount_sender = - (
                sender_coins + value +
                self.plain_bitcoin.get_fee(self.opening_transaction_size)
            )
            self.plain_bitcoin.update_coins(sender, amount_sender)
        elif payment_information['kind'] == self.open_virtual_channel_string:
            path, value, sender_coins = payment_information['data']
            sender = path[0]
            if self.open_virtual_channel_string == "LVPC-open-virtual-channel":
                new_virtual_channel_fee = 0
                for i in range(len(path)-2):
                    path_for_recursion = [sender] + path[i+1:i+3]
                    sender_coins_recursion = sender_coins / (MULTIPLIER_BALANCE_RECURSION_LVPC**i)
                    if i != len(path)-3:
                        sender_coins_recursion += value * (1 + self.fee_rate) + self.base_fee
                    receiver_coins_recursion = (
                        0 if i != len(path)-3 else value
                    )
                    receiver_recursion = path_for_recursion[-1]
                    new_virtual_channel_fee += self.get_new_virtual_channel_fee(
                        path_for_recursion, sender_coins_recursion + receiver_coins_recursion
                    )
                    # important that next line is at that position so that Error gets raised in case update is not possible
                    # before anything else is done.
                    self.update_balances_new_virtual_channel(
                        path_for_recursion, receiver_coins_recursion, sender_coins_recursion, new_channel=True
                    )
                    self.network.lock_unlock(
                        path_for_recursion, sender_coins_recursion + receiver_coins_recursion, lock=True
                    )
                    self.network.add_channel(
                        sender, sender_coins_recursion, receiver_recursion, receiver_coins_recursion, path_for_recursion
                    )
                return new_virtual_channel_fee
            else: # Donner or Elmo
                sender = path[0]
                receiver = path[-1]
                # important that next line is at that position so that Error gets raised in case update is not possible
                # before anything else is done.
                self.update_balances_new_virtual_channel(path, value, sender_coins, new_channel=True)
                self.network.lock_unlock(path, sender_coins + value, lock=True)
                self.network.add_channel(sender, sender_coins, receiver, value, path)
                new_virtual_channel_fee = self.get_new_virtual_channel_fee(path, value + sender_coins)
                return new_virtual_channel_fee
        elif payment_information['kind'] == self.pay_string:
            sender, receiver, value = payment_information['data']
            self.pay(sender, receiver, value)
        else:
            raise ValueError

    def undo(self, payment_information):
        if payment_information['kind'] == self.open_virtual_channel_string:
            path, value, sender_coins = payment_information['data']
            sender = path[0]
            if self.open_virtual_channel_string == "LVPC-open-virtual-channel":
                for i in range(len(path)-3, -1, -1):
                    path_for_recursion = [sender] + path[i+1:i+3]
                    receiver = path_for_recursion[-1]
                    amount_sender, amount_receiver = self.network.cooperative_close_channel(sender, receiver)
                    self.update_balances_new_virtual_channel(
                        path_for_recursion, amount_receiver, amount_sender, new_channel=False
                    )
            else:
                sender = path[0]
                receiver = path[-1]
                amount_sender, amount_receiver = self.network.cooperative_close_channel(sender, receiver)
                self.update_balances_new_virtual_channel(path, amount_receiver, amount_sender, new_channel=False)
        elif payment_information['kind'] == self.pay_string:
            sender, receiver, value = payment_information['data']
            if self.network.graph.get_edge_data(sender, receiver) is None:
                raise ValueError
            self.network.graph[sender][receiver]['balance'] += value
            self.network.graph[receiver][sender]['balance'] -= value
        else:
            raise ValueError

