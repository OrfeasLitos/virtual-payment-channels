# maybe Network should extend a class "LabeledGraph"
import math
import networkx as nx


UNIT_COST = 1

class Network:

    def __init__(self, nr_vertices):
        self.graph = nx.empty_graph(nr_vertices, create_using=nx.DiGraph)
        self.edge_id = 0

    def get_new_edges(self, idA, balA, idB, balB, method_data):
        assert(balA > 0 or balB > 0)
        edges = [
            (idA, idB, {'balance': balA, 'cost' : UNIT_COST}),
            (idB, idA, {'balance': balB, 'cost' : UNIT_COST})
        ]
        return edges

    def update_channels(self, idA, balA, idB, balB, method_data):
        pass

    def add_channel(self, idA, balA, idB, balB, method_data = None):
        edges = self.get_new_edges(idA, balA, idB, balB, method_data)
        self.graph.add_edges_from(edges)
        self.edge_id += 1
        self.update_channels(idA, balA, idB, balB, method_data)

    def remove_channel(self, idA, idB):
        edges = [(idA, idB) ,(idB, idA)]
        self.graph.remove_edges_from(edges)

    def get_weight_function(self, amount):
        """
        This function returns the weight function we use in the following.
        The balance acts as a threshold.
        If the amount is bigger than the balance the weight is math.inf, otherwise it is 1.
        """
        # TODO: Check whether higher order functions make some optimizations harder.
        def weight_function(sender, receiver, edge_attributes):
            if edge_attributes['balance'] >= amount:
                return 1
            return math.inf
        return weight_function

    def find_cheapest_path(self, sender, receiver, amount, fee_intermediary):
        try:
            weight_function = self.get_weight_function(amount)
            cheapest_path = nx.shortest_path(self.graph, sender, receiver, weight_function)
            # this is a check that the cheapest path really can be used for a transaction
            # (cheapest path could still have distance math.inf)
            for i in range(len(cheapest_path)-1):
                sender = cheapest_path[i]
                receiver = cheapest_path[i+1]
                if self.graph.get_edge_data(sender, receiver)['balance'] < amount + (len(cheapest_path) - 1) * fee_intermediary:
                    return None
            return len(cheapest_path) - 1, cheapest_path
        except nx.exception.NetworkXNoPath:
            return None

    def get_harmonic_centrality(self):
        return nx.harmonic_centrality(self.graph)

# review: why do we need a separate Network class for Elmo?
class Network_Elmo(Network):
    def __init__(self, nr_vertices):
        super().__init__(nr_vertices)

    def get_new_edges(self, idA, balA, idB, balB, path):
        # convention: path goes from A to B (makes it easier to think about it in close channel)
        assert(balA > 0 or balB > 0)
        edge_A_to_B = (
            idA, idB,
            {'balance': balA, 'locked_coins' : 0, 'cost' : UNIT_COST,
            'channels_below' : path, 'channels_above': []}
        )
        # TODO: maybe also struct.
        edge_B_to_A = (
            idB, idA,
            {'balance': balB, 'locked_coins' : 0, 'cost' : UNIT_COST,
            'channels_below' : list(reversed(path)) if path is not None else None,
            'channels_above': []}
        )
        return [edge_A_to_B, edge_B_to_A]

    def update_channels(self, idA, balA, idB, balB, path):
        if path is not None:
            for i in range(len(path) - 1):
                sender = path[i]
                receiver = path[i+1]
                # TODO: maybe store it just on one edge as an optimization.
                self.graph[sender][receiver]['channels_above'].append({idA, idB})
                self.graph[receiver][sender]['channels_above'].append({idA, idB})
        self.edge_id += 1
    
    def lock_coins(self, path, lock_value):
        # Question: are coins on the first channel in the path also locked?
        # review: yes, the sender locks these coins in its base channel as well.
        for i in range(len(path) - 1):
            sender = path[i]
            receiver = path[i+1]
            if self.graph[sender][receiver]['balance'] < lock_value:
                for j in range(i):
                    sender = path[j]
                    receiver = path[j+1]
                    self.graph[sender][receiver]['balance'] += lock_value
                    self.graph[sender][receiver]['locked_coins'] -= lock_value
                raise ValueError
            self.graph[sender][receiver]['balance'] -= lock_value
            self.graph[sender][receiver]['locked_coins'] += lock_value

    def undo_locking(self, path, lock_value):
        # TODO: maybe make it similarly as for update_balances and include this with an operator
        # and boolean variable in lock.
        # undoes just one lock, doesn't free all locked money.
        for i in range(len(path) - 1):
            sender = path[i]
            receiver = path[i+1]
            self.graph[sender][receiver]['balance'] += lock_value
            self.graph[sender][receiver]['locked_coins'] -= lock_value

    def cooperative_close_channel(self, idA, idB):
        # TODO: maybe convention idA < idB
        channels_below_reference_channel_A_to_B = self.graph[idA][idB]['channels_below']
        channels_below_reference_channel_B_to_A = self.graph[idB][idA]['channels_below']
        channels_above_reference_channel = self.graph[idA][idB]['channels_above']
        # if onchain channel raise ValueError
        if channels_below_reference_channel_A_to_B is None:
            raise ValueError
        for channel in channels_above_reference_channel:
            idC, idD = channel
            channels_below_upper_channel_C_to_D = self.graph[idC][idD]['channels_below']
            # assume that channel can occur only once in upper layer, i.e. no cycles.
            i = channels_below_upper_channel_C_to_D.index(idA)
            # review: Can i be 0? Does the below work then?
            # It should, because if i = 0 then channels_below_upper_channel_C_to_D[i-1] gives the last element,
            # which shouldn't be idB, since then C -> D would be A -> B and D -> D is above A -> B.
            # tested in test_coop_close_channel_first_virtual_layer_one_layer_above
            j = i - 1 if channels_below_upper_channel_C_to_D[i-1] == idB else i+1
            is_right_party_closing = channels_below_upper_channel_C_to_D[i-1] == idB
            j = i - 1 if is_right_party_closing else i + 1
            # review: this is a big improvement in the logic. Has it been thoroughly tested for equivalence with the old one?
            # I've checked the logic and it passed all previous tests for channel_closing,
            # tested in test_coop_close_channel_first_virtual_layer_one_layer_above
            (first_index, second_index) = (j, i) if is_right_party_closing else (i, j)
            path_length_C_to_D = len(channels_below_upper_channel_C_to_D)
            second_index_reverse = path_length_C_to_D - 1 - first_index
            first_index_reverse = path_length_C_to_D - 1 - second_index
            startpath_C_to_D = self.graph[idC][idD]['channels_below'][:first_index]
            endpath_C_to_D = self.graph[idC][idD]['channels_below'][second_index + 1:]
            startpath_D_to_C = self.graph[idD][idC]['channels_below'][:first_index_reverse]
            endpath_D_to_C = self.graph[idD][idC]['channels_below'][second_index_reverse + 1:]
            self.graph[idC][idD]['channels_below'] = (
                startpath_C_to_D + 
                (list(reversed(channels_below_reference_channel_A_to_B)) if is_right_party_closing else channels_below_reference_channel_A_to_B) + 
                endpath_C_to_D
            )
            self.graph[idD][idC]['channels_below'] = (
                startpath_D_to_C +
                (list(reversed(channels_below_reference_channel_B_to_A)) if is_right_party_closing else channels_below_reference_channel_B_to_A) +
                endpath_D_to_C
            )
        #adjust channels above.
        path = channels_below_reference_channel_A_to_B
        for i in range(len(path)-1):
            # remove old channel above
            self.graph[path[i]][path[i+1]]['channels_above'].remove({idA, idB})
            self.graph[path[i+1]][path[i]]['channels_above'].remove({idA, idB})
            # add new channels above.
            self.graph[path[i]][path[i+1]]['channels_above'] += channels_above_reference_channel
            self.graph[path[i+1]][path[i]]['channels_above'] += channels_above_reference_channel
        self.remove_channel(idA, idB) 


    def force_close_channel(self, idA, idB):
        # TODO: maybe convention idA < idB
        # TODO: handle the case that the channel is virtual
        channels_below_reference_channel_A_to_B = self.graph[idA][idB]['channels_below']
        channels_above_reference_channel = self.graph[idA][idB]['channels_above']

        unlocked_coins = {
            (idA, idB) : self.graph[idA][idB]['locked_coins'],
            (idB, idA) : self.graph[idB][idA]['locked_coins']
        }
        self.remove_channel(idA, idB)

        # forceClose channels below
        if channels_below_reference_channel_A_to_B is not None:
            for i in range(len(channels_below_reference_channel_A_to_B) - 1):
                self.force_close_channel(
                    channels_below_reference_channel_A_to_B[i],
                    channels_below_reference_channel_A_to_B[i+1]
                )
    
        for channel_above_reference in channels_above_reference_channel:
            idC, idD = channel_above_reference
            if self.graph.get_edge_data(idC, idD) is None:
                continue
            channels_below_upper = self.graph[idC][idD]['channels_below']
            # TODO: this should work, but doesn't really capture how elmo works.
            # Think of a better way to close channels that are also below the channel above and at onchain-layer.
            for i in range(len(channels_below_upper)-1):
                if self.graph.get_edge_data(channels_below_upper[i], channels_below_upper[i+1]) is not None:
                    previously_unlocked_coins = self.force_close_channel(
                        channels_below_upper[i],
                        channels_below_upper[i+1]
                    )
                    for party, coins in previously_unlocked_coins.items():
                        if party in unlocked_coins:
                            unlocked_coins[party] += coins
                        else:
                            unlocked_coins[party] = coins
            if self.graph.get_edge_data(idC, idD) is not None:
                self.graph[idC][idD]['channels_below'] = None
                self.graph[idD][idC]['channels_below'] = None

        return unlocked_coins
        # TODO: handle balances.

    #TODO: maybe we can optimize that.
    # for simplicity use for now cooperative close for virtual channel
    def close_channel(self, idA, idB):
        if self.graph[idA][idB]['channels_below'] is None:
            self.force_close_channel(idA, idB)

        else:
            self.cooperative_close_channel(idA, idB)
