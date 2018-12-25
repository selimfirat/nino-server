"""from threading import Thread
from .nino_pipeline import NinoPipeline
from .nino_object import NinoObject
from .nino_utils import *
from PIL import Image
import pathlib

dir_notes = "../../../notes/"
class RequestHandleThread(Thread):
    # Implement producer consumer here.
    def __init__(self, data, modules):
        Thread.__init__(self)
        self.name self.data = data.split("@*@NINO@*@") #0->note_name 1->filename 2->username
        print(self.data)
        self.modules = modules

    def run(self):
        initial_image_str = self.data[1]
        username = self.data[2]
        request_id = "REQUEST_ID"
        print('Running request for user ' + username +
        " with request id #" + request_id)

        initial_image = Image.open(dir_notes + 'original_images/' + initial_image_str)

        # Create NinoObject with a name and initial image
        no = NinoObject(request_id, initial_image) # Temp solution for com

        # Create NinoPipeline with modules and NinoObject
        np = NinoPipeline(no, self.modules)
        np.run() # Start processsing

        ########################################################################
        # For debuging purposes
        ########################################################################
        path_request = dir_notes + 'processed_images/' + request_id + '/'
        pathlib.Path(path_request).mkdir(parents=True, exist_ok=True)
        for m in self.modules:
            output_of_module = no.get(m.process_name)
            output_of_module.save(path_request + m.process_name, "JPEG")
        final_out = no.get_final_out()
        final_out.save(path_request + "FINAL", "JPEG")
        ########################################################################

        print("Done processing!")
        # TODO: SEND PIC BACK TO USER XD
"""