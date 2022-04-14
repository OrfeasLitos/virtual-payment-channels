from abc import ABC, abstractmethod
from network import Network

# review: each class that inherits from PaymentMethod should be able to return a payment method, ready to be compared against others by Utility

class PlainBitcoin():
    # TODO: check for reasonable default values
    def __init__(self, MAX_COINS = 1000000, bitcoin_fee = 1, bitcoin_delay = 3600):
        self.MAX_COINS = MAX_COINS
        self.bitcoin_fee = bitcoin_fee
        self.bitcoin_delay = bitcoin_delay

    def get_unit_transaction_cost(self):
        return (self.bitcoin_fee, self.bitcoin_delay)


# review: this class should return an off-chain payment method (if any is found) and an open-new-channel payment method
class LN(PlainBitcoin):
    # TODO: look up reasonable default values
    def __init__(self, nr_players, MAX_COINS = 1000000, bitcoin_fee = 1, bitcoin_delay = 3600, LN_fee = 0.001, LN_delay = 0.05, opening_transaction_size = 1):
        super().__init__(MAX_COINS, bitcoin_fee, bitcoin_delay)
        self.LN = LN_fee
        self.LN_delay = LN_delay
        self.opening_transaction_size = opening_transaction_size
        self.network = Network(nr_players)
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

    def get_payment_options(self, sender, receiver, value, future_payments):
        # atm assume for simplicity that future_payments are only payments the sender makes.
        # TODO: check if some of the stuff that happens here should be in separate functions.

        bitcoin_time = self.bitcoin_delay
        # is the fee fixed?
        bitcoin_fee = self.bitcoin_fee
        # if centrality or distance was already a attribute I could use this attribute straightaway as PlainBitcoin payment doesn't change the network.
        bitcoin_centrality = self.network.get_harmonic_centrality()
        # bitcoin_distance = 
        bitcoin_option = (bitcoin_time, bitcoin_fee, bitcoin_centrality, bitcoin_distance)

        new_channel_time = self.bitcoin_delay + self.LN_delay
        # is the fee for PlainBitcoin fixed? should there be the factor self.opening_transaction_size?
        new_channel_fee = self.bitcoin_fee * self.opening_transaction_size
        # new_channel_centrality = 
        # new_channel_distance = 
        new_channel_option = (new_channel_time, new_channel_fee, new_channel_centrality, new_channel_distance)

        # TODO: check if there's a better method to say that there is no path than to return None as offchain_option
        offchain_option = None
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
        if offchain_cost_and_path != None:
            offchain_cost, offchain_path = offchain_cost_and_path
            offchain_time = self.get_payment_time(offchain_path)
            payment = (sender, receiver, value)
            offchain_fee = self.get_payment_fee(payment, offchain_path)
            #offchain_centrality = 
            #offchain_distance = 
            offchain_option = (offchain_time, offchain_fee, offchain_centrality, offchain_distance, offchain_cost, offchain_path)
        
        return (bitcoin_option, new_channel_option, offchain_option)