from .nino_module import NinoModule
import cv2

import os
import sys

sys.path.append(os.path.abspath('../..'))
import nino.bbox.layout as ly
import nino.textrec.textrec as tr
import nino.textrec.lineseg as ls

class TextRecognition(NinoModule):
    def __init__(self, model=None):
        self.process_name = 'text_recognition'
        self.ls = ls.LineSegmentor(downsample=8)
        self.tr = tr.TextRecognizer(path=model)

    def apply_module(self, nino_obj):
        # first convert layout into bboxes
        img = cv2.imread(nino_obj.get_initial_input(), cv2.IMREAD_GRAYSCALE)
        note = ly.parse(nino_obj.get('layout_analysis'), image=img)

        # then simply visit the damn note
        self.ls.visit(note)
        self.tr.visit(note)

        # finally record the note object
        nino_obj.set(self.process_name, note)

    def get_requirements_list(self):
        return ['layout_analysis'] # these strings should really be in a config file, or simply a class property

text_recognition = TextRecognition
