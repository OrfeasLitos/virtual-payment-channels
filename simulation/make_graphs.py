import pickle
from turtle import width
import matplotlib.pyplot as plt

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

pickled_file_elmo = open("example_results_Elmo.pickle", 'rb')
payments_elmo = pickle.load(pickled_file_elmo)
num_successful_payments_elmo = 0
sum_fees_elmo = 0
for payment in payments_elmo:
    if payment[0] == True:
        num_successful_payments_elmo += 1
        sum_fees_elmo += payment[2]

print(sum_fees_elmo)
num_unsuccessful_payments_elmo = len(payments_elmo) - num_successful_payments_elmo

x_coords_success = [0,1,2,3]
payments_bar = [
    num_successful_payments_ln, num_unsuccessful_payments_ln,
    num_successful_payments_elmo, num_unsuccessful_payments_elmo
]
labels_success = ['successul_ln', 'unsuccessful_ln', 'successul_elmo', 'unsuccessul_elmo']

plt.bar(x_coords_success, payments_bar, tick_label = labels_success, width = 0.8, color = ['blue', 'red'])
plt.ylabel("Number of payments")
plt.show()

x_coords_cost = [0, 1]
labels_cost = ['Ln', 'Elmo']

cost_bar = [
    sum_fees_ln, sum_fees_elmo,
]

plt.bar(x_coords_cost, cost_bar, tick_label = labels_cost, width=0.5)
plt.ylabel("Cost")
plt.show()
