"""from nino_pipeline import NinoPipeline
from nino_object import NinoObject

################################################################################
def print_outs():
    # Get the original image
    print("Initial Input: ", no.get_initial_input())

    # Get individual outputs from each module
    print("Output of exmodule1: ", no.get('exmodule1'))
    print("Output of exmodule2: ", no.get('exmodule2'))

    # Get the final output of the pipeline
    print("Final Output: ", no.get_final_out(), "\n")
################################################################################
# 1st Way: use defaults for all modules
################################################################################

# A sequential list of modules to be used
modules = [
  "exmodule1",
  "exmodule2"
]

# Create NinoObject with a name and initial image
no = NinoObject("#1", 123) # 123 => placeholder for image

# Create NinoPipeline with modules and NinoObject
np = NinoPipeline(no, modules)
np.run() # Start processsing

print_outs()

################################################################################
# 2nd Way: use modules with custom parameters
################################################################################
module_names = [
  "exmodule1",
  "exmodule2"
]

# Import required modules
from nino_utils import *
class_references = request_class_references(module_names)

# Create objects of modules using custom parameters. Even default ones should be
# created.
modules = [
    class_references['exmodule1'](), # Default values for "exmodule1"
    class_references['exmodule2']("param1", "param2") # Custom parameters for "exmodule2"
]

# Create NinoObject with a name and initial image
no = NinoObject("#1", 123) # 123 => placeholder for image

# Create NinoPipeline with modules and NinoObject
np = NinoPipeline(no, modules)
np.run() # Start processsing

print_outs()
"""