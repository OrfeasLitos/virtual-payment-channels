import pickle
import matplotlib.pyplot as plt

pickled_file_ln = open("example_results_ln.pickle", 'rb')
payments_ln = pickle.load(pickled_file_ln)
num_successful_payments_ln = 0
for i in range(len(payments_ln)):
    if payments_ln[i][0] == True:
        num_successful_payments_ln += 1

num_unsuccessful_payments_ln = len(payments_ln) - num_successful_payments_ln

pickled_file_elmo = open("example_results_Elmo.pickle", 'rb')
payments_elmo = pickle.load(pickled_file_elmo)
num_successful_payments_elmo = 0
for i in range(len(payments_elmo)):
    if payments_elmo[i][0] == True:
        num_successful_payments_elmo += 1

num_unsuccessful_payments_elmo = len(payments_elmo) - num_successful_payments_elmo

x_coords = [0,1,2,3]
payments_bar = [
    num_successful_payments_ln, num_unsuccessful_payments_ln,
    num_successful_payments_elmo, num_unsuccessful_payments_elmo
]
labels = ['successul_ln', 'unsuccessful_ln', 'successul_elmo', 'unsuccessul_elmo']

plt.bar(x_coords, payments_bar, tick_label = labels, width = 0.8, color = ['blue', 'red'])
plt.show()
