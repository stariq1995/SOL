class Resource:
    def __init__(self, name, capacity, owner):
        self.name = name
        self.capacity = capacity
        self.owner = owner

    def __repr__(self):
        return "Resource(name={}, capacity={})".format(self.name,
                                                       self.capacity)

    def __eq__(self, other):
        if not isinstance(other, Resource):
            raise TypeError('Expected Resource type for comparison')
        return self.name == other.name and self.owner == other.owner

    def __hash__(self):
        return hash((self.name, self.owner))

#
# class CompoundResource:
#     def __init__(self, resname, links, nodes):
#         self.name = resname
#         self.links = links
#         self.nodes = nodes
#
#     def __add__(self, o):
#         if not isinstance(CompoundResource, o):
#             raise TypeError(
#                 'Expected another ComboResource in the add operation')
#         if self.resname != o.resname:
#             raise AttributeError('Expected same resource name in add')
#         return CompoundResource(self.resname, self.links + o.links,
#                                 self.nodes + o.nodes)
#
#     def capacity(self, topology, mode='max'):
#         capacities = []
#         for node in self.nodes:
#             capacities.append(topology.getResources(node)[self.name].capacity)
#         for link in self.links:
#             capacities.append(topology.getResources(link)[self.name].capacity)
#         if mode == 'max':
#             return max(capacities)
#         elif mode == 'sum':
#             return sum(capacities)
#         elif mode == 'min':
#             return min(capacities)