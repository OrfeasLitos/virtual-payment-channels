import math
from network import Network

# units in millisatoshis
# default on-chain fees from https://bitcoinfees.net/ for an 1-input-2-output P2WPKH on 14/4/2022
# default max coins loosely copied from real world USD figures

class PlainBitcoin():
    def __init__(self, nr_players, max_coins = 2000000000000000, bitcoin_fee = 1000000,
                bitcoin_delay = 3600):
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

    def update_coins(self, party, amount):
        if self.coins[party] + amount < 0:
            raise ValueError
        self.coins[party] += amount

    def pay(self, data):
        sender, receiver, value = data
        # should self.get_fee() also be multiplied with value
        try:
            amount_sender = - value - self.get_fee()
            self.update_coins(sender, amount_sender)
            self.update_coins(receiver, value)
        except ValueError:
            raise

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

    def sum_future_payments_to_receiver(self, receiver, future_payments):
        """
        This is used to determine a minimum amount that should be put on a new channel between sender and receiver.
        """
        future_payments_to_receiver = [future_payment for future_payment in future_payments if future_payment[1] == receiver]
        return sum([payment[2] for payment in future_payments_to_receiver])

    def get_distance_to_future_parties(self, future_payments):
        """
        Returns the sum of the distances of the future parties
        (if parties occur multiple times their distance is summed multiple times)
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
            if cost_and_path is not None:
                _, cheapest_path = cost_and_path
                distances.append(len(cheapest_path)-1)
            else:
                distances.append(math.inf)
        return distances

    def update_balances(self, value, ln_fee, base_fee, path):
        num_intermediaries = len(path) - 2
        sender = path[0]
        receiver = path[-1]
        # review: we could also get `fee_intermediary` directly as input, to reduce parameters
        fee_intermediary = ln_fee * value + base_fee
        cost_sender = value + num_intermediaries * fee_intermediary
        if self.network.graph[sender][path[1]]['balance'] - cost_sender < 0:
            raise ValueError
        self.network.graph[sender][path[1]]['balance'] -= cost_sender
        self.network.graph[receiver][path[-2]]['balance'] += value
        # Now have to update the balances of the intermediaries.
        for i in range(1, num_intermediaries + 1):
            received = (num_intermediaries - i) * fee_intermediary
            transfered = received - fee_intermediary
            self.network.graph[path[i]][path[i-1]]['balance'] += received
            self.network.graph[path[i]][path[i+1]]['balance'] -= transfered

    def get_onchain_option(self, sender, receiver, value, future_payments):
        onchain_time = self.plain_bitcoin.get_delay()
        # review: bitcoin fee depends on tx size. we should hardcode the sizes of the various txs of interest and use the simple tx (a.k.a. P2WP2KH) fee here
        onchain_fee = self.plain_bitcoin.get_fee()
        if onchain_fee + value > self.plain_bitcoin.coins[sender]:
            return None
        onchain_centrality = self.network.get_harmonic_centrality()
        onchain_distance = self.get_distance_to_future_parties(future_payments)
        onchain_option = {
            'delay': onchain_time,
            'fee': onchain_fee,
            'centrality': onchain_centrality,
            'distance': onchain_distance,
            'payment_information': { 'kind': 'onchain', 'data': (sender, receiver, value) }
        }
        return onchain_option

    def get_new_channel_option(self, sender, receiver, value, future_payments, counterparty):
        new_channel_time = self.plain_bitcoin.get_delay() + self.ln_delay
        new_channel_fee = self.plain_bitcoin.get_fee() * self.opening_transaction_size
        # TODO: incorporate counterparty in min_amount
        min_amount = self.sum_future_payments_to_receiver(receiver, future_payments)
        # review: give receiver the current payment value (corresponds to `push_msat` of LN).
        # review: our initial coins should be slightly higher than the minimum needed,
        # review: in order to accommodate for future payments and act as intermediary.
        # review: we can say e.g. `min(our on-chain coins, 2 * (min_amount - value))` and we can improve from there
        sender_coins = min(self.plain_bitcoin.coins[sender] , 2 * min_amount) - value - new_channel_fee
        if sender_coins + value + new_channel_fee > self.plain_bitcoin.coins[sender]:
            raise ValueError
        # TODO: the formula above isn't entirely correct yet, as it should also include possible offchain fees
        # in case the counterparty is not the receiver.
        # TODO: discuss what to do if sender doesn't have enough money for future transactions,
        # but could open channel and make the transaction.
        self.network.add_channel(sender, min_amount, counterparty, value)
        new_channel_centrality = self.network.get_harmonic_centrality()
        new_channel_distance = self.get_distance_to_future_parties(future_payments)
        if counterparty == receiver:
            # TODO: adjust future_payments. Maybe in Simulation
            new_channel_offchain_option = self.get_offchain_option(
                sender, receiver, value, future_payments[1:])
        else:
            new_channel_offchain_option = None
        self.network.close_channel(sender, counterparty)

        new_channel_option = {
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
        return new_channel_option

    def get_offchain_option(self, sender, receiver, value, future_payments):
        # review: if offchain_cost_path is None: return None
        # review: otherwise return the dict immediately
        # review: this way we don't need the offchain_option var at all
        # review: and the logic is more "local"
        offchain_option = None
        offchain_cost_and_path = self.network.find_cheapest_path(sender, receiver, value)
        if offchain_cost_and_path is not None:
            offchain_hops, offchain_path = offchain_cost_and_path
            offchain_time = self.get_payment_time(offchain_path)
            payment = (sender, receiver, value)
            offchain_fee = self.get_payment_fee(payment, offchain_hops)
            # review: we should do the payment, get centrality and distance, undo the payment
            offchain_centrality = self.network.get_harmonic_centrality()
            offchain_distance = self.get_distance_to_future_parties(future_payments)
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
                    payment_information['data'])
                counterparty_coins = value if counterparty == receiver else 0
                self.network.add_channel(sender, sender_coins, counterparty, counterparty_coins)
                # next update the coins of sender
                amount_sender = - (sender_coins + counterparty_coins + self.plain_bitcoin.get_fee())
                self.plain_bitcoin.update_coins(sender, amount_sender)
                # use ln-pay here to make the off-chain payment after opening a new channel.
                if counterparty != receiver:
                    self.do(new_channel_offchain_option['payment_information'])
            case 'ln-pay':
                offchain_path, value = payment_information['data']
                try:
                    self.update_balances(value, self.ln_fee, self.base_fee, offchain_path)
                except ValueError:
                    # TODO: think of what should happen in case of a ValueError
                    raise Exception("can't make payment")
            case _:
                raise ValueError
