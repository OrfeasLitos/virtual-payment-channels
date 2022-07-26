import math
import operator
from paymentmethod import PlainBitcoin, Payment_Network, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE
from network import Network_Elmo, Network_LVPC, Network_Donner

class Custom_Elmo_LVPC_Donner(Payment_Network):
    # TODO: find reasonable value for fee_intermediary, opening_transaction_size, delay
    def __init__(
        self, method_name, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600, 
        coins_for_parties = "max_value", fee_intermediary = 10000,
        opening_transaction_size = 200, pay_delay = 0.05,
        new_virtual_channel_delay = 1
    ):
        super().__init__(nr_players, max_coins, bitcoin_fee, bitcoin_delay, coins_for_parties)
        self.method_name = method_name
        # review: the three last assignments of each case can be done more succinctly: `self.open_channel_string = method_name + "-open-channel"`
        match method_name:
            case "Elmo":
                self.network = Network_Elmo(nr_players)
                self.open_channel_string = "Elmo-open-channel"
                self.open_virtual_channel_string = "Elmo-open-virtual-channel"
                self.pay_string = "Elmo-pay"
            case "LVPC":
                self.network = Network_LVPC(nr_players)
                self.open_channel_string = "LVPC-open-channel"
                self.open_virtual_channel_string = "LVPC-open-virtual-channel"
                self.pay_string = "LVPC-pay"
            case "Donner":
                self.network = Network_Donner(nr_players)
                self.open_channel_string = "Donner-open-channel"
                self.open_virtual_channel_string = "Donner-open-virtual-channel"
                self.pay_string = "Donner-pay"
            case _:
                raise ValueError

        self.fee_intermediary = fee_intermediary
        self.opening_transaction_size = opening_transaction_size
        # delay for opening new virtual channel (per hop)
        self.pay_delay = pay_delay
        self.new_virtual_channel_delay = new_virtual_channel_delay

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
        return self.new_virtual_channel_delay * hops

    def get_new_virtual_channel_fee(self, path):
        return self.fee_intermediary * (len(path) - 2)

    # adjusted from LN
    def get_new_channel_option(self, sender, receiver, value, future_payments):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        new_channel_time = self.plain_bitcoin.get_delay() + self.pay_delay
        new_channel_fee = self.plain_bitcoin.get_fee(self.opening_transaction_size)
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        sender_coins = min(
            self.plain_bitcoin.coins[sender] - value - new_channel_fee,
            MULTIPLIER_CHANNEL_BALANCE * sum_future_payments
        )
        if sender_coins < 0:
            return None
        self.network.add_channel(sender, sender_coins, receiver, value, None)
        new_channel_centrality = self.network.get_harmonic_centrality()
        new_channel_distance = self.get_distances(sender, future_payments)
        self.network.close_channel(sender, receiver)
        return {
            'delay': new_channel_time,
            'fee': new_channel_fee,
            'centrality': new_channel_centrality,
            'distance': new_channel_distance,
            'payment_information': {
                'kind': self.open_channel_string,
                'data': (sender, receiver, value, sender_coins)
            }
        }

    def get_new_virtual_channel_option(self, sender, receiver, value, future_payments):
        # in case we have already a channel
        if self.network.graph.get_edge_data(sender, receiver) is not None:
            return None
        sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
        # this is a simplification. TODO: think if this is what we want.
        anticipated_lock_value = sum_future_payments + value
        if self.method_name != "LVPC":
            cost_and_path = self.network.find_cheapest_path(
                sender, receiver, anticipated_lock_value, self.fee_intermediary,
                function="new_virtual_donner" if self.method_name=="Donner" else "standard"
                )
        else:
            cost_and_path = self.network.find_cheapest_path_for_new_virtual(
                sender, receiver, anticipated_lock_value, self.fee_intermediary
            )
        if cost_and_path is None:
            return None
        hops, path = cost_and_path
        new_virtual_channel_fee = self.get_new_virtual_channel_fee(path)
        # the factor is introduced so that lower channel doesn't end up with 0 balance.
        availability_factor = 4
        base_channels_max_lock_values = [
            self.network.graph[path[i]][path[i+1]]['balance'] / availability_factor - value - new_virtual_channel_fee for i in range(len(path)-1)
        ]
        max_common_lock_value = min(
            base_channels_max_lock_values
        )
        desired_virtual_coins = MULTIPLIER_CHANNEL_BALANCE * sum_future_payments
        sender_coins = min(max_common_lock_value, desired_virtual_coins)
        if sender_coins < 0:
            return None
        payment_information = {'kind': self.open_virtual_channel_string, 'data': (path, value, sender_coins)}
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

    def get_pay_option(self, sender, receiver, value, future_payments):
        payment_information = {'kind': self.pay_string, 'data': (sender, receiver, value)}
        try:
            self.do(payment_information)
        except ValueError:
            return None
        centrality_pay = self.network.get_harmonic_centrality()
        distance_pay = self.get_distances(sender, future_payments)
        self.undo(payment_information)
        return {
            'delay': self.pay_delay,
            'fee': 0,
            'centrality': centrality_pay,
            'distance': distance_pay,
            'payment_information': payment_information
        }

    def get_payment_options(self, sender, receiver, value, future_payments):
        onchain_option = self.get_onchain_option(sender, receiver, value, future_payments)
        new_channel_option = self.get_new_channel_option(sender, receiver, value, future_payments)
        new_virtual_channel_option = self.get_new_virtual_channel_option(sender, receiver, value, future_payments)
        pay_option = self.get_pay_option(sender, receiver, value, future_payments)
        options = [onchain_option, new_channel_option, new_virtual_channel_option, pay_option]
        return [option for option in options if option is not None]

    # TODO: think if update balances should be in network.
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
            case self.open_channel_string:
                # adjusted from LN-open
                sender, receiver, value, sender_coins = payment_information['data']
                self.network.add_channel(sender, sender_coins, receiver, value, None)
                # next update the coins of sender
                amount_sender = - (
                    sender_coins + value +
                    self.plain_bitcoin.get_fee(self.opening_transaction_size)
                )
                self.plain_bitcoin.update_coins(sender, amount_sender)
            case self.open_virtual_channel_string:
                path, value, sender_coins = payment_information['data']
                sender = path[0]
                receiver = path[-1]
                # Question: are coins for new virtual channel taken from onchain-coins or from coins of some existing channel?
                if self.plain_bitcoin.coins[sender] < sender_coins + value:
                    raise ValueError
                # important that next line is at that position so that Error gets raised in case update is not possible
                # before anything else is done.
                self.update_balances_new_virtual_channel(path, value, sender_coins, new_channel=True)
                self.network.lock_coins(path, sender_coins + value)
                self.network.add_channel(sender, sender_coins, receiver, value, path)
            case self.pay_string:
                sender, receiver, value = payment_information['data']
                self.pay(sender, receiver, value)
            case _:
                raise ValueError

    def undo(self, payment_information):
        match payment_information['kind']:
            case self.open_virtual_channel_string:
                path, value, sender_coins = payment_information['data']
                sender = path[0]
                receiver = path[-1]
                amount_sender, amount_receiver = self.network.cooperative_close_channel(sender, receiver)
                self.update_balances_new_virtual_channel(path, amount_receiver, amount_sender, new_channel=False)
            case self.pay_string:
                sender, receiver, value = payment_information['data']
                if self.network.graph.get_edge_data(sender, receiver) is None:
                    raise ValueError
                self.network.graph[sender][receiver]['balance'] += value
                self.network.graph[receiver][sender]['balance'] -= value
            case _:
                raise ValueError

