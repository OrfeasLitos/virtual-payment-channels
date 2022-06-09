import math
import numpy as np
import operator
from network import Network

# units in millisatoshis
# default on-chain fees from https://bitcoinfees.net/ for an 1-input-2-output P2WPKH on 14/4/2022
# default max coins loosely copied from real world USD figures

MULTIPLIER_CHANNEL_BALANCE_LN = 20

class PlainBitcoin():
    # the total fee is num_vbytes * price_per_vbyte
    # price per vbyte currently at about 1 satoshi
    def __init__(self, nr_players, max_coins = 2000000000000000, bitcoin_fee = 1000,
                bitcoin_delay = 3600):
        self.max_coins = max_coins
        self.bitcoin_fee = bitcoin_fee
        self.bitcoin_delay = bitcoin_delay
        # TODO: different amount for different parties
        self.coins = {i: max_coins for i in range(nr_players)}

    def get_unit_transaction_cost(self):
        return (self.bitcoin_fee, self.bitcoin_delay)

    # tx_size for 1-input-2-output P2WPKH
    def get_fee(self, tx_size = 140.5):
        return self.bitcoin_fee * tx_size

    def get_delay(self):
        return self.bitcoin_delay

    def update_coins(self, party, amount):
        if self.coins[party] + amount < 0:
            raise ValueError
        self.coins[party] += amount

    def pay(self, data):
        sender, receiver, value = data
        amount_sender = - value - self.get_fee()
        self.update_coins(sender, amount_sender)
        # only the first update_coins can fail, no bookkeeping is required.
        self.update_coins(receiver, value)
            

# LN fees from https://www.reddit.com/r/lightningnetwork/comments/tmn1kc/bmonthly_ln_fee_report/

class LN(PlainBitcoin):
    def __init__(
        self, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600, ln_fee = 0.00002, ln_delay = 0.05,
        opening_transaction_size = 200, base_fee = 1000
    ):
        self.ln_fee = ln_fee
        self.ln_delay = ln_delay
        self.opening_transaction_size = opening_transaction_size
        self.network = Network(nr_players)
        self.base_fee = base_fee
        self.plain_bitcoin = PlainBitcoin(nr_players, max_coins, bitcoin_fee, bitcoin_delay)

    def get_payment_time(self, path):
        return self.ln_delay * len(path)

    def get_payment_fee(self, payment, num_hops):
        sender, receiver, value = payment
        return (self.base_fee +  value * self.ln_fee) * num_hops

    def sum_future_payments_to_counterparty(self, sender, counterparty, future_payments):
        """
        This is used to determine a minimum amount that should be put on a new channel between sender and receiver.
        """
        future_payments_to_receiver = [
            future_payment for future_payment in future_payments if future_payment[0] == sender
            and future_payment[1] == counterparty
        ]
        return sum([payment[2] for payment in future_payments_to_receiver])

    def get_distances(self, source, future_payments):
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
        path_data = []
        for future_sender, future_receiver, value in future_payments:
            encountered_parties.add(future_sender)
            encountered_parties.add(future_receiver)
            if future_sender != source:
                # TODO: think about discarding first part of the tuple.
                path_data.append((
                    future_sender,
                    weight_endpoint if future_receiver == source else weight_intermediary,
                    self.network.find_cheapest_path(future_sender, source, value)
                ))
            if future_receiver != source:
                path_data.append((
                    future_receiver,
                    weight_endpoint if future_sender == source else weight_intermediary,
                    self.network.find_cheapest_path(source, future_receiver, value)
                ))

        # taken from here: https://coingate.com/blog/post/lightning-network-bitcoin-stats-progress
        # is quite old source. # TODO: look for newer source.
        dummy_amount = 500000000
        for party in (set(self.network.graph.nodes()).difference(encountered_parties)):
            path_data.append((
                party,
                weight_other,
                self.network.find_cheapest_path(source, party, dummy_amount)
            ))
        
        for counterparty, weight, cost_and_path in path_data:
            if cost_and_path is None:
                distances.append((weight, math.inf))
            else:
                _, cheapest_path = cost_and_path
                distances.append((weight, len(cheapest_path)-1))

        return distances

    def update_balances(self, value, ln_fee, base_fee, path, pay = False):
        # the pay argument tells whether this corresponds to making a payment
        # or undoing it.
        # all the "speaking names" like op_take, received, etc are in the case of a payment
        # in case of undoing they do the opposite.
        op_take, op_give = (operator.add, operator.sub) if pay else (operator.sub, operator.add)
        num_intermediaries = len(path) - 2
        sender = path[0]
        receiver = path[-1]
        # review: we could also get `fee_intermediary` directly as input, to reduce parameters
        fee_intermediary = ln_fee * value + base_fee
        cost_sender = value + num_intermediaries * fee_intermediary
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

    def get_onchain_option(self, sender, receiver, value, future_payments):
        onchain_time = self.plain_bitcoin.get_delay()
        onchain_fee = self.plain_bitcoin.get_fee()
        if onchain_fee + value > self.plain_bitcoin.coins[sender]:
            return None
        onchain_centrality = self.network.get_harmonic_centrality()
        onchain_distance = self.get_distances(sender, future_payments)
        return {
            'delay': onchain_time,
            'fee': onchain_fee,
            'centrality': onchain_centrality,
            'distance': onchain_distance,
            'payment_information': { 'kind': 'onchain', 'data': (sender, receiver, value) }
        }

    def get_new_channel_option(self, sender, receiver, value, future_payments, counterparty):
        new_channel_time = self.plain_bitcoin.get_delay() + self.ln_delay
        new_channel_fee = self.plain_bitcoin.get_fee(self.opening_transaction_size)
        sum_future_payments = self.sum_future_payments_to_counterparty(sender, counterparty, future_payments)
        sender_coins = min(
            self.plain_bitcoin.coins[sender] - value - new_channel_fee,
            MULTIPLIER_CHANNEL_BALANCE_LN * sum_future_payments
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
            new_channel_centrality = self.network.get_harmonic_centrality()
            new_channel_distance = self.get_distances(sender, future_payments)
        self.network.close_channel(sender, counterparty)

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

    def get_offchain_option(self, sender, receiver, value, future_payments):
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
        if offchain_cost_and_path is None:
            return None
        offchain_hops, offchain_path = offchain_cost_and_path
        offchain_time = self.get_payment_time(offchain_path)
        payment = (sender, receiver, value)
        payment_information = {'kind': 'ln-pay', 'data': (offchain_path, value)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        offchain_fee = self.get_payment_fee(payment, offchain_hops)
        offchain_centrality = self.network.get_harmonic_centrality()
        offchain_distance = self.get_distances(sender, future_payments)
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
        # review: consider trying out opening other channels as well, e.g. a channel with the party that appears most often (possibly weighted by coins) in our future
        # TODO: make a loop that gives us several possible new channels with different counterparties
        counterparty = receiver
        new_channel_option = self.get_new_channel_option(sender, receiver, value, future_payments, counterparty)
        offchain_option = self.get_offchain_option(sender, receiver, value, future_payments)
        options = [onchain_option, new_channel_option, offchain_option]
        return [option for option in options if option is not None]

    def do(self, payment_information):
        match payment_information['kind']:
            case 'onchain':
                self.plain_bitcoin.pay(payment_information['data'])
            case 'ln-open':
                # review: lint
                (sender, receiver, value, counterparty, sender_coins, new_channel_offchain_option) = (
                    payment_information['data']
                )
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
            case 'ln-pay':
                offchain_path, value = payment_information['data']
                self.update_balances(value, self.ln_fee, self.base_fee, offchain_path, pay = True)
            case _:
                raise ValueError

    def undo(self, payment_information):
        match payment_information['kind']:
            case 'ln-pay':
                offchain_path, value = payment_information['data']
                self.update_balances(value, self.ln_fee, self.base_fee, offchain_path, pay = False)
            case _:
                raise ValueError
