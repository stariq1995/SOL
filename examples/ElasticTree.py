# coding=utf-8

if __name__ == '__main__':
    pass
# def addPowerConstraint(self, nodeConsumption, edgeConsumption,
# normalize=True):
# """
#
# :param self.cplexprob:
# :param nodeConsumption:
# :param edgeConsumption:
# :param normalize:
# """
# self.cplexprob.variables.add(names=['linkpower', 'switchpower'],
# lb=[0, 0])
# v = self.cplexprob.variables.get_names()
# varindex = dict(izip(v, range(len(v))))
# norm = sum(nodeConsumption.values()) + sum(edgeConsumption.values()) \
# if normalize else 1
# self.cplexprob.linear_constraints.add([cplex.SparsePair(
# [varindex['binedge_{}_{}'.format(a, b)] for (a, b) in
# edgeConsumption] +
# [varindex['linkpower']],
# [edgeConsumption[link] / norm for link in edgeConsumption] + [-1])],
# rhs=[0], senses=['E'])
# self.cplexprob.linear_constraints.add([cplex.SparsePair(
#         [varindex['binnode_{}'.format(u)] for u in nodeConsumption] +
#         [varindex['switchpower']],
#         [nodeConsumption[node] / norm for node in nodeConsumption] + [-1])],
#                                           rhs=[0], senses=['E'])