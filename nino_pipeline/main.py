from nino_pipeline import NinoPipeline
from nino_object import NinoObject
from nino_utils import *
from RequestThread import RequestThread
from queue import Queue
import M

################################################################################
# Module Writer Responsiblities:
# - Include name of the module to M.py
# - Extend nino_module, set self.process_name = M.{YOUR_MODULE_NAME}
# - Implement apply_module and get_requirements_list functions
# - Make sure each parameter has a default value in __init__
# - Make sure apply_module sets appropriate tags
################################################################################
# TODO: Connect server to handle request.
# TODO: Apply composite to nino_pipeline.
# TODO: Update examples

load_modules()
crs = get_class_references()

# Android sends two images to the server:
# * Warped paper/board etc.
# * Original image taken

# Default pipeline: Preprocess the image(s) and extract region images for text/
# figures/math equations etc.

# - All pipelines use the following template:
#   Preprocess -> Apply module spesific enhancement or information extraction
# - Mind that you are creating objects of module classes here, hence the "()".
# - For default parameters, use: crs[M.{YOUR_MODULE_NAME}]().
modules = [
    crs[M.PREPROCESS](),
    crs[M.REGION_SEGMENTATION]("param1", "param2")
]

request_queue = Queue() # Queue for request that are yet to be handled
nino_object_queue = Queue() # Queue for nino objects that were created by handling requests

# Move this to a seperate thread so that this is done for each request. Make the
# thread infinetly listen to requests
t = RequestThread(nino_object_queue, modules)
t.start()
t.join()

# Move this to a seperate infinite thread to wait for created nino objects.
no = nino_object_queue.get()

# Get the original image
print("Initial Input: ", no.get_initial_input())
# Get individual outputs from each module
print("Output of exmodule1: ", no.get('PreprocessModule'))
print("Output of exmodule2: ", no.get('RegionSegmentationModule'))
# Get the final output of the pipeline
print("Final Output: ", no.get_final_out(), "\n")
