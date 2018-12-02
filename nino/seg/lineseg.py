# Segment lines into words before sending them to TextRecognizer
# For now, simple rule-based implementation; may add more implementations later

import numpy as np
import cv2

import bbox as bb
import imgprep as ip

class LineSegmentor(bb.BBoxVisitor):
    def __init__(self, downsample=4, r=3):
        self.downsample = downsample
        self.ker = np.ones((r,r),np.uint8)
        self.r = r
        
    def visit_line(self, line, *args, **kwargs):
        # get image of line
        img = ip.get_image(line, **kwargs)
        
        # binarize, then downsample and close image
        img = ip.binarize(img, otsu=True)
        img = cv2.bitwise_not(img)
        if self.downsample:
            img = cv2.morphologyEx(img, cv2.MORPH_DILATE, self.ker)
            img = ip.rescale(img, scale=1/self.downsample)
            img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, self.ker)
        
        # get contours of processed image, collect their bounding rectangles
        contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]
        rects = [cv2.boundingRect(contour) for contour in contours]
        rects = [bb.Rect(x0,y0,x0+w,y0+h) for (x0,y0,w,h) in rects]
        # rects = [bb.Rect(x0-self.r/2,y0-self.r/2,x0+w+self.r/2,y0+h+self.r/2) for (x0,y0,w,h) in rects]
        
        # rescale each rectangle back to size of original image
        rects = [rect.rescale(self.downsample) for rect in rects]
        # rects = [bb.Rect(rect.x0-self.r/2, rect.y0-self.r/2,
        #                  rect.x1+self.r/2, rect.y1+self.r/2) for rect in rects]
        
        # for each rectangle, add new WordBBox to line.children
        for rect in rects:
            line.add_child(bb.WordBBox(rect))
        