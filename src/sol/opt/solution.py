# coding: utf-8

from sol.opt.app import App

ALLAPPS = 'allapps'


class Solution(object):
    """
    Stores the essential basics of the Optmization solution
    """

    def __init__(self, opt, apps, with_paths=False):
        # Extract paths (pptc), resource loads, binary variables, (app obectives?)
        if isinstance(apps, App):
            apps = [apps]
        self.objectives = {app.name: opt.get_solved_objective(app) for app in apps}
        self.objectives[ALLAPPS] = opt.get_solved_objective()
        if with_paths:
            self.paths = opt.get_paths()
        else:
            self.paths = None
        self.binvars = {
            'nodes': opt.get_enabled_nodes(),
            'links': opt.get_enabled_links(),
        }
        # self.loads = opt.get_load_dict()

    def __repr__(self):
        return "Sol Solution, objective: {}".format(self.objectives[ALLAPPS])

    def to_dict(self):
        """
        Return a JSON-compatible representation of the solution object as a dictionary
        :return: 
        """
        # TODO: bring back paths and loads once we speed up their retrieval
        # json_load_arr = []
        # for resource in self.loads:
        #     json_load_arr.append({
        #         'resource': resource,
        #         'elements': [{
        #             'element': element,
        #             'load': self.loads[resource][element]
        #         } for element in self.loads[resource]]
        #     })
        d = {
            'objectives': [{'application': k, 'objective': v} for k, v in self.objectives.items()],
            # 'paths': self.paths.json_list(),
            'enabled': self.binvars,
            # 'loads': json_load_arr
        }
        if self.paths is not None:
            d['paths'] = self.paths.json_list()
        return d
