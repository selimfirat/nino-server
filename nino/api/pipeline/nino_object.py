class NinoObject(object):

    def __init__(self, name, original_image):
        self.name = name
        self.final_out = None
        self.process_output_dict = dict()
        self.set("INITIAL_INPUT", original_image)

    def set(self, process_name, process_output):
        self.process_output_dict[process_name] = process_output
        self.final_out = process_name

    def get(self, process_name):
        return self.process_output_dict[process_name]

    def get_initial_input(self):
        return self.get("INITIAL_INPUT")

    def get_final_out(self):
        return self.get(self.final_out)

    def check_requirement(self, process_name):
        return process_name in self.process_output_dict
