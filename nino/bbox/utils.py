from .bbox import *
from ..utils import imgprep as ip

import cv2

class BBoxNormalizer(BBoxVisitor):
    'Sort child boxes and accumulate their annotations into that of the parent.'
    def visit_text(self, text, **kwargs):
        text.annot.text = []
        text.children.sort(key=lambda b: b.rect.y0)
        self.visit_children(text, parent=text, **kwargs)
    def visit_line(self, line, parent, **kwargs):
        line.annot.text = []
        line.children.sort(key=lambda b: b.rect.x0)
        self.visit_children(line, parent=line, **kwargs)
        parent.annot.text.append(line.annot.text)
    def visit_word(self, word, parent, **kwargs):
        parent.annot.text.append(word.annot.text)

class BBoxDisplay(BBoxVisitor):
    'Generate mask displaying each bbox in a note.'
    def __init__(self):
        self.depth = 0
        self.maxd = 10
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 1
    def visit_note(self, bbox, *args, **kwargs):
        res = np.zeros(bbox.annot.image.shape + (3,))
        super(BBoxDisplay, self).visit_note(bbox, res, *args, **kwargs)
        return res
    def visit_children(self, bbox, *args, **kwargs):
        self.depth += 1
        super(BBoxDisplay, self).visit_children(bbox, *args, **kwargs)
        self.depth -= 1
    def visit_bbox(self, bbox, res, *args, **kwargs):
        thickness = self.maxd - self.depth
        if thickness < 2:
            thickness = 2
        res = cv2.rectangle(res, (bbox.rect.x0, bbox.rect.y1), 
                                 (bbox.rect.x1, bbox.rect.y0), (255,0,0), thickness)
        self.visit_children(bbox, res, *args, **kwargs)
    def visit_word(self, bbox, res, *args, **kwargs):
        self.visit_bbox(bbox, res, *args, **kwargs)
        baseline, _ = cv2.getTextSize(bbox.annot.text, self.font, self.scale, 3)
        scale = self.scale * min([(bbox.rect.x1 - bbox.rect.x0)/baseline[0],
                                  (bbox.rect.y1 - bbox.rect.y0)/baseline[1]])
        res = cv2.putText(res, bbox.annot.text, (bbox.rect.x0, bbox.rect.y0), 
                          self.font, scale, 3)
        