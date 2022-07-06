# maybe Network should extend a class "LabeledGraph"
import math
import copy
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
            'channels_underneath' : path, 'channels_above': []}
        )
        # TODO: maybe also struct.
        reversed_path = copy.copy(path)
        if reversed_path is not None:
            reversed_path.reverse()
        edge_B_to_A = (
            idB, idA,
            {'balance': balB, 'locked_coins' : 0, 'cost' : UNIT_COST,
            'channels_underneath' : list(reversed(path)) if path is not None else None,
            'channels_above': []}
        )
        return [edge_A_to_B, edge_B_to_A]

    def update_channels(self, idA, balA, idB, balB, path):
        if path is not None:
            for i in range(len(path) - 1):
                sender = path[i]
                receiver = path[i+1]
                # TODO: think if pair is ok here or if we want all the information of the channels to be stored.
                # review: let's update this on an as-needed basis
                # TODO: add our spot in path above. (in dictionary : source, sink, path_index)
                # TODO: store set.
                # TODO: maybe store it just on one edge as an optimization.
                self.graph[sender][receiver]['channels_above'].append((idA, idB))
                self.graph[receiver][sender]['channels_above'].append((idA, idB))
        self.edge_id += 1

    def close_channel(self, idA, idB):
        # TODO: maybe convention idA < idB
        # this is only for adjusting the lower level channels of the channels above, e.g.
        # for A - > E via A -> C, C -> E and A - > C via A -> B, B -> C and A -> C closes,
        # then channels underneath A -> E before closing are A -> C, C -> E,  and afterwards
        # A -> B, B -> C, C -> E.
        # TODO: test this!!!
        # TODO: try to simplify this
        # TODO: rename layer to channel
        # TODO: rename underneath to below
        channels_underneath_reference_layer_A_to_B = self.graph[idA][idB]['channels_underneath']
        channels_underneath_reference_layer_B_to_A = self.graph[idB][idA]['channels_underneath']
        channels_above_reference_layer = self.graph[idA][idB]['channels_above']
        if channels_underneath_reference_layer_A_to_B is not None:
            for channel in channels_above_reference_layer:
                idC, idD = channel
                channels_underneath_upper_layer_C_to_D = self.graph[idC][idD]['channels_underneath']
                channels_underneath_upper_layer_D_to_C = self.graph[idD][idC]['channels_underneath']
                # assume that channel can occur only once in upper layer, i.e. no cycles.
                i = channels_underneath_upper_layer_C_to_D.index(idA)
                j = channels_underneath_upper_layer_C_to_D.index(idB)
                # j = i+1 if ... else i - 1
                #TODO: calculate with length of list.
                k = channels_underneath_upper_layer_D_to_C.index(idA)
                l = channels_underneath_upper_layer_D_to_C.index(idB)
                # TODO: take minimum and exchange i and j if necessary
                if i < j:
                    startpath_C_to_D = self.graph[idC][idD]['channels_underneath'][:i]
                    endpath_C_to_D = self.graph[idC][idD]['channels_underneath'][j+1:]
                    startpath_D_to_C = self.graph[idD][idC]['channels_underneath'][:l]
                    endpath_D_to_C = self.graph[idD][idC]['channels_underneath'][k+1:]
                    self.graph[idC][idD]['channels_underneath'] = startpath_C_to_D + channels_underneath_reference_layer_A_to_B + endpath_C_to_D
                    self.graph[idD][idC]['channels_underneath'] = startpath_D_to_C + channels_underneath_reference_layer_B_to_A + endpath_D_to_C
                else:
                    startpath_C_to_D = self.graph[idC][idD]['channels_underneath'][:j]
                    endpath_C_to_D = self.graph[idC][idD]['channels_underneath'][i+1:]
                    startpath_D_to_C = self.graph[idD][idC]['channels_underneath'][:k]
                    endpath_D_to_C = self.graph[idD][idC]['channels_underneath'][l+1:]
                    self.graph[idC][idD]['channels_underneath'] = startpath_C_to_D + channels_underneath_reference_layer_B_to_A + endpath_C_to_D
                    self.graph[idD][idC]['channels_underneath'] = startpath_D_to_C + channels_underneath_reference_layer_A_to_B + endpath_D_to_C
            #adjust channels above.
            path = channels_underneath_reference_layer_A_to_B
            for i in range(len(path)-1):
                # remove old channel above
                if (idA, idB) in self.graph[path[i]][path[i+1]]['channels_above']:
                    self.graph[path[i]][path[i+1]]['channels_above'].remove((idA, idB))
                    self.graph[path[i+1]][path[i]]['channels_above'].remove((idA, idB))
                # TODO: remove if after using Set.
                if (idB, idA) in self.graph[path[i]][path[i+1]]['channels_above']:
                    self.graph[path[i]][path[i+1]]['channels_above'].remove((idB, idA))
                    self.graph[path[i+1]][path[i]]['channels_above'].remove((idB, idA))
                # add new channels above.
                self.graph[path[i]][path[i+1]]['channels_above'] += channels_above_reference_layer
                self.graph[path[i+1]][path[i]]['channels_above'] += channels_above_reference_layer

        else:  # we're closing an onchain channel
            # Question: if we have virtual channel A -> C via A -> B and B -> C (both opened onchain),
            # and we close A -> B. Should channels_underneath[A -> B] == None and channels_above[B->C] == []?
            for channel in channels_above_reference_layer:
                idC, idD = channel
                self.graph[idC][idD]['channels_underneath'] = None
                self.graph[idD][idC]['channels_underneath'] = None
        # TODO: handle balances.
        self.remove_channel(idA, idB)      


