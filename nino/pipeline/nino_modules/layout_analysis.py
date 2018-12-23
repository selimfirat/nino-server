from .nino_module import NinoModule
import xmltodict
import os

class LayoutAnalysis(NinoModule):

    def __init__(self):
        self.process_name = "layout_analysis"
        self.counter = 1 # a file indicator in case of parallel calls to the apply module

    def apply_module(self, nino_obj):
        
        localImagePath = nino_obj.get_initial_input()
        outputFile = "out" + str(self.counter) + ".xml"
        
        os.system("bash ./tesseract-recognize-docker --only-layout --layout-level=region " + localImagePath + " " + outputFile)
        
        with open(outputFile) as fd:
            layout = xmltodict.parse(fd.read())
        
        os.system("rm " + outputFile)
        self.counter += 1
        nino_obj.set(self.process_name, layout)

    def get_requirements_list(self):
        return []

layout_analysis = LayoutAnalysis

# Test part. Run via "python layout_analysis.py"
if __name__ == "__main__":
    import json
    # Importing NinoObject I WANT TO SLEEP
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
    
    layout_module = LayoutAnalysis()
    no = NinoObject("#1", "../../notes/original_images/13722_1071460739534917_2979984990414340900_n.jpg") 
    layout_module.apply_module(no)
    print(json.dumps(no.get("layoutanalysis")))