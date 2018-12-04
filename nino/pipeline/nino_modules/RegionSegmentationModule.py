from .nino_module import NinoModule
import M

class RegionSegmentationModule(NinoModule):

    def __init__(self, param1="p1", param2="p2"):
        self.process_name = M.REGION_SEGMENTATION
        self.param1 = param1
        self.param2 = param2

    def apply_module(self, nino_obj):
        print("Segmenting Regions with: " + self.param1 + " " + self.param2 + "...")
        output = "Segmented Regions Output"
        nino_obj.set(self.process_name, output)

    def get_requirements_list(self):
        return ["PreprocessModule"]
