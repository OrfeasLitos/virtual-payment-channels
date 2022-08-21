import pickle

pickled_file_ln = open("example_results_ln.pickle", 'rb')
payments_ln = pickle.load(pickled_file_ln)
print(payments_ln)

pickled_file_elmo = open("example_results_Elmo.pickle", 'rb')
payments_elmo = pickle.load(pickled_file_elmo)
print(payments_elmo)