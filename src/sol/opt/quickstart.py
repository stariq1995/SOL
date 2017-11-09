# coding=utf-8
from numpy import array

from sol.utils.const import NODES, LINKS, EpochComposition, ERR_UNKNOWN_MODE, Fairness, MBOXES
from sol.utils.exceptions import InvalidConfigException
from sol.utils.logger import logger
from .gurobiwrapper import OptimizationGurobi

__all__ = ['from_app']


def from_app(topo, app, network_config):
    """
    Create an optimization from a single application.

    :param topo: the network topology
    :param app: the application
    :param network_config: operator-specified network config. (see :py:class:`sol.NetworkConfig`)
    :return: the optimization object
    """
    # Start the optimization
    opt = OptimizationGurobi(topo, app.pptc)
    # Extract the capacities from all links and nodes
    node_caps = {node: topo.get_resources(node) for node in topo.nodes()}
    link_caps = {link: topo.get_resources(link) for link in topo.links()}

    # "Consume" network resources. For each resource, generate resource constraints by considering the
    # load imposed by all traffic classes
    for r in app.resource_cost:
        mode, cost_val, cost_func = app.resource_cost[r]
        if mode == NODES or mode == MBOXES:
            capacities = {n: node_caps[n][r] for n in node_caps if r in node_caps[n]}
        elif mode == LINKS:
            capacities = {n: link_caps[n][r] for n in link_caps if r in link_caps[n]}
        else:
            raise InvalidConfigException(ERR_UNKNOWN_MODE % ('resource owner', mode))
        # Avoid using cost funcs for now
        # TODO: figure out efficient way of evaluating cost funcs
        opt.consume(app.pptc.tcs(), r, capacities, mode, cost_val, None)

    # Cap the resources, if caps were given
    if network_config is not None:
        caps = network_config.get_caps()
        if caps is not None:
            logger.debug('Capping resources')
            for r in caps.resources():
                opt.cap(r, caps.caps(r))

    # And add any other constraints the app might desire
    opt.add_named_constraints(app)

    # Add a single objective
    kwargs = app.obj[2].copy()
    kwargs.update(dict(varname=app.name, tcs=app.obj_tc))
    epoch_objs = opt.add_single_objective(app.obj[0], *app.obj[1], **kwargs)
    # For a single app the composition is not particularly important or sensitive,
    # so we go with reasonable defaults of worst across epochs.
    # Weight of 1 means no other apps, use full objective value as is.
    opt.compose_objectives(array([epoch_objs]), EpochComposition.WORST, Fairness.WEIGHTED, array([1]))
    return opt
