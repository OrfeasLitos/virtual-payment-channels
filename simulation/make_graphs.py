import pickle
from turtle import width
import matplotlib.pyplot as plt

"""
pickled_file_ln = open("example_results_ln.pickle", 'rb')
payments_ln = pickle.load(pickled_file_ln)
num_successful_payments_ln = 0
sum_fees_ln = 0
for payment in payments_ln:
    if payment[0] == True:
        num_successful_payments_ln += 1
        sum_fees_ln += payment[2]

print(sum_fees_ln)
num_unsuccessful_payments_ln = len(payments_ln) - num_successful_payments_ln

"""

pickled_file_elmo = open("example_results_Elmo.pickle", 'rb')
payments_elmo = pickle.load(pickled_file_elmo)
num_successful_payments_elmo = 0
sum_fees_elmo = 0
sum_delays_elmo = 0
for payment in payments_elmo:
    if payment[0] == True:
        num_successful_payments_elmo += 1
        sum_fees_elmo += payment[2]
        sum_delays_elmo += payment[3]

print(sum_fees_elmo)
print("Delays: ", sum_delays_elmo)
num_unsuccessful_payments_elmo = len(payments_elmo) - num_successful_payments_elmo
print(num_successful_payments_elmo)

pickled_file_donner = open("example_results_Donner.pickle", 'rb')
payments_donner = pickle.load(pickled_file_donner)
num_successful_payments_donner = 0
sum_fees_donner = 0
sum_delays_donner = 0
for payment in payments_donner:
    if payment[0] == True:
        num_successful_payments_donner += 1
        sum_fees_donner += payment[2]
        sum_delays_donner += payment[3]

print(sum_fees_donner)
print("Delays: ", sum_delays_donner)
num_unsuccessful_payments_donner = len(payments_donner) - num_successful_payments_donner
print(num_successful_payments_donner)

pickled_file_lvpc = open("example_results_LVPC.pickle", 'rb')
payments_lvpc = pickle.load(pickled_file_lvpc)
num_successful_payments_lvpc = 0
sum_fees_lvpc = 0
sum_delays_lvpc = 0
for payment in payments_lvpc:
    if payment[0] == True:
        num_successful_payments_lvpc += 1
        sum_fees_lvpc += payment[2]
        sum_delays_lvpc += payment[3]

print(sum_fees_lvpc)
print("Delays: ", sum_delays_lvpc)
num_unsuccessful_payments_lvpc = len(payments_lvpc) - num_successful_payments_lvpc
print(num_successful_payments_lvpc)

x_coords_success = [0,1,2,3,4,5]
payments_bar = [
    num_successful_payments_elmo, num_unsuccessful_payments_elmo,
    num_successful_payments_donner, num_unsuccessful_payments_donner,
    num_successful_payments_lvpc, num_unsuccessful_payments_lvpc
]
labels_success = [
    'successul_elmo', 'unsuccessful_elmo', 'successul_donner', 'unsuccessul_donner',
    'successul_lvpc', 'unsuccessful_lvpc']

plt.bar(x_coords_success, payments_bar, tick_label = labels_success, width = 0.8, color = ['blue', 'red'])
plt.ylabel("Number of payments")
plt.show()

x_coords_cost = [0, 1, 2]
labels_cost = ['Elmo', 'Donner', 'LVPC']

cost_bar = [
    sum_fees_elmo, sum_fees_donner, sum_fees_lvpc
]

plt.bar(x_coords_cost, cost_bar, tick_label = labels_cost, width=0.5)
plt.ylabel("Cost")
plt.show()

x_coords_delay = [0, 1, 2]
labels_delay = ['Elmo', 'Donner', 'LVPC']

delay_bar = [
    sum_delays_elmo, sum_delays_donner, sum_delays_lvpc
]

plt.bar(x_coords_delay, delay_bar, tick_label = labels_delay, width=0.5)
plt.ylabel("Delay")
plt.show()
