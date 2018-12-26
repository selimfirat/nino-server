# Class representing rectangular regions in images

import numpy as np
from numbers import Number

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
    
    def shape(self):
        return (self.y1-self.y0, self.x1-self.x0)
    
    def __repr__(self):
        return 'Rect(%d,%d,%d,%d)' % (self.x0, self.y0, self.x1, self.y1)
    
    def area(self):
        return (self.x1-self.x0)*(self.y1-self.y0)
    
    def rescale(self, scale):
        return Rect(self.x0, self.y0, int(scale*self.x1 + (1-scale)*self.x0), 
                                      int(scale*self.y1 + (1-scale)*self.y0))
    
    def intersects(self, other):
        return (self*other).area() > 0
    
    def __radd__(self, other):
        return self + other
    
    def __add__(self, other):
        'Join of two rectangles'
        if isinstance(other, Number):
            return Rect(self.x0+other, self.y0+other, self.x1+other, self.y1+other)
        if self.area() == 0:
            return other
        if other.area() == 0:
            return self
        x0 = min([self.x0, other.x0])
        y0 = min([self.y0, other.y0])
        x1 = max([self.x1, other.x1]) if -1 not in [self.x1, other.x1] else -1
        y1 = max([self.y1, other.y1]) if -1 not in [self.y1, other.y1] else -1
        return Rect(x0, y0, x1, y1)
    
    def __rmul__(self, other):
        return self + other
    
    def __mul__(self, other):
        'Meet of two rectangles'
        if isinstance(other, Number):
            return self.rescale(other)
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