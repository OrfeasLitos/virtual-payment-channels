# maybe Network should extend a class "LabeledGraph"

class Network:

    def __init__(self, nr_vertices):
        self.vertices = list(range(nr_vertices))
        self.edges = []

    def add_vertex(self, vertex):
        self.vertices.append(vertex)

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_edge(self, edge):
        for e in self.edges:
            # if the first part of edge is sth like "PlainBitcoin" it's ok, if it is a Bitcoin object I would need to overwrite the __eq__ method.
            if e == edge:
                return e
        return None
    
    def add_edge_with_check(self, edge):
        """
        This method only adds an edge if it doesn't exist yet.
        """
        if self.get_edge(edge) == None:
            self.add_edge(edge)

    # TODO: remove vertices, edges ...
