# maybe Network should extend a class "LabeledGraph"

class Network:

    def __init__(self, nr_vertices):
        self.vertices = list(range(nr_vertices))
        self.edges = set()

    def add_vertex(self, vertex):
        self.vertices.append(vertex)

    def add_edge(self, edge):
        self.edges.add(edge)

    def has_edge(self, edge):
        return edge in self.edges

    # TODO: remove vertices, edges ...
