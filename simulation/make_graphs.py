import pickle
import matplotlib.pyplot as plt
from tqdm import tqdm
from simulation import ROUNDS_RANDOM_PAYMENTS


# power law
num_successful_payments_elmo_power_law = 0
num_failures_elmo_power_law = 0
sum_fees_elmo_power_law = 0
sum_delays_elmo_power_law = 0
num_onchain_elmo_power_law = 0
num_new_virtual_channel_elmo_power_law = 0
num_new_channel_elmo_power_law = 0
num_pay_elmo_power_law = 0

num_successful_payments_donner_power_law = 0
num_failures_donner_power_law = 0
sum_fees_donner_power_law = 0
sum_delays_donner_power_law = 0
num_onchain_donner_power_law = 0
num_new_virtual_channel_donner_power_law = 0
num_new_channel_donner_power_law = 0
num_pay_donner_power_law = 0

num_successful_payments_lvpc_power_law = 0
num_failures_lvpc_power_law = 0
sum_fees_lvpc_power_law = 0
sum_delays_lvpc_power_law = 0
num_onchain_lvpc_power_law = 0
num_new_virtual_channel_lvpc_power_law = 0
num_new_channel_lvpc_power_law = 0
num_pay_lvpc_power_law = 0

num_successful_payments_ln_power_law = 0
num_failures_ln_power_law = 0
sum_fees_ln_power_law = 0
sum_delays_ln_power_law = 0
num_onchain_ln_power_law = 0
num_new_channel_ln_power_law = 0
num_pay_ln_power_law = 0

for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):

    with open("results_power_lawElmo_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_elmo_power_law:
        payments_elmo_power_law = pickle.load(pickled_file_elmo_power_law)
    num_successful_payments_elmo_power_law_round = 0
    sum_fees_elmo_power_law_round = 0
    sum_delays_elmo_power_law_round = 0
    num_onchain_elmo_power_law_round = 0
    num_new_virtual_channel_elmo_power_law_round = 0
    num_new_channel_elmo_power_law_round = 0
    num_pay_elmo_power_law_round = 0
    for payment in payments_elmo_power_law:
        if payment[0] == True:
            num_successful_payments_elmo_power_law_round += 1
            sum_fees_elmo_power_law_round += payment[2]
            sum_delays_elmo_power_law_round += payment[3]
            if payment[1]['kind'] == 'onchain':
                num_onchain_elmo_power_law_round += 1
            elif payment[1]['kind'] == 'Elmo-open-channel':
                num_new_channel_elmo_power_law_round += 1
            elif payment[1]['kind'] == 'Elmo-open-virtual-channel':
                num_new_virtual_channel_elmo_power_law_round += 1
            elif payment[1]['kind'] == 'Elmo-pay':
                num_pay_elmo_power_law_round += 1
            else:
                pass

    num_failures_elmo_power_law_round = len(payments_elmo_power_law) - num_successful_payments_elmo_power_law_round

    num_successful_payments_elmo_power_law += num_successful_payments_elmo_power_law_round
    num_failures_elmo_power_law += num_failures_elmo_power_law_round
    sum_fees_elmo_power_law += sum_fees_elmo_power_law_round
    sum_delays_elmo_power_law += sum_delays_elmo_power_law_round
    num_onchain_elmo_power_law += num_onchain_elmo_power_law_round
    num_new_virtual_channel_elmo_power_law += num_new_virtual_channel_elmo_power_law_round
    num_new_channel_elmo_power_law += num_new_channel_elmo_power_law_round
    num_pay_elmo_power_law += num_pay_elmo_power_law_round
    num_failures_elmo_power_law += num_failures_elmo_power_law_round


    with open("results_power_lawDonner_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_donner_power_law:
        payments_donner_power_law = pickle.load(pickled_file_donner_power_law)
    num_successful_payments_donner_power_law_round = 0
    sum_fees_donner_power_law_round = 0
    sum_delays_donner_power_law_round = 0
    num_onchain_donner_power_law_round = 0
    num_new_virtual_channel_donner_power_law_round = 0
    num_new_channel_donner_power_law_round = 0
    num_pay_donner_power_law_round = 0
    for payment in payments_donner_power_law:
        if payment[0] == True:
            num_successful_payments_donner_power_law_round += 1
            sum_fees_donner_power_law_round += payment[2]
            sum_delays_donner_power_law_round += payment[3]
            if payment[1]['kind'] == 'onchain':
                num_onchain_donner_power_law_round += 1
            elif payment[1]['kind'] == 'Donner-open-channel':
                num_new_channel_donner_power_law_round += 1
            elif payment[1]['kind'] == 'Donner-open-virtual-channel':
                num_new_virtual_channel_donner_power_law_round += 1
            elif payment[1]['kind'] == 'Donner-pay':
                num_pay_donner_power_law_round += 1
            else:
                pass

    num_failures_donner_power_law_round = len(payments_donner_power_law) - num_successful_payments_donner_power_law_round

    num_successful_payments_donner_power_law += num_successful_payments_donner_power_law_round
    num_failures_donner_power_law += num_failures_donner_power_law_round
    sum_fees_donner_power_law += sum_fees_donner_power_law_round
    sum_delays_donner_power_law += sum_delays_donner_power_law_round
    num_onchain_donner_power_law += num_onchain_donner_power_law_round
    num_new_virtual_channel_donner_power_law += num_new_virtual_channel_donner_power_law_round
    num_new_channel_donner_power_law += num_new_channel_donner_power_law_round
    num_pay_donner_power_law += num_pay_donner_power_law_round
    num_failures_donner_power_law += num_failures_donner_power_law_round

    with open("results_power_lawLVPC_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_lvpc_power_law:
        payments_lvpc_power_law = pickle.load(pickled_file_lvpc_power_law)
    num_successful_payments_lvpc_power_law_round = 0
    sum_fees_lvpc_power_law_round = 0
    sum_delays_lvpc_power_law_round = 0
    num_onchain_lvpc_power_law_round = 0
    num_new_virtual_channel_lvpc_power_law_round = 0
    num_new_channel_lvpc_power_law_round = 0
    num_pay_lvpc_power_law_round = 0
    for payment in payments_lvpc_power_law:
        if payment[0] == True:
            num_successful_payments_lvpc_power_law_round += 1
            sum_fees_lvpc_power_law_round += payment[2]
            sum_delays_lvpc_power_law_round += payment[3]
            if payment[1]['kind'] == 'onchain':
                num_onchain_lvpc_power_law_round += 1
            elif payment[1]['kind'] == 'LVPC-open-channel':
                num_new_channel_lvpc_power_law_round += 1
            elif payment[1]['kind'] == 'LVPC-open-virtual-channel':
                num_new_virtual_channel_lvpc_power_law_round += 1
            elif payment[1]['kind'] == 'LVPC-pay':
                num_pay_lvpc_power_law_round += 1
            else:
                pass

    num_failures_lvpc_power_law_round = len(payments_lvpc_power_law) - num_successful_payments_lvpc_power_law_round

    num_successful_payments_lvpc_power_law += num_successful_payments_lvpc_power_law_round
    num_failures_lvpc_power_law += num_failures_lvpc_power_law_round
    sum_fees_lvpc_power_law += sum_fees_lvpc_power_law_round
    sum_delays_lvpc_power_law += sum_delays_lvpc_power_law_round
    num_onchain_lvpc_power_law += num_onchain_lvpc_power_law_round
    num_new_virtual_channel_lvpc_power_law += num_new_virtual_channel_lvpc_power_law_round
    num_new_channel_lvpc_power_law += num_new_channel_lvpc_power_law_round
    num_pay_lvpc_power_law += num_pay_lvpc_power_law_round
    num_failures_lvpc_power_law += num_failures_lvpc_power_law_round

    with open("results_power_lawln_" + "{}".format(i) + ".pickle", 'rb') as pickled_file_ln_power_law:
        payments_ln_power_law = pickle.load(pickled_file_ln_power_law)
    num_successful_payments_ln_power_law_round = 0
    sum_fees_ln_power_law_round = 0
    sum_delays_ln_power_law_round = 0
    num_onchain_ln_power_law_round = 0
    num_new_channel_ln_power_law_round = 0
    num_pay_ln_power_law_round = 0
    for payment in payments_ln_power_law:
        if payment[0] == True:
            num_successful_payments_ln_power_law_round += 1
            sum_fees_ln_power_law_round += payment[2]
            sum_delays_ln_power_law_round += payment[3]
            if payment[1]['kind'] == 'onchain':
                num_onchain_ln_power_law_round += 1
            elif payment[1]['kind'] == 'ln-open':
                num_new_channel_ln_power_law_round += 1
            elif payment[1]['kind'] == 'ln-pay':
                num_pay_ln_power_law_round += 1
            else:
                pass

    num_failures_ln_power_law_round = len(payments_ln_power_law) - num_successful_payments_ln_power_law_round

    num_successful_payments_ln_power_law += num_successful_payments_ln_power_law_round
    num_failures_ln_power_law += num_failures_ln_power_law_round
    sum_fees_ln_power_law += sum_fees_ln_power_law_round
    sum_delays_ln_power_law += sum_delays_ln_power_law_round
    num_onchain_ln_power_law += num_onchain_ln_power_law_round
    num_new_channel_ln_power_law += num_new_channel_ln_power_law_round
    num_pay_ln_power_law += num_pay_ln_power_law_round
    num_failures_ln_power_law += num_failures_ln_power_law_round

print("Onchain Elmo", num_onchain_elmo_power_law)
print("New channel Elmo", num_new_channel_elmo_power_law)
print("New virtual channel Elmo", num_new_virtual_channel_elmo_power_law)
print("Pay Elmo", num_pay_elmo_power_law)
print("Fees Elmo:", sum_fees_elmo_power_law)
print("Delays Elmo: ", sum_delays_elmo_power_law)

print("Onchain Donner", num_onchain_donner_power_law)
print("New channel Donner", num_new_channel_donner_power_law)
print("New virtual channel Donner", num_new_virtual_channel_donner_power_law)
print("Pay Donner", num_pay_donner_power_law)
print("Fees Donner:", sum_fees_donner_power_law)
print("Delays Donner: ", sum_delays_donner_power_law)

print("Onchain LVPC", num_onchain_lvpc_power_law)
print("New channel LVPC", num_new_channel_lvpc_power_law)
print("New virtual channel LVPC", num_new_virtual_channel_lvpc_power_law)
print("Pay LVPC", num_pay_lvpc_power_law)
print("Fees LVPC:", sum_fees_lvpc_power_law)
print("Delays LVPC: ", sum_delays_lvpc_power_law)

print("Onchain Ln", num_onchain_ln_power_law)
print("New channel Ln", num_new_channel_ln_power_law)
print("Pay Ln", num_pay_ln_power_law)
print("Fees Ln:", sum_fees_ln_power_law)
print("Delays Ln: ", sum_delays_ln_power_law)



x_coords_success = [0,1,2,3,4,5,6,7]
payments_bar = [
    num_successful_payments_elmo_power_law, num_failures_elmo_power_law,
    num_successful_payments_donner_power_law, num_failures_donner_power_law,
    num_successful_payments_lvpc_power_law, num_failures_lvpc_power_law,
    num_successful_payments_ln_power_law, num_failures_ln_power_law
]
labels_success = [
    'successul_elmo', 'unsuccessful_elmo', 'successul_donner', 'unsuccessul_donner',
    'successul_lvpc', 'unsuccessful_lvpc', 'successful_ln', 'unsuccessful_ln']

plt.bar(
    x_coords_success, payments_bar, tick_label = labels_success, width = 0.8,
    color = ['blue', 'red']
)
plt.ylabel("Number of payments")
plt.show()

x_coords_cost = [0, 1, 2, 3]
labels_cost = ['Elmo', 'Donner', 'LVPC', 'Ln']

cost_bar = [
    sum_fees_elmo_power_law, sum_fees_donner_power_law,
    sum_fees_lvpc_power_law, sum_fees_ln_power_law
]

plt.bar(x_coords_cost, cost_bar, tick_label = labels_cost, width=0.5)
plt.ylabel("Cost")
plt.show()

x_coords_delay = [0, 1, 2, 3]
labels_delay = ['Elmo', 'Donner', 'LVPC', 'Ln']

delay_bar = [
    sum_delays_elmo_power_law, sum_delays_donner_power_law,
    sum_delays_lvpc_power_law, sum_delays_ln_power_law
]

plt.bar(x_coords_delay, delay_bar, tick_label = labels_delay, width=0.5)
plt.ylabel("Delay")
plt.show()
