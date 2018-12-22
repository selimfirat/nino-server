# Some helper functions for image processing

import numpy as np
import cv2

from .rect import *

def rescale(img, h=None, w=None, scale=None):
    'Rescale image to given height or width, rescaling proportionally if only one extent is given.'
    if h is None and w is None and scale is None:
        return img
    h0, w0 = img.shape
    if scale:
        h = int(h0*scale)
        w = int(w0*scale)
    if h is None:
        h = int(h0*w/w0)
    if w is None:
        w = int(w0*h/h0)
    return cv2.resize(img, (w, h))

def binarize(img, thres=None, otsu=False):
    'Binarize image with threshold provided or adaptively, optionally using Otsu\'s method.'
    if thres is None:
        thres = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    if otsu:
        thres = 0
    return cv2.threshold(img, thres, 255, cv2.THRESH_BINARY+otsu*cv2.THRESH_OTSU)[1]

def crop(img, rect, copy=True):
    res = img[rect.y0:rect.y1,rect.x0:rect.x1]
    return res.copy() if copy else res

def bounding_rects(img):
    contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]
    rects = [cv2.boundingRect(contour) for contour in contours]
    return [Rect(x0,y0,x0+w,y0+h) for (x0,y0,w,h) in rects]

# may add here further functions to find contours, bounding boxes etc. when the need arises