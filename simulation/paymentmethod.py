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
        self.coins = dict([(i, max_coins) for i in range(nr_players)])

    def get_unit_transaction_cost(self):
        return (self.bitcoin_fee, self.bitcoin_delay)
    
    def get_fee(self):
        return self.bitcoin_fee
    
    def get_delay(self):
        return self.bitcoin_delay

    def pay(self, data):
        sender, receiver, value = data
        # should self.get_fee() also be multiplied with value
        self.coins[sender] -= (value + self.get_fee())
        self.coins[receiver] += value
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
                cost, cheapest_path = cost_and_path
                distances.append(len(cheapest_path)-1)
            else:
                distances.append(math.inf)
        return distances

    def get_payment_options(self, sender, receiver, value, future_payments):
        # atm assume for simplicity that future_payments are only payments the sender makes.
        # TODO: check if some of the stuff that happens here should be in separate functions.

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
            'payment_information': { 'kind': 'ln-open', 'data': (sender, receiver, value, counterparty, sender_coins, counterparty_coins) }
        }

        # TODO: check if there's a better method to say that there is no path than to return None as offchain_option
        offchain_option = None
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
        if offchain_cost_and_path != None:
            offchain_hops, offchain_path = offchain_cost_and_path
            offchain_time = self.get_payment_time(offchain_path)
            payment = (sender, receiver, value)
            offchain_fee = self.get_payment_fee(payment, offchain_hops)
            # In LN an off-chain payment doesn't change the network, same for PlainBitcoin, so centrality and distance are equal.
            # review: the above shouldn't be right: depleting my channels should reduce my centrality and increase my distance
            # True, TODO: change the way this is handled here.
            # TODO: change the balance on the edges, calculate distance and centrality and reset the balance to the previous value.
            # review: also here centrality & distance are calculated after payment is complete, whereas in the "new channel" case the off-chain payment isn't carried out before calculating the metrics.
            offchain_centrality = bitcoin_centrality
            offchain_distance = bitcoin_distance
            offchain_option = {
                'delay': offchain_time,
                'fee': offchain_fee,
                'centrality': offchain_centrality,
                'distance': offchain_distance,
                'payment_information': {'kind': 'ln-pay', 'data': (sender, receiver, value, offchain_hops, offchain_path)}
            }

        return [bitcoin_option, new_channel_option, offchain_option]

    def do(self, payment_information):
        match payment_information['kind']:
            case 'onchain':
                data = payment_information['data']
                self.plain_bitcoin.pay(data)
            case 'ln-open':
                pass # TODO
            case 'ln-pay':
                pass # TODO
            case _:
                raise ValueError

        if method_num == 1:
            # TODO: think about a reasonable balance that should be put on the new channel. For the sender it should be >= value
            # actually it should probably depend on the future payments, i.e. knowledge, but still some useful heuristic would be good if not all payments are known.
            self.network.add_channel(sender, value, receiver, 0)
            # TODO: make a function that updates the balance of a party (hereby I mean the balance that is not on a channel, so just the Bitcoins in a Wallet)
            # TODO: make a function that does the transaction and updates the balance on the channel (or both updates in one)
            # probably add_channel should automatically update the balance of the wallets when they are transfered to the channel.
            # then only the balance on the channel has to be updated.
            self.network.update_balance(sender, amount_sender, receiver, amount_receiver, intermediaries, amount_intermediaries)
            # TODO: keep actually track of the balance of a party in his wallet.
        else:
            # TODO: make two more cases (with elif else)
            self.network.update_balance(sender, amount_sender, receiver, amount_receiver, intermediaries, amount_intermediaries)
