import sys
import os

sys.path.append(os.path.abspath('..')) # hacky

from nino_pipeline import NinoPipeline
from nino_object import NinoObject

from nino.bbox.bbox import BBoxEncoder

def print_outs():
    # Get the original image
    print("Initial Input: ", no.get_initial_input())

    # Get individual outputs from each module
    print("Output of layout analysis: ", no.get('layout_xanalysis'))
    print("Output of text recognition: ", json.dumps(BBoxEncoder().default(no.get('text_recognition')), indent=2))

    # Get the final output of the pipeline
    print("Final Output: ", no.get_final_out(), "\n")

module_names = [
    'layout_analysis',
    'text_recognition'
]

# Import required modules
from nino_utils import *
class_references = request_class_references(module_names)

# Create objects of modules using custom parameters. Even default ones should be
# created.
modules = [
    class_references['layout_analysis'](), # Default values for "exmodule1"
    class_references['text_recognition']('../models/trec_words_100.pt') # Custom parameters for "exmodule2"
]

# Create NinoObject with a name and initial image
path = sys.argv[1]
no = NinoObject("#1", path)

# Create NinoPipeline with modules and NinoObject
np = NinoPipeline(no, modules) # Fails because filenames and class names do not match
np.run() # Start processsing

# from nino_modules.layout_analysis import LayoutAnalysis
# from nino_modules.text_recognition import TextRecognition

# la = LayoutAnalysis()
# tr = TextRecognition()

# la.apply_module(no)
# tr.apply_module(no)

print_outs()
