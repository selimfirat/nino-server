# dependencies: google-cloud, google-api-core

import argparse
from enum import Enum
import io, os
from google.cloud import vision, storage
from google.cloud.vision import types
from PIL import Image, ImageDraw

# paragraph_dict = {
#   "text": par_text,
#   "left": par_left,
#   "top": par_top,
#   "right": par_right,
#   "bottom": par_bottom
# }


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3  # paragraph
    WORD = 4
    SYMBOL = 5


def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y], None, color)
    return image


def get_document_bounds(image_file, feature):
    """Returns document bounds given an image."""
    client = vision.ImageAnnotatorClient()

    bounds = []

    with io.open(image_file, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    # Collect specified feature bounds by enumerating all document features
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if (feature == FeatureType.SYMBOL):
                            bounds.append(symbol.bounding_box)

                    if (feature == FeatureType.WORD):
                        bounds.append(word.bounding_box)

                if (feature == FeatureType.PARA):
                    bounds.append(paragraph.bounding_box)

            if (feature == FeatureType.BLOCK):
                bounds.append(block.bounding_box)

        if (feature == FeatureType.PAGE):
            bounds.append(block.bounding_box)

    # The list `bounds` contains the coordinates of the bounding boxes.
    return bounds


def render_doc_text(filein, fileout, bottom=0, top=0, left=0, right=0):
    image = Image.open(filein)
    width, height = image.size

    # convert str args into int
    bottom = int(bottom)
    top = int(top)
    left = int(left)
    right = int(right)

    if (top < bottom) and (left < right) and right <= width and bottom <= height:
        # there is at least 1 pixel that is specified, so image is cropped to include only that pixels
        image = image.crop((left, top, right, bottom))

    bounds = get_document_bounds(filein, FeatureType.PAGE)
    draw_boxes(image, bounds, 'blue')
    bounds = get_document_bounds(filein, FeatureType.PARA)
    draw_boxes(image, bounds, 'red')
    bounds = get_document_bounds(filein, FeatureType.WORD)
    draw_boxes(image, bounds, 'yellow')

    # if fileout is not 0:
    #     image.save(fileout)
    # else:
    #     image.show()

    # TODO: rather than drawing the bounding boxes, return bounds in specified format


if __name__ == '__main__':
    # enviroment var GOOGLE_APPLICATION_CREDENTIALS is visible in this process & it's children
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.dirname(os.path.abspath(__file__))+"/apikey.json"

    # extract text & equations
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='The image for text detection.')
    parser.add_argument('-output_file', help='Optional output for saving the image with boxes')
    parser.add_argument('-bottom', help='Optional bottom coordinate', default=0)
    parser.add_argument('-top', help='Optional top  coordinate', default=0)
    parser.add_argument('-left', help='Optional left  coordinate', default=0)
    parser.add_argument('-right', help='Optional right  coordinate', default=0)
    args = parser.parse_args()

    render_doc_text(args.input_file, args.output_file, args.bottom, args.top, args.left, args.right)
