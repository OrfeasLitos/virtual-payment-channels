from custom_elmo_lvpc_donner import Custom_Elmo_LVPC_Donner

class Elmo(Custom_Elmo_LVPC_Donner):
    # The fee is the same for all payment methods. It is paid on channel
    # opening and is set to 20 times the LN fee. The rationale is that the
    # intermediaries have to be compensated for keeping their coins locked.
    # review: With current values, it is `fee_intermediary = 20*base_fee = 20000`.
    # review: If it is easy, we should also add an equivalent to the
    # review: proportional `ln_fee` and make it 20 times that of ln as well.
    # review: Re delays, I believe it's safe to use the same delay for all
    # payment methods. in LN it is multiplied by the number of hops, in all
    # other constructions it isn't, as in all of them parties pay each other
    # directly in their virtual channel.
    def __init__(
        self, nr_players, max_coins = 2000000000000000,
        bitcoin_fee = 1000000, bitcoin_delay = 3600,
        coins_for_parties = "max_value", base_fee = 20000,
        fee_rate = 0.0004, opening_transaction_size = 121.5,
        elmo_pay_delay = 0.05, elmo_new_virtual_channel_delay = 0.05
    ):
        super().__init__(
            "Elmo", nr_players, max_coins, bitcoin_fee, bitcoin_delay,  coins_for_parties, base_fee,
            fee_rate, opening_transaction_size, elmo_pay_delay, elmo_new_virtual_channel_delay
        )
