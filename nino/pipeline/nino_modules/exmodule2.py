from .nino_module import NinoModule

class exmodule2(NinoModule):

    def __init__(self, param1="p1", param2="p2"):
        self.process_name = "exmodule2"
        self.param1 = param1
        self.param2 = param2

    def apply_module(self, nino_obj):
        # Do crazy stuff with the object.
        # ...
        # End of crazy stuff
        output_of_crazy_stuff = "I am crazy output #2: " + self.param1 + " " + self.param2;
        nino_obj.set(self.process_name, output_of_crazy_stuff)

        # Writer must assert process_name is set

    def get_requirements_list(self):
        return ["exmodule1"] # Requires "exmodule1"
