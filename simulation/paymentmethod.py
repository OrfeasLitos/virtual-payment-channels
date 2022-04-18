from abc import ABC, abstractmethod
from pydoc import plain
from network import Network
import math

# units in millisatoshis
# default on-chain fees from https://bitcoinfees.net/ for an 1-input-2-output P2WPKH on 14/4/2022
# default max coins loosely copied from real world USD figures

# review: each class that inherits from PaymentMethod should be able to return a payment method, ready to be compared against others by Utility

class PlainBitcoin():
    # TODO: check for reasonable default values
    def __init__(self, max_coins = 2000000000000000, bitcoin_fee = 1000000, bitcoin_delay = 3600):
        self.max_coins = max_coins
        self.bitcoin_fee = bitcoin_fee
        self.bitcoin_delay = bitcoin_delay

    def get_unit_transaction_cost(self):
        return (self.bitcoin_fee, self.bitcoin_delay)

# LN fees from https://www.reddit.com/r/lightningnetwork/comments/tmn1kc/bmonthly_ln_fee_report/

# review: this class should return an off-chain payment method (if any is found) and an open-new-channel payment method
# review: bring back base_fee and add fee_rate. The per-hop fee is base_fee + fee_rate * payment_value
class LN(PlainBitcoin):
    def __init__(
        self, nr_players, plain_bitcoin, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600, ln_fee = 0.00002, ln_delay = 0.05,
        opening_transaction_size = 200, base_fee = 1000
    ):
        super().__init__(max_coins, bitcoin_fee, bitcoin_delay)
        self.ln_fee = ln_fee
        self.ln_delay = ln_delay
        self.opening_transaction_size = opening_transaction_size
        self.network = Network(nr_players)
        self.base_fee = base_fee
        self.plain_bitcoin = plain_bitcoin
        # use attribute to give flexibility with different fees and delays for Plainbitcoin

    def get_payment_time(self, path):
        return self.delay * len(path)

    def get_payment_fee(self, payment, path):
        # TODO: check if cost in reality depends on the payment or just on the path in the network
        # for PlainBitcoin it probably depends on the payment so I need the argument payment here.
        # review: the next comment is a good point. Let's add a test to ensure equality and if it is always equal, we can just use the fastest
        # cost actually should not depend on the path, but just on the length of the path, so we could use the cost_output of the method find cheapest path
        # which should actually be len(path) - 1
        # review:
        #   * the base_fee should be payed for each hop and the fee should be additionally multiplied with the payment value
        #   * no need to assign to `payment_fee`, just return directly
        payment_fee = self.fee * (len(path) - 1)
        return payment_fee

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
        # TODO: save calculated distances to parties in a list to prevent multiple calls to find_cheapest_path
        distances = []
        for sender, receiver, value in future_payments:
            cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
            if cost_and_path != None:
                cost, cheapest_path = cost_and_path
                distances.append(len(cheapest_path))
            else:
                distances.append(math.inf)
        return distances

    def get_payment_options(self, sender, receiver, value, future_payments):
        # atm assume for simplicity that future_payments are only payments the sender makes.
        # TODO: check if some of the stuff that happens here should be in separate functions.

        bitcoin_time = self.bitcoin_delay
        # is the fee fixed?
        # review: bitcoin fee depends on tx size. we should hardcode the sizes of the various txs of interest and use the simple tx (a.k.a. P2WP2KH) fee here
        bitcoin_fee = self.bitcoin_fee
        # if centrality or distance was already a attribute I could use this attribute straightaway as PlainBitcoin payment doesn't change the network.
        bitcoin_centrality = self.network.get_harmonic_centrality()
        bitcoin_distance = self.distance_to_future_parties(future_payments)
        bitcoin_option = (bitcoin_time, bitcoin_fee, bitcoin_centrality, bitcoin_distance)

        # review: consider trying out opening other channels as well, e.g. a channel with the party that appears most often (possibly weighted by coins) in our future
        new_channel_time = self.bitcoin_delay + self.ln_delay
        # is the fee for PlainBitcoin fixed? should there be the factor self.opening_transaction_size?
        new_channel_fee = self.bitcoin_fee * self.opening_transaction_size
        min_amount = self.sum_future_payments_to_receiver(receiver, future_payments)
        self.network.add_channel(sender, min_amount, receiver, 0)
        new_channel_centrality = self.network.get_harmonic_centrality()
        new_channel_distance = self.distance_to_future_parties(future_payments)
        self.network.close_channel(sender, receiver)
        new_channel_option = (new_channel_time, new_channel_fee, new_channel_centrality, new_channel_distance)

        # TODO: check if there's a better method to say that there is no path than to return None as offchain_option
        offchain_option = None
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
        if offchain_cost_and_path != None:
            offchain_cost, offchain_path = offchain_cost_and_path
            offchain_time = self.get_payment_time(offchain_path)
            payment = (sender, receiver, value)
            offchain_fee = self.get_payment_fee(payment, offchain_path)
            # In LN an off-chain payment doesn't change the network, same for PlainBitcoin, so centrality and distance are equal.
            # review: the above shouldn't be right: depleting my channels should reduce my centrality and increase my distance
            # review: also here centrality & distance are calculated after payment is complete, whereas in the "new channel" case the off-chain payment isn't carried out before calculating the metrics.
            offchain_centrality = bitcoin_centrality
            offchain_distance = bitcoin_distance
            offchain_option = (offchain_time, offchain_fee, offchain_centrality, offchain_distance, offchain_cost, offchain_path)
        
        return [bitcoin_option, new_channel_option, offchain_option]
