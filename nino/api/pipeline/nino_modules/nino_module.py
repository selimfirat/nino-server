import abc

class NinoModule(object):

    """
    It is subclass writer's responsibility to make sure every parameter has a
    default value in __init__.
    """
    def __init__(self):
        pass

    @abc.abstractmethod
    def apply_module(self, nino_obj):
        pass

    @abc.abstractmethod
    def get_requirements_list(self):
        pass
