import numpy as np
import cv2
import sys
import os

import nino.bbox.bbox as bb
from nino.utils import imgprep as ip, rect as rc

sys.path.append(os.path.dirname(__file__)+'/abhyasa/src')
import track2 as dr

class MathExpRecognizer(bb.BBoxVisitor):
	def __init__(self):
		pass

	def visit_eqn(self, bbox, *args, **kwargs):
		print('visiting %s' % bbox.rect)
		img = self.get_image(bbox, *args, **kwargs)

		cv2.imwrite(os.path.dirname(dr.__file__) + '/../digitRecognition/' + dr.in_path, img)

		# grayscale_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

		# smooth the image to avoid noises
		# gray = cv2.medianBlur(img.astype(np.uint8), 5)

		thresh = cv2.adaptiveThreshold(img.astype(np.uint8), 255, 1, 1, 11, 2) # may also use ip.binarize
		thresh = cv2.dilate(thresh, None, iterations=2)
		thresh = cv2.erode(thresh, None, iterations=1)
		contours = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[1]

		rects = [cv2.boundingRect(contour) for contour in contours]
		# rects = [rc.Rect(x0,y0,x0+w,y0+h) for (x0,y0,w,h) in rects]
		rects.sort(key=lambda rect: rect[0])

		dr.X_cord = []
		dr.Y_cord = []
		dr.W_cord = []
		dr.H_cord = []
		for x, y, w, h in rects:
			if dr.processcontour(x, y, w, h) == 1:
				# get labels of this rectangle
				dr.X_cord.append(x)
				dr.Y_cord.append(-(y+h))
				dr.W_cord.append(w)
				dr.H_cord.append(h)
		dr.getlabels()

		start = dr.Node(value=0, label=dr.labels[0])
		dr.parent_avg = dr.Y_cord[0] + dr.H_cord[0]/2
		prev_node = start

		for i in range(1, len(dr.X_cord)):
			curr_node = dr.Node(value=i, label=dr.labels[i])
			prev_node = dr.locate_and_label(prev_node, curr_node, i)

		# create EqnBBoxes for each node and annotate them (for testing; later parse into latex and annotate the single box)
		for i, (x,y,w,h) in enumerate(rects):
			bbox.children.append(bb.EqnBBox(rect=rc.Rect(x,y,x+w,y+h)+(bbox.rect.x0,bbox.rect.y0), latex=dr.labels[i]))
