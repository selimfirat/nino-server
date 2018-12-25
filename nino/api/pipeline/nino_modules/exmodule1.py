from .nino_module import NinoModule
class exmodule1(NinoModule):

    def __init__(self):
        self.process_name = "exmodule1"

    def apply_module(self, nino_obj):
        # Do crazy stuff with the object.
        # ...
        # End of crazy stuff
        output_of_crazy_stuff = "I am crazy output #1";
        nino_obj.set(self.process_name, output_of_crazy_stuff)

        # Writer must assert process_name is set

    def get_requirements_list(self):
        return [] # Empty list, no requirements
