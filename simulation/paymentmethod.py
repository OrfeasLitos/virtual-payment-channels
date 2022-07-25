import random
import math
import numpy as np
import operator
# review: discuss the new class model
from abc import ABC, abstractmethod, abstractproperty
from network import Network, Network_Elmo

# units in millisatoshis
# default on-chain fees from https://bitcoinfees.net/ for an 1-input-2-output P2WPKH on 14/4/2022
# default max coins loosely copied from real world USD figures

MULTIPLIER_CHANNEL_BALANCE = MULTIPLIER_CHANNEL_BALANCE_LN = MULTIPLIER_CHANNEL_BALANCE_ELMO = MULTIPLIER_CHANNEL_BALANCE_LVPC = 5

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
    def __init__(self, nr_players, max_coins = 2000000000000000, bitcoin_fee = 1000,
                bitcoin_delay = 3600, coins_for_parties = "max_value"):
        self.max_coins = max_coins
        self.bitcoin_fee = bitcoin_fee
        self.bitcoin_delay = bitcoin_delay
        match coins_for_parties:
            case "max_value":
                self.coins = {i: max_coins for i in range(nr_players)}
            case "small_value":
                self.coins = {i: bitcoin_fee * 10000 for i in range(nr_players)}
            case "random":
                # maybe better Pareto distribution?
                self.coins = {i: max(0, random.normalvariate(max_coins/2, max_coins/4)) for i in range(nr_players)}
            case _:
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
            self.max_coins == other.max_coins and
            self.bitcoin_fee == other.bitcoin_fee and
            self.bitcoin_delay == other.bitcoin_delay and
            self.coins == other.coins
        )
            
# this should act as super class for LN, Elmo, etc.
class Payment_Network(ABC):
    def __init__(
        self, nr_players, max_coins = 2000000000000000, bitcoin_fee = 1000000,
        bitcoin_delay = 3600, coins_for_parties = "max_value"
    ):
        self.plain_bitcoin = PlainBitcoin(nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties)
        @property
        @abstractmethod
        def network(self):
            pass

    @abstractmethod
    def get_distances(self, sender, future_payments):
        pass

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
    