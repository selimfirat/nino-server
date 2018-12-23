from nino_object import NinoObject
from nino_utils import *
from RequestHandleThread import RequestHandleThread
from queue import Queue
import M
import multiprocessing
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

import socket

def main():
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

    def server():
        host = socket.gethostname()   # get local machine name
        port = 5432  # Make sure it's within the > 1024 $$ <65535 range

        s = socket.socket()
        s.bind((host, port))

        print("Listening to client requests...")
        while True:
            s.listen(1)
            client_socket, adress = s.accept()
            print("Connection from: " + str(adress))
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                  break
                print('Data got from client: ' + data)
                #t = RequestHandleThread(data, modules)
                #t.start()
                def handle(recieved_data):
                    data = recieved_data.split("@*@NINO@*@") #0->note_name 1->filename 2->username
                    print(data)
                    initial_image_str = data[1]
                    username = data[2]
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
                    for m in modules:
                        output_of_module = no.get(m.process_name)
                        output_of_module.save(path_request + m.process_name, "JPEG")
                    final_out = no.get_final_out()
                    final_out.save(path_request + "FINAL", "JPEG")

                handle(data)



        s.close()

    server()

    # Get the original image
    print("Initial Input: ", no.get_initial_input())
    # Get individual outputs from each module
    print("Output of exmodule1: ", no.get('PreprocessModule'))
    print("Output of exmodule2: ", no.get('RegionSegmentationModule'))
    # Get the final output of the pipeline
    print("Final Output: ", no.get_final_out(), "\n")

if __name__ == "__main__":
    main()
