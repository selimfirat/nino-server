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
    def __init__(self, maxd=5, font=cv2.FONT_HERSHEY_SIMPLEX, scale=1, 
                 drawbox=False, clearbox=False, printtext=False, printeqn=False):
        self.maxd = maxd
        self.font = font
        self.scale = scale
        self.drawbox = drawbox # whether to draw boundaries around boxes
        self.clearbox = clearbox # whether to clear boxes before writing text on them
        self.printtext = printtext
        self.printeqn = printeqn
    def visit_note(self, bbox, res=None, *args, **kwargs):
        self.depth = 0
        if res is None:
            res = np.zeros(bbox.annot.image.shape + (3,))
        super(BBoxDisplay, self).visit_note(bbox, res, *args, **kwargs)
        return res
    def visit_children(self, bbox, *args, **kwargs):
        self.depth += 1
        super(BBoxDisplay, self).visit_children(bbox, *args, **kwargs)
        self.depth -= 1
    def visit_bbox(self, bbox, res, *args, **kwargs):
        if self.drawbox:
            thickness = self.maxd - self.depth
            if thickness < 2:
                thickness = 2
            res = cv2.rectangle(res, (bbox.rect.x0-thickness, bbox.rect.y1+thickness), 
                                     (bbox.rect.x1+thickness, bbox.rect.y0-thickness), (127,0,0), thickness)
        self.visit_children(bbox, res, *args, **kwargs)
    def visit_eqn(self, bbox, res, *args, **kwargs):
        if self.printeqn:
            return self.visit_text(bbox, res, *args, **kwargs)
        return self.visit_bbox(bbox, res, *args, **kwargs)
    def visit_text(self, bbox, res, *args, **kwargs):
        self.visit_bbox(bbox, res, *args, **kwargs)
        if not bbox.children and self.printtext:
            thickness = 2
            
            if self.clearbox: # fill box white before writing text
                res = cv2.rectangle(res, (bbox.rect.x0, bbox.rect.y1), 
                                         (bbox.rect.x1, bbox.rect.y0), (255,255,255), -1)
            
            # compute scale of text to fit in box
            baseline, _ = cv2.getTextSize(str(bbox.annot), self.font, self.scale, thickness)
            scale = self.scale * min([(bbox.rect.x1 - bbox.rect.x0)/baseline[0],
                                      (bbox.rect.y1 - bbox.rect.y0)/baseline[1]])
            
            # compute lower left corner of text
            height = bbox.rect.y1 - bbox.rect.y0
            if self.clearbox:
                height = cv2.getTextSize(str(bbox.annot), self.font, scale, thickness)[0][1]
            
            # write text
            res = cv2.putText(res, str(bbox.annot), (bbox.rect.x0, bbox.rect.y0+height), 
                              self.font, scale, (0,0,0), thickness)

class BBoxPrinter(BBoxVisitor):
    def print_note(note):
        return BBoxPrinter().visit(note)
    def read_note(string):
        return eval(string) # VERY dangerous
    def visit_bbox(self, bbox, ident='BBox', arglist='annot=None', *args, **kwargs):
        children = self.visit_children(bbox, *args, init=[], op=(lambda a, b: a + [b]))
        children = '[%s]' % ', '.join(children)
        return '%s(rect=%s, c=%s, image=None, %s, children=%s)' % (ident, bbox.rect, bbox.c, arglist, children)
    def visit_note(self, bbox, *args, **kwargs):
        children = self.visit_children(bbox, *args, init=[], op=(lambda a, b: a + [b]))
        children = '[%s]' % ', '.join(children)
        return 'Note(rect=%s, image=None, children=%s)' % (bbox.rect, children)
    def visit_text(self, bbox, ident='TextBBox', arglist=None, *args, **kwargs):
        text = '' if bbox.annot.text == [''] else '\\n' % bbox.annot.text
        if arglist is None:
            arglist = 'text=\'\'\'%s\'\'\'' % text
        return self.visit_bbox(bbox, ident=ident, arglist=arglist, *args, **kwargs)
    def visit_line(self, bbox, *args, **kwargs):
        return self.visit_text(bbox, ident='LineBBox', *args, **kwargs)
    def visit_word(self, bbox, *args, **kwargs):
        return self.visit_text(bbox, ident='WordBBox', *args, **kwargs)
    def visit_eqn(self, bbox, *args, **kwargs):
        return self.visit_bbox(bbox, ident='EqnBBox', arglist='latex=\'\'\'%s\'\'\''%bbox.annot.text[0], *args, **kwargs)