import json

import numpy as np

class Rect:
    def __init__(self, x0, y0, x1, y1):
        if x0 > x1 and x1 != -1: # -1 taken to be right margin
            x0 = x1
        if y0 > y1 and y1 != -1:
            y0 = y1
        self.x0 = int(x0)
        self.y0 = int(y0)
        self.x1 = int(x1)
        self.y1 = int(y1)
    
    def area(self):
        return (self.x1-self.x0)*(self.y1-self.y0)
    
    def __add__(self, other):
        'Join of two rectangles'
        if self.area() == 0:
            return other
        if other.area() == 0:
            return self
        x0 = min([self.x0, other.x0])
        y0 = min([self.y0, other.y0])
        x1 = max([self.x1, other.x1]) if -1 not in [self.x1, other.x1] else -1
        y1 = max([self.y1, other.y1]) if -1 not in [self.y1, other.y1] else -1
        return Rect(x0, y0, x1, y1)
    
    def __mul__(self, other):
        'Meet of two rectangles'
        if self.area() == 0:
            return self
        if other.area() == 0:
            return other
        x0 = max([self.x0, other.x0])
        y0 = max([self.y0, other.y0])
        x1 = min([self.x1, other.x1]) if -1 not in [self.x1, other.x1] else max([self.x1, other.x1])
        y1 = min([self.y1, other.y1]) if -1 not in [self.y1, other.y1] else max([self.y1, other.y1])
        return Rect(x0, y0, x1, y1)
    
    def area_dist(self, other):
        # area of self + other - self union other - self intersect other
        # need triangle inequality: (x+z)-x-z <= (x+y)-x-y+(y+z)-y-z
        # or (x+z) <= (x+y)+(y+z)-2y
        return (self + other).area() - self.area() - other.area() # + (self * other).area() 
    
    def norm(self):
        'Length of diagonal'
        return ((self.x1-self.x0)**2 + (self.y1-self.y0)**2)**.5
    
    def center(self):
        xs = np.array([self.x0, self.x1])
        ys = np.array([self.y0, self.y1])
        return (xs+ys)/2
    
    def max_dist(self, ps):
        # maximum distance to p=(x,y) [shape n,2]
        cs = self.argmax_dist(ps)
        return np.linalg.norm(cs - ps, axis=1)
    
    def argmax_dist(self, ps):
        # corners of max distance to p=(x, y)
        xs = np.array([self.x0, self.x1])
        ys = np.array([self.y0, self.y1])
        xis = np.argmax(np.abs(ps[:,0].reshape(-1,1) - xs), axis=1)
        yjs = np.argmax(np.abs(ps[:,1].reshape(-1,1) - ys), axis=1)
        return np.stack([xs[xis], ys[yjs]], axis=1)
    
    def __eq__(self, other):
        return [self.x0, self.y0, self.x1, self.y1] == [other.x0, other.y0, other.x1, other.y1]
    
    def __ne__(self, other):
        return not self == other
    
    def __le__(self, other):
        return (self + other) == other # self contained in other
    
    def __lt__(self, other):
        return self <= other and self != other
    
    def __ge__(self, other):
        return other <= self
    
    def __gt__(self, other):
        return other < self

class BBox:
    class BBoxAnnot:
        def __init__(self):
            pass
        def __add__(self, other):
            return other
        def __radd__(self, other):
            return other
    
    def __init__(self, rect, c=100, annot=None, children=None):
        self.rect = rect
        self.c = int(c)
        self.annot = annot or BBoxAnnot() # annotation of box e.g. text or equation that implements addition
        self.children = children or []
    
    def area(self):
        return rect.area()
    
    def __add__(self, other):
        # smallest box containing both boxes
        # TODO detect whether rects are added vertically or horizontally
        left, right = (self, other) if self.rect.x0 <= other.rect.x0 else (other, self)
        return BBox(self.rect + other.rect, min([self.c, other.c]), left.annot + right.annot, [left, right])
    
    def __repr__(self):
        return 'BBox(%d, %d, %d, %d, %d, %s, %s)' % (self.rect.x0, self.rect.y0, self.rect.x1, self.rect.y1, self.c, self.annot, self.children)

class TextBBox(BBox):
    class TextBBoxAnnot:
        def __init__(self, text, rect):
            self.text = text
            self.rect = rect
        def __add__(self, other):
            # determine whether rects differ more in height or in width
            return TextBBoxAnnot(self.text + ' ' + other.text, self.rect + other.rect)
        def __str__(self):
            return self.text
    
    def __init__(self, rect, c=100, text='', children=None):
        BBox.__init__(self, rect, c, TextBBoxAnnot(text, rect), children)

# csv may be easier
class BBoxEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            return [self.default(a) for a in obj]
        if isinstance(obj, BBox):
            return {'text': obj.text, 'coords': [obj.x0, obj.y0, obj.x1, obj.y1], 'conf': obj.c,
                    'children': []} # self.default(obj.children)}
        return json.JSONEncoder.default(self, obj)