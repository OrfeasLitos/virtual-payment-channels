
import math
import networkx as nx
from numpy.testing import assert_almost_equal as assert_eq
from ln import LN
from utility import Utility
from paymentmethod import (
    sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE,
    MAX_COINS
)
from tests import make_example_utility_function, make_example_simulation_for_all, get_knowledge_sender

def make_example_network_ln(base_fee = 1000, ln_fee = 0.00002):
    lightning = LN(10, base_fee = base_fee, ln_fee = ln_fee)

    lightning.network.add_channel(0, 3000000000., 2, 7000000000.)
    lightning.network.add_channel(0, 6000000000., 1, 7000000000.)
    lightning.network.add_channel(1, 4000000000., 4, 8000000000.)
    lightning.network.add_channel(0, 5000000000., 2, 6000000000.)
    lightning.network.add_channel(3, 9000000000., 4, 8000000000.)
    lightning.network.add_channel(2, 9000000000., 3, 2000000000.)
    lightning.network.add_channel(1, 10000000000., 2, 8000000000.)
    lightning.network.add_channel(4, 10000000000., 7, 8000000000.)
    lightning.network.add_channel(3, 10000000000., 8, 8000000000.)
    return lightning

def make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 0.00002):
    lightning = make_example_network_ln(base_fee, ln_fee)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return base_fee, ln_fee, lightning, future_payments

def make_example_simulation_ln(seed = 12345, nr_players = 10, coins_for_parties = 'max_value'):
    return make_example_simulation_for_all("LN", seed, nr_players, coins_for_parties)

def test_get_payment_fee_ln():
    def get_payment_fee_with_path(base_fee, ln_fee, payment, path):
        sender, receiver, value = payment
        return (base_fee +  value * ln_fee) * (len(path) - 2)
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    for payment in future_payments:
        sender, receiver, value = payment
        fee_intermediary = base_fee + value * ln_fee
        path = lightning.network.find_cheapest_path(sender, receiver, value, fee_intermediary)
        num_hops = len(path) - 1
        assert (get_payment_fee_with_path(base_fee, ln_fee, payment, path) ==
            lightning.get_payment_fee(payment, num_hops)
        )

def test_get_payment_options_ln_enough_money():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
    )
    sender = 0
    receiver = 7
    value = 1000000000.
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    sum_future_payments = sum_future_payments_to_counterparty(sender, receiver, future_payments)
    payment_options = lightning.get_payment_options(sender, receiver, value, knowledge_sender)
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    actual_onchain_option = payment_options[0]
    assert payment_options[1]['payment_information']['kind'] == 'ln-open'
    actual_ln_open_option = payment_options[1]
    assert payment_options[2]['payment_information']['kind'] == 'ln-pay'
    actual_ln_pay_option = payment_options[2]

    on_chain_centrality = lightning.network.get_centrality(0)
    onchain_fee = lightning.plain_bitcoin.get_fee()
    expected_onchain_option = {
        'delay' : 3600,
        'fee': onchain_fee,
        'centrality': on_chain_centrality,
        'distance': [
            (100, 3), (100, 3), (100, 3), (100, 1), (1, 1), (1, 2),(1, 2),
            (1, math.inf), (1, math.inf), (1, math.inf)
        ],
        'payment_information': { 'kind': 'onchain', 'data': (0, 7, 1000000000.)}
    }

    expected_ln_open_option = {
        'delay' : lightning.plain_bitcoin.bitcoin_delay + lightning.ln_delay,
        'fee' : lightning.plain_bitcoin.get_fee(lightning.opening_transaction_size),
        'centrality' : None,
        'distance': [
            (100, 1), (100, 1), (100, 1), (100, 3), (1, 1), (1, 2), (1, 2),
            (1, math.inf), (1, math.inf), (1, math.inf)
        ],
        'payment_information' : {
            'kind' : 'ln-open',
            'data' : (
                sender, receiver, value, receiver,
                sum_future_payments + MULTIPLIER_CHANNEL_BALANCE * value, None
            )
        }
    }
    expected_ln_pay_option = {
        'delay' : lightning.get_payment_time([0,1,4,7]),
        'fee' : lightning.get_payment_fee((0, 7, 1000000000.), 3),
        'centrality' : None,
        'distance': [
            (100, 1), (100, 3), (100, 3), (100, 3), (1, 1), (1, 2), (1, 2),
            (1, math.inf), (1, math.inf), (1, math.inf)
        ],
        'payment_information' : {'kind' : 'ln-pay', 'data' : ([0,1,4,7], 1000000000.)}
    }
    assert expected_onchain_option['delay'] == actual_onchain_option['delay']
    assert expected_onchain_option['fee'] == actual_onchain_option['fee']
    assert expected_onchain_option['centrality'] == actual_onchain_option['centrality']
    expected_onchain_option['distance'].sort()
    actual_onchain_option['distance'].sort()
    assert expected_onchain_option['distance'] == actual_onchain_option['distance']
    assert expected_onchain_option['payment_information'] == actual_onchain_option['payment_information']

    assert_eq(expected_ln_open_option['fee'], actual_ln_open_option['fee'])
    assert_eq(expected_ln_open_option['delay'], actual_ln_open_option['delay'])
    expected_ln_open_option['distance'].sort()
    actual_ln_open_option['distance'].sort()
    assert expected_ln_open_option['distance'] == actual_ln_open_option['distance']
    assert expected_ln_open_option['payment_information']['data'] == actual_ln_open_option['payment_information']['data']

    assert_eq(expected_ln_pay_option['delay'], actual_ln_pay_option['delay'])
    assert_eq(expected_ln_pay_option['fee'], actual_ln_pay_option['fee'])
    expected_ln_pay_option['distance'].sort()
    actual_ln_pay_option['distance'].sort()
    assert expected_ln_pay_option['distance'] == actual_ln_pay_option['distance']
    assert expected_ln_pay_option['payment_information'] == actual_ln_pay_option['payment_information']

def test_get_payment_options_ln():
    test_get_payment_options_ln_enough_money()

def test_choose_payment_method_offchain_best_ln():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = lightning.get_payment_options(sender, 7, 1., knowledge_sender)
    utility_function = make_example_utility_function(10000, 5000, 1, 1)
    utility = Utility('customized', utility_function=utility_function)
    payment_method, fee, delay = utility.choose_payment_method(sender, payment_options)
    assert payment_method['kind'] == 'ln-pay'

def test_choose_payment_method_new_channel_best_ln():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 0.2)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = lightning.get_payment_options(sender, 7, 1000000000., knowledge_sender)
    utility_function = make_example_utility_function(10000, 50, 200, 1)
    utility = Utility('customized', utility_function=utility_function)
    payment_method, _, _ = utility.choose_payment_method(sender, payment_options)
    assert payment_method['kind'] == 'ln-open'

def test_choose_payment_method_onchain_best_ln():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 200)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = lightning.get_payment_options(sender, 7, 1000000000., knowledge_sender)
    # there's no offchain option
    # the fee in the utility favors the onchain option.
    utility_function = make_example_utility_function(1, 0, 0, 0)
    utility = Utility('customized', utility_function=utility_function)
    payment_method, _, _ = utility.choose_payment_method(sender, payment_options)
    assert payment_method['kind'] == 'onchain'

def test_choose_payment_method_ln():
    test_choose_payment_method_offchain_best_ln()
    test_choose_payment_method_new_channel_best_ln()
    test_choose_payment_method_onchain_best_ln()

def test_LN():
    nr_players = 10
    lightning = LN(nr_players)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    result = sum_future_payments_to_counterparty(0, 7, future_payments)
    payment_options = lightning.get_payment_options(0, 7, 1., knowledge_sender)
    assert result == 3.6

def make_example_values_for_do_ln():
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
    )
    value = 1000000000.
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = lightning.get_payment_options(sender, 7, value, knowledge_sender)
    return base_fee, ln_fee, lightning, future_payments, value, payment_options

def test_do_ln_onchain():
    base_fee, ln_fee, lightning, future_payments, value, payment_options = (
        make_example_values_for_do_ln()
    )
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    payment_information_onchain = payment_options[0]['payment_information']
    lightning.do(payment_information_onchain)
    # sender should have MAX_COINS - value - fee many coins, receiver MAX_COINS + value
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS - value - lightning.plain_bitcoin.get_fee() 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS + value

def test_do_ln_onchain_exception():
    lightning = make_example_network_ln(base_fee = 1000, ln_fee = 0.00002)
    payment_information_onchain = { 
        'kind': 'onchain', 'data': (0, 7, 999999999999999999999.)
    }
    try:
        lightning.do(payment_information_onchain)
        assert False, 'should raise exception as amount is too high'
    except ValueError:
        pass

def test_do_ln_offchain():
    base_fee, ln_fee, lightning, future_payments, value, payment_options = (
        make_example_values_for_do_ln()
    )
    balances_before = nx.get_edge_attributes(lightning.network.graph, "balance")
    fee_intermediary = base_fee + value*ln_fee
    for payment_option in payment_options:
        match payment_option['payment_information']['kind']:
            case 'ln-pay':
                payment_information_offchain = payment_option['payment_information']

    # path is [0,1,4,7]
    path, _ = payment_information_offchain['data']
    assert path == [0,1,4,7]
    lightning = make_example_network_ln(base_fee=1000, ln_fee = 0.00002)
    lightning.do(payment_information_offchain)
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS
    assert_eq(lightning.network.graph[0][1]['balance'], balances_before[(0, 1)] - value - 2*fee_intermediary)
    assert_eq(lightning.network.graph[1][0]['balance'], balances_before[(1, 0)] + value + 2*fee_intermediary)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], balances_before[(1, 4)] - value - fee_intermediary)
    assert_eq(lightning.network.graph[4][1]['balance'], balances_before[(4, 1)] + value + fee_intermediary)
    assert_eq(lightning.network.graph[4][7]['balance'], balances_before[(4, 7)] - value)
    assert_eq(lightning.network.graph[7][4]['balance'], balances_before[(7, 4)] + value)
    assert_eq(lightning.network.graph[1][2]['balance'], balances_before[(1, 2)])

def test_do_ln_offchain_exception():
    base_fee = 1000
    ln_fee = 200
    lightning = make_example_network_ln(base_fee, ln_fee)
    payment_information_offchain = {
        'kind': 'ln-pay', 'data': ([0,1,4,7], 1000000000)
    }
    try:
        lightning.do(payment_information_offchain)
        assert False, 'fee is too high, should raise Exception'
    except ValueError:
        pass

def test_do_ln_new_channel():
    _, _, lightning, future_payments, value, payment_options = (
        make_example_values_for_do_ln()
    )
    assert payment_options[1]['payment_information']['kind'] == 'ln-open'
    payment_information_new_channel = payment_options[1]['payment_information']

    lightning.do(payment_information_new_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 7, future_payments)
    sender_coins = sum_future_payments + MULTIPLIER_CHANNEL_BALANCE * value
    receiver_coins = value
    tx_size = lightning.opening_transaction_size
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS - lightning.plain_bitcoin.get_fee(tx_size) - sender_coins - receiver_coins 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS
    # test the balances on ln (-2 for base fee and payment, +1 for payment).
    assert lightning.network.graph[0][7]['balance'] == sender_coins 
    assert lightning.network.graph[7][0]['balance'] == receiver_coins


def test_do_ln_new_channel_exception():
    lightning = make_example_network_ln(base_fee = 1, ln_fee = 0.00002)
    payment_information_new_channel = {
        'kind': 'ln-open',
        'data': (0, 7, 1, 7, 99999999999999999999999, None)
    }
    try:
        lightning.do(payment_information_new_channel)
        assert False, "sender can't put more on channel than he has"
    except ValueError:
        pass

def test_do_ln():
    test_do_ln_onchain()
    test_do_ln_onchain_exception()
    test_do_ln_offchain()
    test_do_ln_offchain_exception()
    test_do_ln_new_channel()
    test_do_ln_new_channel_exception()

def test_update_balances_pay_enough_money_ln():
    lightning = make_example_network_ln(base_fee = 1000, ln_fee = 0.00002)
    balances_before = nx.get_edge_attributes(lightning.network.graph, "balance")
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000
    fee_intermediary = base_fee + value*ln_fee
    lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
    # sender 0 has 6000000000. in the beginning on the channel to 1
    # after update he should have value less for the transaction to 7 and 2*fee_intermediary less for the fee,
    assert_eq(lightning.network.graph[0][1]['balance'], balances_before[(0, 1)] - value - 2*fee_intermediary)
    # the first intermediary should have value + 2*fee_intermediary more on his channel with the sender
    assert_eq(lightning.network.graph[1][0]['balance'], balances_before[(1, 0)] + value + 2*fee_intermediary)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], balances_before[(1, 4)] - value - fee_intermediary)
    assert_eq(lightning.network.graph[4][1]['balance'], balances_before[(4, 1)] + value + fee_intermediary)
    assert_eq(lightning.network.graph[4][7]['balance'], balances_before[(4, 7)] - value)
    assert_eq(lightning.network.graph[7][4]['balance'], balances_before[(7, 4)] + value)
    assert_eq(lightning.network.graph[1][2]['balance'], balances_before[(1, 2)])

def test_update_balances_pay_not_enough_money_ln():
    lightning = make_example_network_ln(base_fee=1000, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000000
    balances = nx.get_edge_attributes(lightning.network.graph, "balance")
    try:
        lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
        assert False, 'update_balances() should raise a ValueError'
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(lightning.network.graph, "balance")
        for key in balances.keys():
            assert_eq(balances[key], balances_after_failure[key])
        

def test_update_balances_reverse_ln():
    lightning = make_example_network_ln(base_fee = 1000, ln_fee = 0.00002)
    balances_before = nx.get_edge_attributes(lightning.network.graph, "balance")
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000
    lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
    # balances are updated, now we want to revert it
    lightning.update_balances(value, ln_fee, base_fee, path, pay=False)
    balances_after = nx.get_edge_attributes(lightning.network.graph, "balance")
    for edge in balances_before.keys():
        assert_eq(balances_before[edge], balances_after[edge])
    for edge in balances_after.keys():
        assert_eq(balances_before[edge], balances_after[edge])

def test_update_balances_ln():
    test_update_balances_pay_enough_money_ln()
    test_update_balances_pay_not_enough_money_ln()
    test_update_balances_reverse_ln()

def test_simulation_with_ln_different_coins(coins_for_parties):
    simulation1 = make_example_simulation_ln(seed = 12345, coins_for_parties = coins_for_parties)
    results1 = simulation1.run()
    lightning1 = simulation1.payment_method
    plainbitcoin1 = lightning1.plain_bitcoin
    simulation2 = make_example_simulation_ln(seed = 12345, coins_for_parties = coins_for_parties)
    lightning2 = simulation2.payment_method
    plainbitcoin2 = lightning2.plain_bitcoin
    results2 = simulation2.run()
    assert results1 == results2
    assert simulation1 == simulation2
    for party in plainbitcoin1.coins.keys():
        assert_eq(plainbitcoin1.coins[party], plainbitcoin2.coins[party])
    for sender in lightning1.network.graph.nodes():
        for receiver in lightning1.network.graph.nodes():
            if lightning1.network.graph.get_edge_data(sender, receiver) == None:
                assert lightning2.network.graph.get_edge_data(sender, receiver) == None
            else:
                assert_eq(
                    lightning1.network.graph[sender][receiver]['balance'],
                    lightning2.network.graph[sender][receiver]['balance']
                )
    simulation3 = make_example_simulation_ln(seed = 123, coins_for_parties = coins_for_parties)
    assert simulation1 != simulation3

def test_simulation_with_ln():
    for coins_for_parties in ['max_value', 'small_value', 'random']:
        test_simulation_with_ln_different_coins(coins_for_parties)



if __name__ == "__main__":
    test_LN()
    test_get_payment_fee_ln()
    test_update_balances_ln()
    test_get_payment_options_ln()
    test_do_ln()
    test_choose_payment_method_ln()
    test_simulation_with_ln()
    print("Success")
