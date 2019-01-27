# Given note object annotated with text and equations, returns image displaying the text &c. on the original image

from .nino_module import NinoModule
import cv2

import nino.bbox.utils as ut

class NoteDisplay(NinoModule):
    def __init__(self, model=None):
        self.process_name = 'note_display'
        self.disp = ut.BBoxDisplay() # possibly add settings

    def apply_module(self, nino_obj):
        # receive note
        note = nino_obj.get('text_recognition') # can also receive the note from layout analysis
        
        # produce image
        img = self.disp.visit(note, res=note.image)

        # record image
        nino_obj.set(self.process_name, img)

    def get_requirements_list(self):
        return ['text_recognition']