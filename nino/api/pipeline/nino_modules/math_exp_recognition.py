from .nino_module import NinoModule
import cv2, os, sys

sys.path.append(os.path.abspath('../..'))
import nino.abhyasa.digitRecognition.track2 as dr
import nino.bbox.layout as ly


class MathExpRecognition(NinoModule):
    def __init__(self):
        self.process_name = 'math_exp_recognition'
        self.mer = dr.MathExpRecognizer()

    def apply_module(self, nino_obj):
        # first convert layout into bboxes
        img = cv2.imread(nino_obj.get_initial_input(), cv2.IMREAD_GRAYSCALE)
        note = ly.parse(nino_obj.get('layout_analysis'), image=img)

        # self.mer.visit(note)
        # TODO: Talk with @Ata about how to integrate this into visit(note)!
        self.mer.visit_eqn(nino_obj.get_initial_input(), img)

        # finally record the note object
        nino_obj.set(self.process_name, note)

    def get_requirements_list(self):
        return  # TODO: I really have no idea about what this is about


math_exp = MathExpRecognition
