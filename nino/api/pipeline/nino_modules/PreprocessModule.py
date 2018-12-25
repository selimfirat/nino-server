from .nino_module import NinoModule
from .. import M
class PreprocessModule(NinoModule):

    def __init__(self):
        self.process_name = M.PREPROCESS

    def apply_module(self, nino_obj):
        print("Preprocessing...")
        output = "Preprocessed Output";
        nino_obj.set(self.process_name, output)

    def get_requirements_list(self):
        return []
