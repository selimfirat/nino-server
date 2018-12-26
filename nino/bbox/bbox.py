# BBox - segments arranged in hierarchy of children, annotated with text, equations or processed images
# (e.g. a figure may be denoised, a line may be straightened etc.)
# Visitors visit this tree of segments in order, processing and annotating each box and possibly creating new children
# E.g. segmentor receives single box and breaks it down into children text, equation and figure segments,
# text recognizer visits each text box, processes its image and writes its text
# the image may also be passed to the visitor through keyword arguments, as well as the parent note

import json
import numpy as np

from ..utils import imgprep as ip
from ..utils.rect import *

# bbox visitor: visits each subclass of bbox, annotates it and possibly returns an output
# a note itself may be a bbox perhaps
class BBoxVisitor:
    def visit(self, bbox, *args, **kwargs):
        return bbox.accept(self, *args, **kwargs)
    def visit_children(self, bbox, *args, **kwargs): # may override this method to update parent after visiting children
        init = None
        op = lambda a, b: b
        if 'init' in kwargs:
            init = kwargs['init']
        if 'op' in kwargs:
            op = kwargs['op']
        res = init
        for b in bbox.children:
            res = op(res, self.visit(b, *args, **kwargs))
        return res
    def visit_bbox(self, bbox, *args, **kwargs): # default
        return self.visit_children(bbox, *args, **kwargs)
    def visit_note(self, bbox, *args, **kwargs):
        return self.visit_bbox(bbox, *args, **kwargs)
    def visit_text(self, bbox, *args, **kwargs):
        return self.visit_bbox(bbox, *args, **kwargs)
    def visit_line(self, bbox, *args, **kwargs):
        return self.visit_text(bbox, *args, **kwargs)
    def visit_word(self, bbox, *args, **kwargs):
        return self.visit_line(bbox, *args, **kwargs)
    def visit_eqn(self, bbox, *args, **kwargs):
        return self.visit_bbox(bbox, *args, **kwargs)
    # etc.
    
    def get_image(self, bbox, image=None, **kwargs): # call from visit_<cls> to access image of bbox
        'Called by BBoxVisitor to access image of bbox, possibly stored in bbox itself or provided as keyword argument.'
        if bbox.annot.image is not None:
            return bbox.annot.image
        if image is not None:
            return ip.crop(image, bbox.rect)
        return None



class BBox:
    'Class representing any segment within a note.'
    class BBoxAnnot:
        def __init__(self, image=None): # may also store images of the box if it needs further processing
            self.image = image
        def __add__(self, other):
            return other
        def __radd__(self, other):
            return self + other
    
    def __init__(self, rect, c=100, annot=None, image=None, children=None):
        self.rect = rect
        self.c = int(c)
        self.annot = annot or BBox.BBoxAnnot(image) # annotation of box e.g. text or equation that implements addition
        self.children = children or []
    
    def area(self):
        return rect.area()
    
    def add_child(self, child):
        self.children.append(child)
        # maybe do some bookkeeping
    
    def __add__(self, other):
        # smallest box containing both boxes
        left, right = (self, other) if self.rect.x0 <= other.rect.x0 else (other, self)
        return BBox(self.rect + other.rect, min([self.c, other.c]), left.annot + right.annot, [left, right])
    
    # def __repr__(self):
    #     return 'BBox(%d, %d, %d, %d, %d, %s, %s)' % (self.rect.x0, self.rect.y0, self.rect.x1, self.rect.y1, self.c, self.annot, self.children)
    
    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_bbox(self, *args, **kwargs)

class Note(BBox):
    def __init__(self, image, rect=Rect(0,0,-1,-1), **kwargs):
        super(Note, self).__init__(rect, image=image, **kwargs)
    
    def accept(self, visitor, *args, **kwargs):
        if 'image' not in kwargs:
            kwargs['image'] = self.annot.image
        if 'note' not in kwargs:
            kwargs['note'] = self
        return visitor.visit_note(self, *args, **kwargs)

class TextBBox(BBox): # may be broken into lines, which may themselves be composed of words or equations
    class TextBBoxAnnot(BBox.BBoxAnnot):
        def __init__(self, text, image=None):
            super(TextBBox.TextBBoxAnnot, self).__init__(image)
            self.text = text # iterable of strings
            # self.rect = rect # may also store processed image of box
        def __add__(self, other):
            # may by default store list of tokens and concatenate them
            # then lines may be arranged vertically while words in lines may be arranged horizontally
            return TextBBox.TextBBoxAnnot(self.text + other.text) #, self.rect + other.rect)
        def __str__(self):
            return '\n'.join(map(str,self.text))
    
    def __init__(self, rect, c=100, text='', image=None, children=None):
        super(TextBBox, self).__init__(rect, c, TextBBox.TextBBoxAnnot([text], image), children)
    
    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_text(self, *args, **kwargs)

class LineBBox(TextBBox): # composed of words or inline expressions
    class LineBBoxAnnot(TextBBox.TextBBoxAnnot):
        def __str__(self):
            return ' '.join(map(str,self.text))
    
    def __init__(self, rect, c=100, text='', image=None, children=None):
        BBox.__init__(self, rect, c, LineBBox.LineBBoxAnnot([text], image), children)
    
    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_line(self, *args, **kwargs)

class WordBBox(TextBBox): # composed of words or inline expressions
    class WordBBoxAnnot(TextBBox.TextBBoxAnnot):
        def __str__(self):
            return ''.join(self.text)
    
    def __init__(self, rect, c=100, text='', image=None, children=None):
        BBox.__init__(self, rect, c, WordBBox.WordBBoxAnnot([text], image), children)
    
    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_word(self, *args, **kwargs)

class EqnBBox(BBox): # composed of mathematical expressions that can span multiple lines
    # TODO special annot class perhaps
    
    def __init__(self, rect, c=100, latex='', image=None, children=None):
        super(EqnBBox, self).__init__(rect, c, TextBBox.TextBBoxAnnot([latex], image), children)
        
    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_eqn(self, *args, **kwargs)

    

# csv may be easier
class BBoxEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            return [self.default(a) for a in obj]
        if isinstance(obj, BBox):
            return {'text': obj.text, 'coords': [obj.x0, obj.y0, obj.x1, obj.y1], 'conf': obj.c,
                    'children': []} # self.default(obj.children)}
        return json.JSONEncoder.default(self, obj)