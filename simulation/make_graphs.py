import pickle
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from simulation import ROUNDS_RANDOM_PAYMENTS

for distribution in tqdm(["power_law", "preferred_receiver", "uniform"]):
    # power law
    num_successful_payments_elmo = 0
    num_payments_elmo = 0
    num_failures_elmo = 0
    sum_fees_elmo = 0
    sum_delays_elmo = 0
    num_onchain_elmo = 0
    num_new_virtual_channel_elmo = 0
    num_new_channel_elmo = 0
    num_pay_elmo = 0

    num_successful_payments_donner = 0
    num_payments_donner = 0
    num_failures_donner = 0
    sum_fees_donner = 0
    sum_delays_donner = 0
    num_onchain_donner = 0
    num_new_virtual_channel_donner = 0
    num_new_channel_donner = 0
    num_pay_donner = 0

    num_successful_payments_lvpc = 0
    num_payments_lvpc = 0
    num_failures_lvpc = 0
    sum_fees_lvpc = 0
    sum_delays_lvpc = 0
    num_onchain_lvpc = 0
    num_new_virtual_channel_lvpc = 0
    num_new_channel_lvpc = 0
    num_pay_lvpc = 0

    num_successful_payments_ln = 0
    num_payments_ln = 0
    num_failures_ln = 0
    sum_fees_ln = 0
    sum_delays_ln = 0
    num_onchain_ln = 0
    num_new_channel_ln = 0
    num_pay_ln = 0

    for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
        with open("results_" + distribution + "Elmo_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_elmo:
            payments_elmo = pickle.load(pickled_file_elmo)

        num_payments_elmo += len(payments_elmo)
        num_successful_payments_elmo_round = 0
        sum_fees_elmo_round = 0
        sum_delays_elmo_round = 0
        num_onchain_elmo_round = 0
        num_new_virtual_channel_elmo_round = 0
        num_new_channel_elmo_round = 0
        num_pay_elmo_round = 0
        for payment in payments_elmo:
            if payment[0] == True:
                num_successful_payments_elmo_round += 1
                sum_fees_elmo_round += payment[2]
                sum_delays_elmo_round += payment[3]
                if payment[1]['kind'] == 'onchain':
                    num_onchain_elmo_round += 1
                elif payment[1]['kind'] == 'Elmo-open-channel':
                    num_new_channel_elmo_round += 1
                elif payment[1]['kind'] == 'Elmo-open-virtual-channel':
                    num_new_virtual_channel_elmo_round += 1
                elif payment[1]['kind'] == 'Elmo-pay':
                    num_pay_elmo_round += 1
                else:
                    pass

        num_failures_elmo_round = len(payments_elmo) - num_successful_payments_elmo_round

        num_successful_payments_elmo += num_successful_payments_elmo_round
        num_failures_elmo += num_failures_elmo_round
        sum_fees_elmo += sum_fees_elmo_round
        sum_delays_elmo += sum_delays_elmo_round
        num_onchain_elmo += num_onchain_elmo_round
        num_new_virtual_channel_elmo += num_new_virtual_channel_elmo_round
        num_new_channel_elmo += num_new_channel_elmo_round
        num_pay_elmo += num_pay_elmo_round
        num_failures_elmo += num_failures_elmo_round


        with open("results_" + distribution + "Donner_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_donner:
            payments_donner = pickle.load(pickled_file_donner)
        num_payments_donner += len(payments_donner)
        num_successful_payments_donner_round = 0
        sum_fees_donner_round = 0
        sum_delays_donner_round = 0
        num_onchain_donner_round = 0
        num_new_virtual_channel_donner_round = 0
        num_new_channel_donner_round = 0
        num_pay_donner_round = 0
        for payment in payments_donner:
            if payment[0] == True:
                num_successful_payments_donner_round += 1
                sum_fees_donner_round += payment[2]
                sum_delays_donner_round += payment[3]
                if payment[1]['kind'] == 'onchain':
                    num_onchain_donner_round += 1
                elif payment[1]['kind'] == 'Donner-open-channel':
                    num_new_channel_donner_round += 1
                elif payment[1]['kind'] == 'Donner-open-virtual-channel':
                    num_new_virtual_channel_donner_round += 1
                elif payment[1]['kind'] == 'Donner-pay':
                    num_pay_donner_round += 1
                else:
                    pass

        num_failures_donner_round = len(payments_donner) - num_successful_payments_donner_round

        num_successful_payments_donner += num_successful_payments_donner_round
        num_failures_donner += num_failures_donner_round
        sum_fees_donner += sum_fees_donner_round
        sum_delays_donner += sum_delays_donner_round
        num_onchain_donner += num_onchain_donner_round
        num_new_virtual_channel_donner += num_new_virtual_channel_donner_round
        num_new_channel_donner += num_new_channel_donner_round
        num_pay_donner += num_pay_donner_round
        num_failures_donner += num_failures_donner_round

        with open("results_" + distribution + "LVPC_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_lvpc:
            payments_lvpc = pickle.load(pickled_file_lvpc)
        num_payments_lvpc += len(payments_lvpc)
        num_successful_payments_lvpc_round = 0
        sum_fees_lvpc_round = 0
        sum_delays_lvpc_round = 0
        num_onchain_lvpc_round = 0
        num_new_virtual_channel_lvpc_round = 0
        num_new_channel_lvpc_round = 0
        num_pay_lvpc_round = 0
        for payment in payments_lvpc:
            if payment[0] == True:
                num_successful_payments_lvpc_round += 1
                sum_fees_lvpc_round += payment[2]
                sum_delays_lvpc_round += payment[3]
                if payment[1]['kind'] == 'onchain':
                    num_onchain_lvpc_round += 1
                elif payment[1]['kind'] == 'LVPC-open-channel':
                    num_new_channel_lvpc_round += 1
                elif payment[1]['kind'] == 'LVPC-open-virtual-channel':
                    num_new_virtual_channel_lvpc_round += 1
                elif payment[1]['kind'] == 'LVPC-pay':
                    num_pay_lvpc_round += 1
                else:
                    pass

        num_failures_lvpc_round = len(payments_lvpc) - num_successful_payments_lvpc_round

        num_successful_payments_lvpc += num_successful_payments_lvpc_round
        num_failures_lvpc += num_failures_lvpc_round
        sum_fees_lvpc += sum_fees_lvpc_round
        sum_delays_lvpc += sum_delays_lvpc_round
        num_onchain_lvpc += num_onchain_lvpc_round
        num_new_virtual_channel_lvpc += num_new_virtual_channel_lvpc_round
        num_new_channel_lvpc += num_new_channel_lvpc_round
        num_pay_lvpc += num_pay_lvpc_round
        num_failures_lvpc += num_failures_lvpc_round

        with open("results_" + distribution + "ln_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_ln:
            payments_ln = pickle.load(pickled_file_ln)
        num_payments_ln += len(payments_ln)
        num_successful_payments_ln_round = 0
        sum_fees_ln_round = 0
        sum_delays_ln_round = 0
        num_onchain_ln_round = 0
        num_new_channel_ln_round = 0
        num_pay_ln_round = 0
        for payment in payments_ln:
            if payment[0] == True:
                num_successful_payments_ln_round += 1
                sum_fees_ln_round += payment[2]
                sum_delays_ln_round += payment[3]
                if payment[1]['kind'] == 'onchain':
                    num_onchain_ln_round += 1
                elif payment[1]['kind'] == 'ln-open':
                    num_new_channel_ln_round += 1
                elif payment[1]['kind'] == 'ln-pay':
                    num_pay_ln_round += 1
                else:
                    pass

        num_failures_ln_round = len(payments_ln) - num_successful_payments_ln_round

        num_successful_payments_ln += num_successful_payments_ln_round
        num_failures_ln += num_failures_ln_round
        sum_fees_ln += sum_fees_ln_round
        sum_delays_ln += sum_delays_ln_round
        num_onchain_ln += num_onchain_ln_round
        num_new_channel_ln += num_new_channel_ln_round
        num_pay_ln += num_pay_ln_round
        num_failures_ln += num_failures_ln_round

    print("Onchain Elmo", num_onchain_elmo)
    print("New channel Elmo", num_new_channel_elmo)
    print("New virtual channel Elmo", num_new_virtual_channel_elmo)
    print("Pay Elmo", num_pay_elmo)
    print("Fees Elmo:", sum_fees_elmo)
    print("Delays Elmo: ", sum_delays_elmo)

    print("Onchain Donner", num_onchain_donner)
    print("New channel Donner", num_new_channel_donner)
    print("New virtual channel Donner", num_new_virtual_channel_donner)
    print("Pay Donner", num_pay_donner)
    print("Fees Donner:", sum_fees_donner)
    print("Delays Donner: ", sum_delays_donner)

    print("Onchain LVPC", num_onchain_lvpc)
    print("New channel LVPC", num_new_channel_lvpc)
    print("New virtual channel LVPC", num_new_virtual_channel_lvpc)
    print("Pay LVPC", num_pay_lvpc)
    print("Fees LVPC:", sum_fees_lvpc)
    print("Delays LVPC: ", sum_delays_lvpc)

    print("Onchain Ln", num_onchain_ln)
    print("New channel Ln", num_new_channel_ln)
    print("Pay Ln", num_pay_ln)
    print("Fees Ln:", sum_fees_ln)
    print("Delays Ln: ", sum_delays_ln)

    color = ['blue']

    x_coords_cost = [0, 1, 2]
    labels_cost = ['Elmo', 'Donner', 'LVPC']

    assert num_payments_elmo == num_payments_donner == num_payments_lvpc

    cutoff_fee = 10**8
    num_payments = num_payments_lvpc
    cost_bar = [
        sum_fees_elmo / num_payments - cutoff_fee, sum_fees_donner / num_payments - cutoff_fee,
        sum_fees_lvpc / num_payments - cutoff_fee
    ]

    plt.bar(
        x_coords_cost, cost_bar, tick_label = labels_cost,
        width=0.5, color=color, bottom=cutoff_fee
    )
    plt.ylabel("Cost")
    plt.title(distribution.replace('_', ' ').title())
    plt.grid(color='grey', linestyle='--', linewidth=1, axis='y', alpha=0.25)
    plt.savefig("Fees_" + distribution + ".png")

    x_coords_delay = [0, 1, 2]
    labels_delay = ['Elmo', 'Donner', 'LVPC']

    cutoff_delay = 2500
    delay_bar = [
        sum_delays_elmo / num_payments - cutoff_delay,
        sum_delays_donner / num_payments - cutoff_delay,
        sum_delays_lvpc / num_payments - cutoff_delay
    ]

    plt.bar(
        x_coords_delay, delay_bar, tick_label = labels_delay,
        width=0.5, color=color, bottom=cutoff_delay
    )
    plt.ylabel("Delay")
    plt.title(distribution.replace('_', ' ').title())
    plt.grid(color='grey', linestyle='--', linewidth=1, axis='y', alpha=0.5)
    plt.savefig("Delays_" + distribution + ".png")
