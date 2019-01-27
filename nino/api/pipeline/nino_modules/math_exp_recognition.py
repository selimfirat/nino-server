from .nino_module import NinoModule
import cv2, os, sys

import nino.bbox.layout as ly
import nino.mer.mer as mer

class MathExpRecognition(NinoModule):
    def __init__(self):
        self.process_name = 'math_exp_recognition'
        self.mer = mer.MathExpRecognizer()

    def apply_module(self, nino_obj):
        note = nino_obj.get('text_recognition')
        self.mer.visit(note)
        nino_obj.set(self.process_name, note)

    def get_requirements_list(self):
        return 'text_recognition' # getting note object from text recognizer

math_exp = MathExpRecognition
