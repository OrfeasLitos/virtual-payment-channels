import random
from abc import ABC, abstractmethod

# units in millisatoshis
# default on-chain fees from https://bitcoinfees.net/ for an 1-input-2-output P2WPKH on 14/4/2022
# default max coins loosely copied from real world USD figures

MAX_COINS = 2000000000000000
MULTIPLIER_CHANNEL_BALANCE = 40
# DUMMY_PAYMENT_VALUE taken from here: https://coingate.com/blog/post/lightning-network-bitcoin-stats-progress
DUMMY_PAYMENT_VALUE = 500000000
BASE_DELAY = 0.05

def sum_future_payments_to_counterparty(sender, counterparty, future_payments):
    """
    This is used to determine a minimum amount that should be put on a new channel between sender and receiver.
    """
    future_payments_to_receiver = [
        future_payment for future_payment in future_payments if future_payment[0] == sender
        and future_payment[1] == counterparty
    ]
    return sum([payment[2] for payment in future_payments_to_receiver])


class PlainBitcoin():
    # the total fee is num_vbytes * price_per_vbyte
    # price per vbyte currently at about 1 satoshi
    def __init__(self, nr_players, bitcoin_fee = 1000,
                bitcoin_delay = 3600, coins_for_parties = "random"):
        self.bitcoin_fee = bitcoin_fee
        self.bitcoin_delay = bitcoin_delay
        if coins_for_parties == "max_value":
            self.coins = {i: MAX_COINS for i in range(nr_players)}
        elif coins_for_parties == "small_value":
            self.coins = {i: bitcoin_fee * 10000 for i in range(nr_players)}
        elif coins_for_parties == "random":
            self.coins = {i: max(0, random.normalvariate(MAX_COINS/2, MAX_COINS/4)) for i in range(nr_players)}
        else:
            raise ValueError

    def get_unit_transaction_cost(self):
        return (self.bitcoin_fee, self.bitcoin_delay)

    # tx_size for 1-input-1-output P2WPKH (tx size in vbytes)
    def get_fee(self, tx_size = 109.5):
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

    def __eq__(self, other):
        return (
            self.bitcoin_fee == other.bitcoin_fee and
            self.bitcoin_delay == other.bitcoin_delay and
            self.coins == other.coins
        )
            
# this acts as super class for LN, Elmo, LVPC, Donner
class Payment_Network(ABC):
    def __init__(
        self, nr_players, bitcoin_fee = 1000000,
        bitcoin_delay = 3600, coins_for_parties = "max_value"
    ):
        self.plain_bitcoin = PlainBitcoin(nr_players, bitcoin_fee, bitcoin_delay, coins_for_parties)
        self.base_delay = BASE_DELAY
        @property
        @abstractmethod
        def network(self):
            pass

    @abstractmethod
    def get_distances_and_paths_from_source(self, sender, future_payments):
        pass

    def get_onchain_option(self, sender, receiver, value, knowledge_sender):
        future_payments, num_payments_sender, num_total_payments = knowledge_sender
        onchain_time = self.plain_bitcoin.get_delay()
        onchain_fee = self.plain_bitcoin.get_fee()
        if onchain_fee + value > self.plain_bitcoin.coins[sender]:
            return None
        onchain_centrality = self.network.get_centrality(sender)
        onchain_distance, cheapest_paths_from_sender = self.get_distances_and_paths_from_source(sender, future_payments)
        return {
            'delay': onchain_time,
            'fee': onchain_fee,
            'centrality': onchain_centrality,
            'distance': onchain_distance,
            'payment_information': { 'kind': 'onchain', 'data': (sender, receiver, value) }
        }
    