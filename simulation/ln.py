import math
import numpy as np
import operator
from paymentmethod import (
    Payment_Network, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE,
    DUMMY_PAYMENT_VALUE
)
from network import Network


# LN fees from https://www.reddit.com/r/lightningnetwork/comments/tmn1kc/bmonthly_ln_fee_report/

class LN(Payment_Network):
    def __init__(
        self, nr_players, bitcoin_fee = 1000000, bitcoin_delay = 3600, ln_fee = 0.00002,
        opening_transaction_size = 121.5, base_fee = 1000, coins_for_parties = "max_value"
    ):
        super().__init__(nr_players, bitcoin_fee, bitcoin_delay, coins_for_parties)
        self.method_name = "ln"
        self.ln_fee = ln_fee
        self.ln_delay = self.base_delay
        self.opening_transaction_size = opening_transaction_size
        self.network = Network(nr_players)
        self.base_fee = base_fee

    def get_payment_time(self, path):
        return self.ln_delay * len(path)

    def get_payment_fee(self, payment, num_hops):
        sender, receiver, value = payment
        return (self.base_fee +  value * self.ln_fee) * num_hops

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
        fee_intermediary = self.ln_fee * DUMMY_PAYMENT_VALUE + self.base_fee
        cheapest_paths_from_sender = self.network.find_cheapest_paths_from_sender(
            source, DUMMY_PAYMENT_VALUE, fee_intermediary
        )
        path_data = []
        for future_sender, future_receiver, value in future_payments:
            fee_intermediary = self.ln_fee * value + self.base_fee
            encountered_parties.add(future_sender)
            encountered_parties.add(future_receiver)
            if future_sender != source:
                path_data.append((
                    weight_endpoint if future_receiver == source else weight_intermediary,
                    self.network.find_cheapest_path(future_sender, source, value, fee_intermediary)
                ))
            if future_receiver != source:
                path_data.append((
                    weight_endpoint if future_sender == source else weight_intermediary,
                    cheapest_paths_from_sender.get(future_receiver)
                ))
        
        fee_intermediary = self.ln_fee * DUMMY_PAYMENT_VALUE + self.base_fee
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

    def update_balances(self, value, ln_fee, base_fee, path, pay = False):
        # the pay argument tells whether this corresponds to making a payment
        # or undoing it.
        # all the "speaking names" like op_take, received, etc are in the case of a payment
        # in case of undoing they do the opposite.
        op_take, op_give = (operator.add, operator.sub) if pay else (operator.sub, operator.add)
        num_intermediaries = len(path) - 2
        sender = path[0]
        receiver = path[-1]
        fee_intermediary = ln_fee * value + base_fee
        cost_sender = value + num_intermediaries * fee_intermediary
        if pay == True and cost_sender > self.network.graph[sender][path[1]]['balance']:
            raise ValueError
        # update the balances of the intermediaries.
        for i in range(1, num_intermediaries + 1):
            received = value + (num_intermediaries - (i-1)) * fee_intermediary
            transfered = received - fee_intermediary
            new_taker_balance = op_take(self.network.graph[path[i]][path[i-1]]['balance'], received)
            new_giver_balance = op_give(self.network.graph[path[i]][path[i+1]]['balance'], transfered)
            # we test just for new_giver_balance < 0 as in case of the payment only giver_balance gets smaller
            # In case of undoing it, there was a payment done before, so there shouldn't occur numbers < 0.
            if new_giver_balance < 0:
                for j in range(1, i):
                    received = value + (num_intermediaries - (j-1)) * fee_intermediary
                    transfered = received - fee_intermediary
                    new_taker_balance = op_give(self.network.graph[path[j]][path[j-1]]['balance'], received)
                    new_giver_balance = op_take(self.network.graph[path[j]][path[j+1]]['balance'], transfered)
                raise ValueError
            self.network.graph[path[i]][path[i-1]]['balance'] = new_taker_balance
            self.network.graph[path[i]][path[i+1]]['balance'] = new_giver_balance
        self.network.graph[sender][path[1]]['balance'] = op_give(self.network.graph[sender][path[1]]['balance'], cost_sender)
        self.network.graph[receiver][path[-2]]['balance'] = op_take(self.network.graph[receiver][path[-2]]['balance'], value)

    def get_new_channel_option(self, sender, receiver, value, knowledge_sender, counterparty):
        # case channel already exists.
        if self.network.graph.get_edge_data(sender, counterparty) is not None:
            return None
        future_payments, num_payments_sender, num_total_payments = knowledge_sender
        new_channel_time = self.plain_bitcoin.get_delay() + self.ln_delay
        new_channel_fee = self.plain_bitcoin.get_fee(self.opening_transaction_size)
        sum_future_payments = sum_future_payments_to_counterparty(sender, counterparty, future_payments)
        sender_coins = min(
            self.plain_bitcoin.coins[sender] - value - new_channel_fee,
            sum_future_payments + MULTIPLIER_CHANNEL_BALANCE * value
        )
        if sender_coins < 0:
            return None
        if counterparty != receiver:
            self.network.add_channel(sender, sender_coins, counterparty, 0)
            new_channel_offchain_option = self.get_offchain_option(
                sender, receiver, value, future_payments
            )
            new_channel_centrality = new_channel_offchain_option['centrality']
            new_channel_distance = new_channel_offchain_option['distance']
            new_channel_time = new_channel_time + new_channel_offchain_option['delay']
            new_channel_fee = new_channel_fee + new_channel_offchain_option['fee']
        else:
            self.network.add_channel(sender, sender_coins, counterparty, value)
            new_channel_offchain_option = None
            new_channel_distance, cheapest_paths_from_sender = (
                self.get_distances_and_paths_from_source(sender, future_payments)
            )
            new_channel_centrality = self.network.get_centrality(
                sender, cheapest_paths_from_sender
            )
        self.network.remove_channel(sender, counterparty)

        return {
            'delay': new_channel_time,
            'fee': new_channel_fee,
            'centrality': new_channel_centrality,
            'distance': new_channel_distance,
            'payment_information': {
                'kind': 'ln-open',
                'data': (
                    sender, receiver, value, counterparty,
                    sender_coins, new_channel_offchain_option
                )
            }
        }

    def get_offchain_option(self, sender, receiver, value, knowledge_sender):
        fee_intermediary = fee_intermediary = self.ln_fee * value + self.base_fee
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value, fee_intermediary)
        if offchain_cost_and_path is None:
            return None
        future_payments, num_payments_sender, num_total_payments = knowledge_sender
        offchain_hops, offchain_path = offchain_cost_and_path
        offchain_time = self.get_payment_time(offchain_path)
        payment = (sender, receiver, value)
        payment_information = {'kind': 'ln-pay', 'data': (offchain_path, value)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        offchain_fee = self.get_payment_fee(payment, offchain_hops)
        offchain_distance, cheapest_paths_from_sender = (
            self.get_distances_and_paths_from_source(sender, future_payments)
        )
        offchain_centrality = self.network.get_centrality(sender, cheapest_paths_from_sender)
        self.undo(payment_information)
        return {
            'delay': offchain_time,
            'fee': offchain_fee,
            'centrality': offchain_centrality,
            'distance': offchain_distance,
            'payment_information': payment_information
        }

    def get_payment_options(self, sender, receiver, value, future_payments):
        onchain_option = self.get_onchain_option(sender, receiver, value, future_payments)
        counterparty = receiver
        new_channel_option = self.get_new_channel_option(sender, receiver, value, future_payments, counterparty)
        offchain_option = self.get_offchain_option(sender, receiver, value, future_payments)
        options = [onchain_option, new_channel_option, offchain_option]
        return [option for option in options if option is not None]

    def do(self, payment_information):
        if payment_information['kind'] == 'onchain':
            self.plain_bitcoin.pay(payment_information['data'])
        elif payment_information['kind'] == 'ln-open':
            (
                sender, receiver, value, counterparty, sender_coins,
                new_channel_offchain_option
            ) = payment_information['data']
            counterparty_coins = value if counterparty == receiver else 0
            self.network.add_channel(sender, sender_coins, counterparty, counterparty_coins)
            # next update the coins of sender
            amount_sender = - (
                sender_coins + counterparty_coins +
                self.plain_bitcoin.get_fee(self.opening_transaction_size)
            )
            self.plain_bitcoin.update_coins(sender, amount_sender)
            # use ln-pay here to make the off-chain payment after opening a new channel.
            if counterparty != receiver:
                self.do(new_channel_offchain_option['payment_information'])
        elif payment_information['kind'] == 'ln-pay':
            offchain_path, value = payment_information['data']
            self.update_balances(value, self.ln_fee, self.base_fee, offchain_path, pay = True)
        else:
            raise ValueError

    def undo(self, payment_information):
        if payment_information['kind'] == 'ln-pay':
            offchain_path, value = payment_information['data']
            self.update_balances(value, self.ln_fee, self.base_fee, offchain_path, pay = False)
        else:
            raise ValueError

    def equal_channels(self, other):
        if self.network.graph.nodes() != other.network.graph.nodes():
            return False
        # assuming that other network is also built as expected,
        # i.e in dict exists 'balance' key.
        for channel in self.network.graph.edges.data("balance"):
            sender, receiver, balance = channel
            if other.network.graph.get_edge_data(sender, receiver) == None:
                return False
            elif not np.isclose(
                    balance,
                    other.network.graph[sender][receiver]['balance']
            ):
                return False

        for channel in other.network.graph.edges.data("balance"):
            sender, receiver, balance = channel
            if self.network.graph.get_edge_data(sender, receiver) == None:
                return False
            elif not np.isclose(
                balance,
                self.network.graph[sender][receiver]['balance']
            ):
                return False

        return True

    def __eq__(self, other):
        return (
            self.ln_fee == other.ln_fee and
            self.ln_delay == other.ln_delay and
            self.opening_transaction_size == other.opening_transaction_size and
            self.equal_channels(other) and
            self.base_fee == other.base_fee and
            self.plain_bitcoin == other.plain_bitcoin
        )
