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

MULTIPLIER_CHANNEL_BALANCE_LN = MULTIPLIER_CHANNEL_BALANCE_ELMO = 5

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
    

# LN fees from https://www.reddit.com/r/lightningnetwork/comments/tmn1kc/bmonthly_ln_fee_report/

class LN(Payment_Network):
    def __init__(
        self, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600, ln_fee = 0.00002, ln_delay = 0.05,
        opening_transaction_size = 121.5, base_fee = 1000, coins_for_parties = "max_value"
    ):
        super().__init__(nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties)
        self.ln_fee = ln_fee
        self.ln_delay = ln_delay
        self.opening_transaction_size = opening_transaction_size
        self.network = Network(nr_players)
        self.base_fee = base_fee

    def get_payment_time(self, path):
        return self.ln_delay * len(path)

    def get_payment_fee(self, payment, num_hops):
        sender, receiver, value = payment
        return (self.base_fee +  value * self.ln_fee) * num_hops

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
            fee_intermediary = self.ln_fee * value + self.base_fee
            encountered_parties.add(future_sender)
            encountered_parties.add(future_receiver)
            if future_sender != source:
                # TODO: think about discarding first part of the tuple.
                path_data.append((
                    future_sender,
                    weight_endpoint if future_receiver == source else weight_intermediary,
                    self.network.find_cheapest_path(future_sender, source, value, fee_intermediary)
                ))
            if future_receiver != source:
                path_data.append((
                    future_receiver,
                    weight_endpoint if future_sender == source else weight_intermediary,
                    self.network.find_cheapest_path(source, future_receiver, value, fee_intermediary)
                ))

        # taken from here: https://coingate.com/blog/post/lightning-network-bitcoin-stats-progress
        # is quite old source. # TODO: look for newer source.
        dummy_amount = 500000000
        fee_intermediary = self.ln_fee * dummy_amount + self.base_fee
        for party in (set(self.network.graph.nodes()).difference(encountered_parties)):
            path_data.append((
                party,
                weight_other,
                self.network.find_cheapest_path(source, party, dummy_amount, fee_intermediary)
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

    def get_new_channel_option(self, sender, receiver, value, future_payments, counterparty):
        # case channel already exists.
        if self.network.graph.get_edge_data(sender, counterparty) is not None:
            return None
        new_channel_time = self.plain_bitcoin.get_delay() + self.ln_delay
        new_channel_fee = self.plain_bitcoin.get_fee(self.opening_transaction_size)
        sum_future_payments = sum_future_payments_to_counterparty(sender, counterparty, future_payments)
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

    def get_offchain_option(self, sender, receiver, value, future_payments):
        fee_intermediary = fee_intermediary = self.ln_fee * value + self.base_fee
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value, fee_intermediary)
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

class Elmo(Payment_Network):
    # TODO: find reasonable value for fee_intermediary, lock_value, opening_transaction_size, elmo_delay
    def __init__(
        self, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600, 
        coins_for_parties = "max_value", fee_intermediary = 10000,
        opening_transaction_size = 200, elmo_pay_delay = 0.05,
        elmo_new_virtual_channel_delay = 1
    ):
        super().__init__(nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties)
        self.network = Network_Elmo(nr_players)
        self.fee_intermediary = fee_intermediary
        self.opening_transaction_size = opening_transaction_size
        # delay for opening new virtual channel (per hop)
        self.elmo_pay_delay = elmo_pay_delay
        self.elmo_new_virtual_channel_delay = elmo_new_virtual_channel_delay

    # adjusted from LN
    # review: This should be minimum for parties with a channel,
    # review: progressively larger for parties that can open a channel on a progressively larger virtual layer
    # review: and infinite for disconnected parties. Let's discuss this.
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
            # TODO: think of a good lock_value or balance the sender wants to put on a new channel
            dummy_lock_value = 10 * 500000000 + value
            if future_sender != source:
                # TODO: think about discarding first part of the tuple.
                path_data.append((
                    future_sender,
                    weight_endpoint if future_receiver == source else weight_intermediary,
                    self.network.find_cheapest_path(future_sender, source, dummy_lock_value, self.fee_intermediary)
                ))
            if future_receiver != source:
                path_data.append((
                    future_receiver,
                    weight_endpoint if future_sender == source else weight_intermediary,
                    self.network.find_cheapest_path(source, future_receiver, dummy_lock_value, self.fee_intermediary)
                ))

        dummy_lock_value = 11 * 500000000
        for party in (set(self.network.graph.nodes()).difference(encountered_parties)):
            path_data.append((
                party,
                weight_other,
                self.network.find_cheapest_path(source, party, dummy_lock_value, self.fee_intermediary)
            ))
        
        for counterparty, weight, cost_and_path in path_data:
            if cost_and_path is None:
                distances.append((weight, math.inf))
            else:
                _, cheapest_path = cost_and_path
                distances.append((weight, len(cheapest_path)-1))

        return distances

    def get_new_virtual_channel_time(self, hops):
        return self.elmo_new_virtual_channel_delay * hops

    def get_new_virtual_channel_fee(self, path):
        return self.fee_intermediary * (len(path) - 2)

    # adjusted from LN
    def get_new_channel_option(self, sender, receiver, value, future_payments):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        new_channel_time = self.plain_bitcoin.get_delay() + self.elmo_pay_delay
        new_channel_fee = self.plain_bitcoin.get_fee(self.opening_transaction_size)
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        sender_coins = min(
            self.plain_bitcoin.coins[sender] - value - new_channel_fee,
            MULTIPLIER_CHANNEL_BALANCE_ELMO * sum_future_payments
        )
        if sender_coins < 0:
            return None
        self.network.add_channel(sender, sender_coins, receiver, value, None)
        new_channel_centrality = self.network.get_harmonic_centrality()
        new_channel_distance = self.get_distances(sender, future_payments)
        self.network.remove_channel(sender, receiver)
        return {
            'delay': new_channel_time,
            'fee': new_channel_fee,
            'centrality': new_channel_centrality,
            'distance': new_channel_distance,
            'payment_information': {
                'kind': 'Elmo-open-channel',
                'data': (sender, receiver, value, sender_coins)
            }
        }

    def get_new_virtual_channel_option(self, sender, receiver, value, future_payments):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        # this is a simplification. TODO: think if this is what we want.
        anticipated_lock_value = MULTIPLIER_CHANNEL_BALANCE_ELMO * sum_future_payments + value
        cost_and_path = self.network.find_cheapest_path(sender, receiver, anticipated_lock_value, self.fee_intermediary)
        if cost_and_path is None:
            return None
        hops, path = cost_and_path
        new_virtual_channel_fee = self.get_new_virtual_channel_fee(path)
        # TODO: find better name for channel_balances
        # TODO: think of reasonable factor.
        # the factor is introduced so that lower channel doesn't end up with 0 balance. Do we want this?
        availability_factor = 4
        base_channels_max_lock_values = [
            self.network.graph[path[i]][path[i+1]]['balance'] / availability_factor - value - new_virtual_channel_fee for i in range(len(path)-1)
        ]
        # review: I'm not sure what is this append doing
        base_channels_max_lock_values
        max_common_lock_value = min(
            base_channels_max_lock_values
        )
        desired_virtual_coins = MULTIPLIER_CHANNEL_BALANCE_ELMO * sum_future_payments
        sender_coins = min(max_common_lock_value, desired_virtual_coins)
        if sender_coins < 0:
            return None
        payment_information = {'kind': 'Elmo-open-virtual-channel', 'data': (path, value, sender_coins)}
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

    def get_elmo_pay_option(self, sender, receiver, value, future_payments):
        payment_information = {'kind': 'Elmo-pay', 'data': (sender, receiver, value)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        centrality_elmo_pay = self.network.get_harmonic_centrality()
        distance_elmo_pay = self.get_distances(sender, future_payments)
        self.undo(payment_information)
        return {
            'delay': self.elmo_pay_delay,
            'fee': 0,
            'centrality': centrality_elmo_pay,
            'distance': distance_elmo_pay,
            'payment_information': payment_information
        }

    def get_payment_options(self, sender, receiver, value, future_payments):
        onchain_option = self.get_onchain_option(sender, receiver, value, future_payments)
        new_channel_option = self.get_new_channel_option(sender, receiver, value, future_payments)
        new_virtual_channel_option = self.get_new_virtual_channel_option(sender, receiver, value, future_payments)
        elmo_pay_option = self.get_elmo_pay_option(sender, receiver, value, future_payments)
        options = [onchain_option, new_channel_option, new_virtual_channel_option, elmo_pay_option]
        return [option for option in options if option is not None]
        
    def lock_coins(self, path, lock_value):
        # Question: are coins on the first channel in the path also locked?
        # review: yes, the sender locks these coins in its base channel as well.
        for i in range(len(path) - 1):
            sender = path[i]
            receiver = path[i+1]
            if self.network.graph[sender][receiver]['balance'] < lock_value:
                for j in range(i):
                    sender = path[j]
                    receiver = path[j+1]
                    self.network.graph[sender][receiver]['balance'] += lock_value
                    self.network.graph[sender][receiver]['locked_coins'] -= lock_value
                raise ValueError
            self.network.graph[sender][receiver]['balance'] -= lock_value
            self.network.graph[sender][receiver]['locked_coins'] += lock_value

    def undo_locking(self, path, lock_value):
        # TODO: maybe make it similarly as for update_balances and include this with an operator
        # and boolean variable in lock.
        # undoes just one lock, doesn't free all locked money.
        for i in range(len(path) - 1):
            sender = path[i]
            receiver = path[i+1]
            self.network.graph[sender][receiver]['balance'] += lock_value
            self.network.graph[sender][receiver]['locked_coins'] -= lock_value

    # TODO: think if update balances, locking, etc should be in network.
    # adjusted from LN
    def update_balances_new_virtual_channel(self, path, value, sender_coins, new_channel = False):
        # the pay argument tells whether this corresponds to making a payment
        # or undoing it.
        # all the "speaking names" like op_take, received, etc are in the case of a payment
        # in case of undoing they do the opposite.
        op_take, op_give = (operator.add, operator.sub) if new_channel else (operator.sub, operator.add)
        num_intermediaries = len(path) - 2
        sender = path[0]
        cost_sender = num_intermediaries * self.fee_intermediary
        if cost_sender > self.network.graph[sender][path[1]]['balance'] and new_channel == True:
            raise ValueError
        # update the balances of the intermediaries.
        for i in range(1, num_intermediaries + 1):
            received = (num_intermediaries - (i-1)) * self.fee_intermediary
            transfered = received - self.fee_intermediary
            new_taker_balance = op_take(self.network.graph[path[i]][path[i-1]]['balance'], received)
            new_giver_balance = op_give(self.network.graph[path[i]][path[i+1]]['balance'], transfered)
            # we test just for new_giver_balance < 0 as in case of new virtual channel only giver_balance gets smaller
            # In case of undoing it, there was a payment done before, so there shouldn't occur numbers < 0.
            if new_giver_balance < 0:
                for j in range(1, i):
                    received = (num_intermediaries - (j-1)) * self.fee_intermediary
                    transfered = received - self.fee_intermediary
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
        match payment_information['kind']:
            case 'onchain':
                self.plain_bitcoin.pay(payment_information['data'])
            case 'Elmo-open-channel':
                # adjusted from LN-open
                sender, receiver, value, sender_coins = payment_information['data']
                self.network.add_channel(sender, sender_coins, receiver, value, None)
                # next update the coins of sender
                amount_sender = - (
                    sender_coins + value +
                    self.plain_bitcoin.get_fee(self.opening_transaction_size)
                )
                self.plain_bitcoin.update_coins(sender, amount_sender)
            case 'Elmo-open-virtual-channel':
                path, value, sender_coins = payment_information['data']
                sender = path[0]
                receiver = path[-1]
                # Question: are coins for new virtual channel taken from onchain-coins or from coins of some existing channel?
                if self.plain_bitcoin.coins[sender] < sender_coins + value:
                    raise ValueError
                # important that next line is at that position so that Error gets raised in case update is not possible
                # before anything else is done.
                self.update_balances_new_virtual_channel(path, value, sender_coins, new_channel=True)
                self.lock_coins(path, sender_coins + value)
                self.network.add_channel(sender, sender_coins, receiver, value, path)
            case 'Elmo-pay':
                sender, receiver, value = payment_information['data']
                self.pay(sender, receiver, value)
            case _:
                raise ValueError

    def undo(self, payment_information):
        match payment_information['kind']:
            case 'Elmo-open-virtual-channel':
                path, value, sender_coins = payment_information['data']
                sender = path[0]
                receiver = path[-1]
                self.undo_locking(path, sender_coins + value)
                self.update_balances_new_virtual_channel(path, value, sender_coins, new_channel=False)
                self.plain_bitcoin.coins[sender] += sender_coins + value
                self.network.remove_channel(sender, receiver)
            case 'Elmo-pay':
                sender, receiver, value = payment_information['data']
                if self.network.graph.get_edge_data(sender, receiver) is None:
                    raise ValueError
                self.network.graph[sender][receiver]['balance'] += value
                self.network.graph[receiver][sender]['balance'] -= value
            case _:
                raise ValueError
