from abc import ABC, abstractmethod
from network import Network
import math
import networkx as nx

# units in millisatoshis
# default on-chain fees from https://bitcoinfees.net/ for an 1-input-2-output P2WPKH on 14/4/2022
# default max coins loosely copied from real world USD figures

# review: each class that inherits from PaymentMethod should be able to return a payment method, ready to be compared against others by Utility

class PlainBitcoin():
    # TODO: check for reasonable default values
    def __init__(self, nr_players, max_coins = 2000000000000000, bitcoin_fee = 1000000, bitcoin_delay = 3600):
        self.max_coins = max_coins
        self.bitcoin_fee = bitcoin_fee
        self.bitcoin_delay = bitcoin_delay
        # TODO: different amount for different parties
        self.coins = {i: max_coins for i in range(nr_players)}

    def get_unit_transaction_cost(self):
        return (self.bitcoin_fee, self.bitcoin_delay)
    
    def get_fee(self):
        return self.bitcoin_fee
    
    def get_delay(self):
        return self.bitcoin_delay

    def pay(self, data):
        sender, receiver, value = data
        # should self.get_fee() also be multiplied with value
        if self.coins[sender] - value + self.get_fee() < 0:
            raise ValueError
        self.coins[sender] -= value + self.get_fee()
        self.coins[receiver] += value
        return

    def update_coins(self, party, amount):
        if self.coins[party] + amount < 0:
            raise ValueError
        self.coins[party] += amount
        return

# LN fees from https://www.reddit.com/r/lightningnetwork/comments/tmn1kc/bmonthly_ln_fee_report/

# review: this class should return an off-chain payment method (if any is found) and an open-new-channel payment method
# review: bring back base_fee and add fee_rate. The per-hop fee is base_fee + fee_rate * payment_value
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

    def sum_future_payments_to_receiver(self, receiver, future_payments):
        """
        This method is used to determine a minimum amount that should be put on a new channel between sender and receiver.
        """
        future_payments_to_receiver = [future_payment for future_payment in future_payments if future_payment[1] == receiver]
        return sum([payment[2] for payment in future_payments_to_receiver])

    def distance_to_future_parties(self, future_payments):
        """
        Returns the sum of the distances of the future parties (if parties occur multiple times their distance is summed multiple times)
        """
        # review: this doesn't calculate _our_ distance from others but _future payers'_ distances from others
        # Yes therefore I made the first comment in get_payment_options. I still have to implement a filter method, so that we don't need the assumption there.
        # review: instead of filtering them out, we could exploit the data on payments that don't include us by e.g.
        # review: wanting to have a shorter distance to those parties as well
        # review: (and give our distance to them bonus weight if we project the unrelated payment to go through us)
        # TODO: save calculated distances to parties in a list to prevent multiple calls to find_cheapest_path
        # review: in orfer to combine the distances of various future payments, we may need to also store sender/receiver info in the list
        distances = []
        for sender, receiver, value in future_payments:
            cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
            if cost_and_path != None:
                _, cheapest_path = cost_and_path
                distances.append(len(cheapest_path)-1)
            else:
                distances.append(math.inf)
        return distances
    
    def update_balances(self, value, fee_intermediary, base_fee, path):
        num_intermediaries = len(path) - 2
        sender = path[0]
        receiver = path[-1]
        # review: I think `sender, receiver` should be `sender, path[1]` x2
        # review: also I suspect that the `[sender, receiver]` syntax is wrong.
        # review: If `num_hops == len(path)`, then the `fee_intermediary` should be paid only `num_hops - 1` times,
        # review: as many as the intermediaries
        if self.network.graph[sender, receiver]['balance'] - value + num_intermediaries * fee_intermediary + base_fee < 0:
            raise ValueError
        self.network.graph[sender, receiver]['balance'] -= value + num_intermediaries * fee_intermediary + base_fee
        # review: I think `receiver, sender` should be `path[-2], receiver`
        self.network.graph[receiver, sender]['balance'] += value
        # Now have to update the balances of the intermediaries.
        for i in range(num_intermediaries):
        # review: I suspect that the `[path[i+1]][path[i]]` syntax is wrong
            self.network.graph[path[i+1]][path[i]]['balance'] += fee_intermediary
        return

    # This method is defined because we need the offchain option several times in get_payment_options.
    # For every new_channel and if we do everything off-chain.
    def get_offchain_option(self, sender, receiver, value, future_payments):
        # TODO: check if there's a better method to say that there is no path than to return None as offchain_option
        offchain_option = None
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
        if offchain_cost_and_path != None:
            offchain_hops, offchain_path = offchain_cost_and_path
            offchain_time = self.get_payment_time(offchain_path)
            payment = (sender, receiver, value)
            offchain_fee = self.get_payment_fee(payment, offchain_hops)
            offchain_centrality = self.network.get_harmonic_centrality()
            offchain_distance = self.distance_to_future_parties(future_payments)
            offchain_option = {
                'delay': offchain_time,
                'fee': offchain_fee,
                'centrality': offchain_centrality,
                'distance': offchain_distance,
                'payment_information': {'kind': 'ln-pay', 'data': (offchain_path, value)}
            }

        return offchain_option

    def get_payment_options(self, sender, receiver, value, future_payments):
        # atm assume for simplicity that future_payments are only payments the sender makes.
        # TODO: check if some of the stuff that happens here should be in separate functions.
        # review: I like that the offchain option is a function, let's make on-chain and ln-open into separate functions as well

        bitcoin_time = self.plain_bitcoin.get_delay()
        # is the fee fixed?
        # review: bitcoin fee depends on tx size. we should hardcode the sizes of the various txs of interest and use the simple tx (a.k.a. P2WP2KH) fee here
        bitcoin_fee = self.plain_bitcoin.get_fee()
        # if centrality or distance was already a attribute I could use this attribute straightaway as PlainBitcoin payment doesn't change the network.
        bitcoin_centrality = self.network.get_harmonic_centrality()
        bitcoin_distance = self.distance_to_future_parties(future_payments)
        bitcoin_option = {
            'delay': bitcoin_time,
            'fee': bitcoin_fee,
            'centrality': bitcoin_centrality,
            'distance': bitcoin_distance,
            'payment_information': { 'kind': 'onchain', 'data': (sender, receiver, value) }
        }

        # review: consider trying out opening other channels as well, e.g. a channel with the party that appears most often (possibly weighted by coins) in our future
        # maybe make methods for new_channel time and fee as well
        new_channel_time = self.plain_bitcoin.get_delay() + self.ln_delay
        new_channel_fee = self.plain_bitcoin.get_fee() * self.opening_transaction_size
        min_amount = self.sum_future_payments_to_receiver(receiver, future_payments)
        # receiver doesn't need same minimum amount, what should he put on channel?
        # review: give receiver the current payment value (corresponds to `push_msat` of LN).
        # review: our initial coins should be slightly higher than the minimum needed,
        # review: in order to accommodate for future payments and act as intermediary.
        # review: we can say e.g. `min(our on-chain coins, 2 * (min_amount - value))` and we can improve from there
        self.network.add_channel(sender, min_amount, receiver, min_amount)
        new_channel_centrality = self.network.get_harmonic_centrality()
        new_channel_distance = self.distance_to_future_parties(future_payments)
        # TODO: adjust future_payments.
        new_channel_offchain_option = self.get_offchain_option(sender, receiver, value, future_payments[1:])
        self.network.close_channel(sender, receiver)
        # TODO: make a loop that gives us several possible new channels with different counterparties
        counterparty = receiver
        sender_coins = 2 * (min_amount - value)
        counterparty_coins = 2 * (min_amount - value)
        new_channel_option = {
            'delay': new_channel_time,
            'fee': new_channel_fee,
            'centrality': new_channel_centrality,
            'distance': new_channel_distance,
            'payment_information': { 'kind': 'ln-open', 'data': (sender, receiver, value, counterparty, sender_coins, counterparty_coins, new_channel_offchain_option) }
        }

        # TODO: check if there's a better method to say that there is no path than to return None as offchain_option
        offchain_option = self.get_offchain_option(sender, receiver, value, future_payments)

        return [bitcoin_option, new_channel_option, offchain_option]

    def do(self, payment_information):
        # Should do return sth?
        match payment_information['kind']:
            case 'onchain':
                data = payment_information['data']
                self.plain_bitcoin.pay(data)
            case 'ln-open':
                data = payment_information['data']
                sender, receiver, value, counterparty, sender_coins, counterparty_coins, new_channel_offchain_option = data
                self.network.add_channel(sender, sender_coins, counterparty, counterparty_coins)
                # next update the coins of sender and counterparty
                amount_sender = - (value + self.plain_bitcoin.get_fee())
                self.plain_bitcoin.update_coins(sender, amount_sender)
                amount_counterparty = - counterparty_coins
                self.plain_bitcoin.update_coins(counterparty, amount_counterparty)
                # use ln-pay here to make the off-chain payment after opening a new channel.
                self.do(self, new_channel_offchain_option['payment_information'])
            case 'ln-pay':
                offchain_path, value = payment_information['data']
                self.update_balances(value, self.ln_fee, self.base_fee, offchain_path)
            case _:
                raise ValueError
