import cv2
import numpy as np
from PIL import Image, ImageEnhance
from skimage.io import imread
from matplotlib import pyplot as plt
from skimage.morphology import skeletonize
from skimage.filters import gaussian, threshold_minimum
import sys
import os
sys.path.insert(0, '../src')
from predictor_svm_cnn_combined import predict_label
sys.path.insert(0, '../..')
from bbox import bbox as bb

White = [255, 255, 255]
labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
			'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
			'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p']
X_cord = []
Y_cord = []
W_cord = []
H_cord = []


class Node(object):
	def __init__(self, top=None, bottom=None, nxt=None, parent=None, value=None, label=None):
		self.top = top
		self.bottom = bottom
		self.nxt = nxt
		self.label = label
		self.parent = parent
		self.value = value


def thinning(image_abs_path, i):
	grayscale_img = imread(image_abs_path, as_gray=True)
	gaussian_blur = gaussian(grayscale_img, sigma=1)
	thresh_sauvola = threshold_minimum(gaussian_blur)
	binary_img = gaussian_blur < thresh_sauvola
	thinned_img = skeletonize(binary_img)
	thinned_img = thinned_img == 0
	plt.imsave('output.png', thinned_img, format="png", cmap="hot")
	plt.imsave('output_'+str(i)+'.png', thinned_img, format="png", cmap="hot")


def crop(image_path, coords, saved_location, i):
	image_obj = Image.open(image_path)
	cropped_image = image_obj.crop(coords)
	cropped_image.save(saved_location)
	cropped_image.save("_ppt"+str(i)+".png")


def printTree(start):
	if start is None:
		return
	print(start.label, end="")
	if start.bottom is not None:
		print('_{', end="")
		printTree(start.bottom)
		print('}', end="")
	if start.top is not None:
		print('^{', end="")
		printTree(start.top)
		print('}', end="")
	printTree(start.nxt)


def squareit(i):
	crop(sys.argv[1], (X_cord[i], -Y_cord[i]-H_cord[i], X_cord[i] + W_cord[i], -Y_cord[i]), "output.png", i)
	img1 = cv2.imread('output.png')
	dif_abs = abs(int(W_cord[i]-H_cord[i]))
	padding = int(dif_abs/2)
	if W_cord[i] > H_cord[i]:
		padded_img = cv2.copyMakeBorder(img1, padding, dif_abs - padding, 0, 0, cv2.BORDER_CONSTANT, value=White)
	else:
		padded_img = cv2.copyMakeBorder(img1, 0, 0, padding, dif_abs - padding, cv2.BORDER_CONSTANT, value=White)
	
	plt.imsave('_sqrd'+str(i)+'.png', padded_img, format="png", cmap="hot")
	padded_img= cv2.resize(padded_img, (45, 45))
	# plt.imsave('final.jpg',new_image, format="jpg", cmap="hot")

	plt.imsave('_small'+str(i)+'.png', padded_img, format="png", cmap="hot")
	plt.imsave('output.png', padded_img, format="png", cmap="hot")
	thinning("output.png", i)


def getlabels():
	for i in range(0, len(X_cord)):
		squareit(i)
		labels[i] = predict_label(np.asarray(Image.open('output_'+str(i)+'.png').convert('L').resize((45, 45), Image.ANTIALIAS)).flatten())
		if labels[i] == 'geq' or labels[i] == 'j' or labels[i] == 'i' or labels[i] == '!' or labels[i] == '-':
			Y_cord[i] = Y_cord[i]-(H_cord[i]/4.0)
			H_cord[i] = H_cord[i]+(H_cord[i]/2.0)
			if i+1 < len(X_cord):
				if processcontour(X_cord[i+1], Y_cord[i+1], W_cord[i+1], H_cord[i+1]) == 0:
					labels.pop(i+1)
					X_cord.pop(i+1)
					Y_cord.pop(i+1)
					W_cord.pop(i+1)
					H_cord.pop(i+1)	
				if processcontour(X_cord[i-1], Y_cord[i-1], W_cord[i-1], H_cord[i-1]) == 0:
					labels.pop(i-1)
					X_cord.pop(i-1)
					Y_cord.pop(i-1)
					W_cord.pop(i-1)
					H_cord.pop(i-1)		
			squareit(i)
			labels[i] = predict_label(np.asarray(Image.open('output_'+str(i)+'.png').convert('L').resize((45, 45), Image.ANTIALIAS)).flatten())
		if labels[i] == 'ascii_124':
			labels[i] = '1'		
		if labels[i] == 'times':
			labels[i] = 'x'
		if labels[i] == 'sum':
			labels[i] = '\sigma'
		if labels[i] == 'lambda' or labels[i] == 'Delta' or labels[i] == 'neq' or \
				labels[i] == 'geq' or labels[i] == 'leq' or labels[i] == 'infty' or labels[i] == 'beta':
			labels[i] = "\\" + labels[i]
		print("Label ", i, "->\t", labels[i])
		# Test the Squared Image received
		# l = process(sqimage)
		# labels.append(l)


# For each contour, find the bounding rectangle and draw it
def processcontour(x, y, w, h):
	for i in range(0,len(X_cord)):
		x2 = X_cord[i]+W_cord[i]
		x1 = X_cord[i]
		y1 = Y_cord[i]
		y2 = Y_cord[i]+H_cord[i]
		if x2 > x > x1 and y2 > -(y+h) > y1:
			if x+w < x2:
				# Check for Height 
				if -y < y2 or abs((y2 + y + h)*1.0/h) > 0.6:
					# Discard
					# print x,-(y+h),x1,y1,"---case 11 ",i
					return 0
			else:
				if -y < y2 and abs((x2 - x)*1.0/w) > 0.6: 
					# Discard
					# print x,-(y+h),x1,y1,"---case 12 ",i
					return 0
				elif -y > y2 and abs((x2-x)*(y2+y+h)*1.0/(w*h)) > 0.6:
					# print x,-(y+h),x1,y1,"---case 13 ",i
					return 0

		elif x2 > x+w > x1 and y2 > -(y+h) > y1:
			if -y < y2 and abs((x+w - x1)*1.0/w) > 0.6: 
				# Discard
				# print x,-(y+h),x1,y1,"---case 21 ",i
				return 0
			elif -y > y2 and abs((x+w-x1)*(y2+y+h)*1.0/(w*h)) > 0.6:
				# print x,-(y+h),x1,y1,"---case 22 ",i
				return 0
		elif x2 > x+w > x1 and y2 > -y > y1:
			if x > x1 and abs(-(y+y1)*1.0/h)>0.6:
				# print x,-(y+h),x1,y1,"---case 31 ",i
				return 0
			elif x < x1 and abs((x+w-x1)*(y+y1)*1.0/(w*h)) > 0.6:
				# print x,-(y+h),x1,y1,"---case 32 ",i
				return 0
		elif x2 > x > x1 and y2 > -(y+h) > y1:
			if abs((x2-x)*(-y-h-y1)*1.0/(w*h)) > 0.6:
				# print x,-(y+h),x1,y1,"---case 41 ",i
				return 0
	return 1


def locate_and_label(prev_node, curr_node, count):
	l_avg = (Y_cord[prev_node.value] + (H_cord[prev_node.value]/2))
	l_bot = Y_cord[prev_node.value]
	l_top = l_bot + H_cord[prev_node.value]
	r_bot = Y_cord[curr_node.value]
	r_top = r_bot + H_cord[curr_node.value]
	prnt = prev_node.parent
	if prnt is None:
		# print "count is ",count,"Inside None"
		if curr_node.label == '2':
			print("Inside if")
		if l_avg < r_bot:
				# Go to TOP of L 
			# print "count is ",count,"Inside None 1"
			if curr_node.label == '2':
				print("Inside if1")
			prev_node.top = curr_node
			curr_node.parent = prev_node
			prev_node = curr_node
		elif l_avg > r_top:
			# Go to BOT Of L
			# print "count is ",count,"Inside None 2"
			if curr_node.label == '2':
				print("Inside if2")
			prev_node.bottom = curr_node
			curr_node.parent = prev_node
			prev_node = curr_node
		else:
			# GO to Next of L 
			# print "count is ",count,"Inside None 3"
			if curr_node.label == '2':
				print("Inside if3")
			prev_node.nxt = curr_node
			curr_node.parent = prev_node.parent
			prev_node = curr_node
		return prev_node
	else:
		parent_avg = (Y_cord[prnt.value] + (H_cord[prnt.value]/2))
		if parent_avg < l_bot:
			# print "count is ",count,"Inside Parent in down"
			if r_bot > parent_avg:
				if l_top*1.1 > r_bot > l_avg:
					#  Go to TOP of L
					# print "TOP"
					prev_node.top = curr_node
					curr_node.parent = prev_node
					prev_node = curr_node

				elif r_top < l_avg: 
					# Go to Bottom  of L
					# print "Bottom"
					prev_node.bottom = curr_node
					curr_node.parent = prev_node
					prev_node = curr_node
				elif r_top > l_avg:
					# Go to next of L
					# print "Next"
					prev_node.nxt = curr_node
					curr_node.parent = prev_node.parent
					prev_node = curr_node
				else:
					return locate_and_label(prev_node.parent, curr_node, count)
					
			else:
				return locate_and_label(prev_node.parent, curr_node, count)
			return prev_node
		elif parent_avg > l_top:
			# print "count is ",count,"Inside Parent is UP"
			if r_top < parent_avg:
				if l_avg > r_top > l_bot*0.9:
					# Go to BOTTOM of L
					# print "Bottom"
					prev_node.bottom = curr_node
					curr_node.parent = prev_node
					prev_node = curr_node
				elif r_bot > l_avg:
					# Go to TOP of L
					# print "Top"
					prev_node.top = curr_node
					curr_node.parent = prev_node
					prev_node = curr_node
				elif r_bot < l_avg:
					#  Go to Next of L
					# print "Next"
					prev_node.nxt = curr_node
					curr_node.parent = prev_node.parent
					prev_node = curr_node 
				else:
					return locate_and_label(prev_node.parent, curr_node, count)
			else:
				return locate_and_label(prev_node.parent, curr_node, count)
			return prev_node


class MathExpRecognizer(bb.BBoxVisitor):
	def __init__(self):
		# TODO: add hidden states & learning rate epoch etc in constructor
		pass

	def visit_eqn(self, original_image, grayscale_image, img):
		# img = cv2.imread(image) # Load the image
		# gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) # convert to grayscale

		# TODO: hayaletbeyazı
		# alpha = 2.2  # contrast
		# beta = 0  # brightness
		# new_image = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

		enhancer_contrast = ImageEnhance.Contrast(Image.open(img))
		enhancer_brightness = ImageEnhance.Brightness(Image.open(img))

		for i in range(8):
			factor = 1 + i / 3.0
			enhancer_contrast.enhance(factor).show("Sharpness %f" % factor)
		#for i in range(2):
		factor = 1 + 1/2
		enhancer_brightness.enhance(factor).show("Brightness %f" % factor)

		grayscale_image = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2GRAY)

		# smooth the image to avoid noises
		gray = cv2.medianBlur(grayscale_image, 5)


		# cv2.imshow('contrast im', new_image)
		cv2.imshow('original gray', gray)




		# Apply adaptive threshold
		thresh = cv2.adaptiveThreshold(gray, 255, 1, 1, 11, 2)
		thresh_color = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

		# apply some dilation and erosion to join the gaps
		thresh = cv2.dilate(thresh, None, iterations=3)
		thresh = cv2.erode(thresh, None, iterations=2)
		x, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
		contours = sorted(contours, key=lambda cont: cv2.boundingRect(cont)[0])

		for cnt in contours:
			x, y, w, h = cv2.boundingRect(cnt)
			# print x;
			if processcontour(x, y, w, h) == 1:
				# get labels of this rectangle
				X_cord.append(x)
				Y_cord.append(-(y+h))
				W_cord.append(w)
				H_cord.append(h)
				cv2.rectangle(original_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
			else:
				cv2.rectangle(original_image, (x, y), (x+w, y+h), (0, 0, 255), 2)

		getlabels()

		start = Node(value=0, label=labels[0])
		parent_avg = (Y_cord[0] + (H_cord[0]/2))
		prev_node = start
		print("Before locate")
		cv2.imshow('img', original_image)
		cv2.waitKey(10000)
		print("About to locate")

		for i in range(1, len(X_cord)):
			curr_node = Node(value=i, label=labels[i])
			prev_node = locate_and_label(prev_node, curr_node, i)
			# print "_L-------------------",prev_node.label

		print("About to print")
		print("$ ", end="")
		printTree(start)
		print(" $")

		return X_cord, Y_cord, W_cord, H_cord


print("Current test for math exp rec: ")
mr = MathExpRecognizer()
mr.visit_eqn(cv2.imread(sys.argv[1]), cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2GRAY), sys.argv[1])
