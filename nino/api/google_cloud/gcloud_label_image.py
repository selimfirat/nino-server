import argparse
import io, os
from google.cloud import vision
from google.cloud.vision import types

# TODO: convert labels into specified format
# params: note_path, bottom, top, left, right
# - crop image. request with cropped image, return "label"

def get_labels(filein, fileout):
    client = vision.ImageAnnotatorClient()

    file_name = os.path.join(os.path.dirname(__file__), filein)

    # Loads the image into memory
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    # Performs label detection on the image file
    response = client.label_detection(image=image)
    labels = response.label_annotations

    # print('Labels:')
    # for label in labels:
    #     print(label.description)

    # print(labels)

    return labels


if __name__ == '__main__':
    # enviroment var GOOGLE_APPLICATION_CREDENTIALS is visible in this process & it's children
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.dirname(os.path.abspath(__file__))+"/apikey.json"

    # extract text & equations
    parser = argparse.ArgumentParser()
    parser.add_argument('detect_file', help='The image')
    parser.add_argument('-out_file', help='Optional output file', default=0)
    args = parser.parse_args()

    get_labels(args.detect_file, args.out_file)




