# dependencies: google-cloud, google-api-core

import argparse
from enum import Enum
import io, os
from google.cloud import vision
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


def crop_image(filein, bottom=0, top=0, left=0, right=0):
    """Reads image in filein & returns cropped PIL.Image"""
    image = Image.open(filein)
    width, height = image.size

    # convert str args into int
    bottom = int(bottom)
    top = int(top)
    left = int(left)
    right = int(right)

    if (top < bottom) and (left < right) and right <= width and bottom <= height:
        # there is at least 1 pixel that is specified, so image is cropped to include only those pixels
        image = image.crop((left, top, right, bottom))

    return image


def PIL_to_gcloud_image(PILImage):
    """Converts PIL.Image to google.cloud.vision.types.Image"""

    buffer = io.BytesIO()
    PILImage.save(buffer, "PNG")

    content = buffer.getvalue()
    gcloudImage = types.Image(content=content)

    return gcloudImage


def feature_dict(text, bound, confidence=0):
    left = bound.vertices[0].x
    right = bound.vertices[1].x
    top = bound.vertices[0].y
    bottom = bound.vertices[2].y

    if confidence == 0:
        dictionary = {
                "text": text,
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom
        }
    else:
        dictionary = {
                "text": text,
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
                "confidence": confidence
            }

    return dictionary


class GCloudRepository:
    def __init__(self, apikey=None):
        if apikey is not None:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = apikey
        else:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.dirname(os.path.abspath(__file__))+"/apikey.json"

        self.client = vision.ImageAnnotatorClient()

    def process_document(self, image_file, feature, bottom=0, top=0, left=0, right=0):
        """Returns document bounds given an image."""

        bounds = []

        image = crop_image(image_file, bottom, top, left, right)
        image = PIL_to_gcloud_image(image)

        response = self.client.document_text_detection(image=image)
        document = response.full_text_annotation

        breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType

        paragraphs = []
        lines = []

        # Collect specified feature bounds & texts by enumerating all document features
        for page in document.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    para = ""
                    line = ""
                    for word in paragraph.words:
                        for symbol in word.symbols:
                            line += symbol.text
                            if symbol.property.detected_break.type == breaks.SPACE:
                                line += ' '
                            if symbol.property.detected_break.type == breaks.EOL_SURE_SPACE:
                                line += ' '
                                lines.append(feature_dict(line, symbol.bounding_box))
                                para += line
                                line = ''
                            if symbol.property.detected_break.type == breaks.LINE_BREAK:
                                lines.append(feature_dict(line, symbol.bounding_box))
                                para += line
                                line = ''

                            if (feature == FeatureType.SYMBOL):
                                bounds.append(symbol.bounding_box)

                            # symbol.confidence

                        if (feature == FeatureType.WORD):
                            bounds.append(word.bounding_box)

                    paragraphs.append(feature_dict(para, paragraph.bounding_box, paragraph.confidence))

                    if (feature == FeatureType.PARA):
                        bounds.append(paragraph.bounding_box)

                if (feature == FeatureType.BLOCK):
                    bounds.append(block.bounding_box)

            if (feature == FeatureType.PAGE):
                bounds.append(block.bounding_box)

        return paragraphs, lines, bounds

    def get_labels(self, filein, fileout):

        file_name = os.path.join(os.path.dirname(__file__), filein)

        # Loads the image into memory
        with io.open(file_name, 'rb') as image_file:
            content = image_file.read()

        image = types.Image(content=content)

        # Performs label detection on the image file
        response = self.client.label_detection(image=image)
        labels = response.label_annotations

        # print('Labels:')
        # for label in labels:
        #     print(label.description)

        # print(labels)

        return labels


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


def render_bounding_box_drawing(filein, fileout, bottom=0, top=0, left=0, right=0):
    """Returns document bounds given an image via get_document_bounds."""
    image = Image.open(filein)

    # convert str args into int
    bottom = int(bottom)
    top = int(top)
    left = int(left)
    right = int(right)

    gcloud = GCloudRepository()

    p, l, bounds = gcloud.process_document(filein, FeatureType.PAGE, bottom, top, left, right)
    draw_boxes(image, bounds, 'blue')
    p, l, bounds = gcloud.process_document(filein, FeatureType.PARA, bottom, top, left, right)
    draw_boxes(image, bounds, 'red')
    p, l, bounds = gcloud.process_document(filein, FeatureType.WORD, bottom, top, left, right)
    draw_boxes(image, bounds, 'yellow')

    if fileout is not 0:
        image.save(fileout)
    else:
        image.show()


if __name__ == '__main__':
    # example call : python3 gcloud.py deneme2.png -output_file output_word.png -top 00 -left 00 -bottom 800 -right 800

    # enviroment var GOOGLE_APPLICATION_CREDENTIALS is visible in this process & it's children
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.dirname(os.path.abspath(__file__))+"/apikey.json"

    # extract text & equations
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='The image for text detection.')
    # parser.add_argument('-output_file', help='Optional output for saving the image with boxes')
    parser.add_argument('-bottom', help='Optional bottom coordinate', default=0)
    parser.add_argument('-top', help='Optional top  coordinate', default=0)
    parser.add_argument('-left', help='Optional left  coordinate', default=0)
    parser.add_argument('-right', help='Optional right  coordinate', default=0)
    args = parser.parse_args()

    gcloud = GCloudRepository()

    paragraphs, lines, bounds = gcloud.process_document(args.input_file, args.bottom, args.top, args.left, args.right)

    print(paragraphs)
