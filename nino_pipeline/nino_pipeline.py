import importlib
from nino_exceptions import RequirementException
from nino_utils import *
# from nino_modules import exmodule1
from nino_modules import nino_module
# from nino_modules import exmodule2

class NinoPipeline(object):

    def __init__(self, nino_obj, modules):
        self.nino_obj = nino_obj
        if modules is not None and len(modules) > 0:
            if isinstance(modules[0], str):
                self.modules = request_default_objects(modules)
            else:
                self.modules = modules

    def run(self):
        for module in self.modules:
            try:
                print("Current Module: ", type(module).__name__)
                self.check_requirements(module)
                module.apply_module(self.nino_obj)
            except RequirementException:
                print("Unsatisfied Requirements! Aborting...")
                break

    def check_requirements(self, module):
        requirements_list = module.get_requirements_list()
        for r in requirements_list:
            if not self.nino_obj.check_requirement(r):
                raise RequirementException
