# maybe Network should extend a class "LabeledGraph"
import numpy as np
import networkx as nx

class Network:

    def __init__(self, nr_vertices):
        self.multigraph = nx.empty_graph(nr_vertices, create_using=nx.MultiDiGraph)
        self.edge_id = 0

    def add_node(self, node):
        self.multigraph.add_node(node)
        # do we need this method? If we need it we need sth like a convention that a new vertex gets the number len(self.vertices).

    def add_channel(self, idA, balA, idB, balB):
        self.multigraph.add_weighted_edges_from([(idA, idB, balA)], weight = "balanceSender", edge_id = self.edge_id)
        self.multigraph.add_weighted_edges_from([(idB, idA, balB)], weight = "balanceSender", edge_id = self.edge_id)
        self.edge_id += 1
        
    # TODO: find library function that does this for us
    def find_all_paths(self, start, end, amount, path = [], edge_ids = []):
        # networkX and jgrapht are the only python libs I found that support multigraphs
        # I didn't find any function that does exactly what we want (with the cutoff for the amount, most search either shortest path or all (simple) paths)
        # nx all_simple_paths is inconvenient as it gives only the nodes of the paths not the edges of the multigraph
        # all_paths = nx.all_simple_paths(self.multigraph, start, end)


        # TODO: use adjacency_list or simply directly self.edges (2nd option slower)
        vertices = self.multigraph.nodes()
        nr_vertices = len(vertices)
        path = path + [start]
        if start == end:
            # no set anymore as it would give a type error for tuples
            return [(path, edge_ids)]
        # TODO: remove the next if, if we're too slow
        if start not in vertices:
            raise ValueError("start not in vertices")
        paths = []
        # TODO: use adjacency_list
        for vertex in vertices:
            try:
                # this gives a dict which has as many elements (dicts again) as the number of channels from start to vertex.
                # In these dicts is the edge_id and the balance of the sender
                edges_from_start_to_vertex = self.multigraph[start][vertex]
                for edge_nr in edges_from_start_to_vertex.keys():
                    edge_id = edges_from_start_to_vertex[edge_nr]['edge_id']
                    # We check whether the balance is high enough and we want only simple paths.
                    if edges_from_start_to_vertex[edge_nr]['balanceSender'] >= amount and vertex not in path:
                        newpaths = self.find_all_paths(vertex, end, amount, path, edge_ids + [edge_id])
                        for i in range(len(newpaths)):
                            newpath, new_edge_ids = newpaths[i]
                            paths.append((newpath, new_edge_ids))
            except KeyError:
                continue
        return paths

    def __eq__(self, other):
        return (self.edges == other.edges and self.vertices == other.vertices)

    # TODO: remove vertices, edges ...