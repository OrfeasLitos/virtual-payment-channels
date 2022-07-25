from donner import Donner

def make_example_network_donner(fee_intermediary = 1000000):
    donner = Donner(10, fee_intermediary = fee_intermediary)

    donner.network.add_channel(0, 3000000000., 2, 7000000000., None)
    donner.network.add_channel(0, 6000000000., 1, 7000000000., None)
    donner.network.add_channel(1, 4000000000., 4, 8000000000., None)
    donner.network.add_channel(3, 9000000000., 4, 8000000000., None)
    donner.network.add_channel(2, 9000000000., 3, 2000000000., None)
    donner.network.add_channel(1, 10000000000., 2, 8000000000., None)
    donner.network.add_channel(4, 10000000000., 7, 8000000000., None)
    donner.network.add_channel(3, 10000000000., 8, 8000000000., None)
    return donner


def test_get_payment_options_donner():
    donner = make_example_network_donner()
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 300000000.), (0, 3, 2500000000.)]
    value1 = 100000000
    payment_options1 = donner.get_payment_options(0, 3, value1, future_payments)
    assert payment_options1[2]['payment_information']['kind'] == 'Donner-open-virtual-channel'
    payment_information_new_virtual_channel1 = payment_options1[2]['payment_information']

    donner.do(payment_information_new_virtual_channel1)

    value2 = 1000000
    payment_options2 = donner.get_payment_options(0, 8, value2, future_payments)
    assert payment_options2[2]['payment_information']['kind'] == 'Donner-open-virtual-channel'
    payment_information_new_virtual_channel2 = payment_options2[2]['payment_information']

if __name__ == "__main__":
    test_get_payment_options_donner()
    print("Success")