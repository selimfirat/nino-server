# Automatically generated dataset for segmentation

import numpy as np
import cv2
import os

from .dataset import *
import nino.bbox.bbox as bb
import nino.utils.imgprep as ip
from nino.utils.rect import Rect
from nino.bbox.utils import BBoxPrinter

class SegmentSample(Sample):
    # generated image with bbox tree for ground truth
    # generate indicator array (height, width, classes) using visitor drawing rectangles on image
    def __init__(self, path, fname, note):
        super(SegmentSample, self).__init__(path, fname)
        self.note = note

class SegmentDataset(Dataset):
    def __init__(self, textds, eqnds, n=None, topdir='~~', msb=True, tabulate=True, sort=True, 
                 lmin=200, lmax=1000, nmax=10, p=.5, sc=5, verbose=False, create=True, **kwargs):
        '''Dataset for segmentation generated from preexisting text and equation datasets
        textds: text dataset
        eqnds: equation dataset
        n: number of samples to generate, None if unbounded
        path: path to save images to, None if generated at will
        lmin, lmax: minimum and maximum width or height of generated images
        nmax, p: parameters of binomial distribution to generate box count
        sc: scale bboxes to between 1/sc and sc times its original size
        more parameters for randomness
        verbose: whether to output progress (default False)
        create: whether to create new images or read from topdir'''
        super(SegmentDataset, self).__init__(topdir, msb, tabulate, sort)
        self.n = n
        self.datasets = {'text': textds, 'eqn': eqnds} # possibly add more
        self.classes = {'text': bb.LineBBox, 'eqn': bb.EqnBBox}
        assert all(dat.sort for dat in self.datasets.values())
        
        assert n is not None # and topdir is None # deal with this later
        
        self.index = self.topdir + '/index.txt'
        self.imgdir = self.topdir + '/images'
        self.boxdir = self.topdir + '/bboxes'
        
        if create and self.topdir != '~~':
            os.mkdir(self.imgdir) # what if folder already exists
            os.mkdir(self.boxdir)
        
        self.init_samples()
        
        if self.topdir == '~~':
            self.topdir = None
        
        if not create:
            with open(self.index, 'r') as f:
                for line in f:
                    sp = line.index(' ')
                    i, s = int(line[:sp]), line[sp+1:]
                    if s[-1] == '\n':
                        s = s[:-1]
                    note = BBoxPrinter.read_note(s)
                    self.add_sample(SegmentSample('%s/%d.png' % (self.imgdir, i), str(i), note), [i])
        
        if self.topdir is not None:
            f = open(self.index, 'w')
        for i in range(n): # TODO deal with unbounded n later
            # generate width, height
            w, h = np.random.randint(lmin, lmax, 2)
            img = np.zeros((h,w)) # sample image, not ground truth (which may later be precomputed)
            img[:] = 255
            
            # generate each box
            boxes = []
            for _ in range(np.random.binomial(nmax, p)):
                
                # draw random sample
                boxtype = np.random.choice(list(self.classes))
                s = np.random.choice(self.datasets[boxtype].samlist)
                
                # load sample
                box = cv2.imread(s.path, cv2.IMREAD_GRAYSCALE)
                if box.shape[0] > 48:
                    box = ip.rescale(box, h=48)
                
                # scale image, generate (x, y)
                for _ in range(10):
                    scale = sc ** (2 * np.random.random() - 1)
                    box = ip.rescale(box, scale=scale)
                    h1, w1 = box.shape
                    if h1 < h and w1 < w:
                        break
                else:
                    continue
                # find empty place, quit if can't find
                for _ in range(10):
                    x = np.random.randint(w - w1)
                    y = np.random.randint(h - h1)
                    rect = Rect(x,y,x+w1,y+h1)
                    if all(not rect.intersects(b.rect) for b in boxes):
                        break
                else:
                    continue
                
                # add image to img, add box to note
                bbox = self.classes[boxtype](rect, 100, s.text)
                boxes.append(bbox)
                img[y:y+h1,x:x+w1] = ip.binarize(box, otsu=True)
            
            note = bb.Note(img, rect=Rect(0,0,w,h), children=boxes) # TODO possibly save image and load it as needed
            if self.topdir is None:
                self.add_sample(SegmentSample(None, str(i), note), [i])
            else:
                self.add_sample(SegmentSample('%s/%d.png' % (self.imgdir, i), str(i), note), [i])
                # write img to imgdir
                cv2.imwrite('%s/%d.png' % (self.imgdir, i), img)
                # write box map to boxdir
                cv2.imwrite('%s/%d.png' % (self.boxdir, i), 127*GroundTruthViewer().visit(note))
                # write i and the note to index
                f.write('%d %s\n' % (i, BBoxPrinter.print_note(note)))
            if verbose:
                print('created %d' % i)
        if self.topdir is not None:
            f.close()
                
        self.sort_samples(msb, tabulate, sort)
        
class GroundTruthViewer(bb.BBoxVisitor):
    classes = {'text': 1, 'eqn': 2}
    def visit_note(self, bbox, *args, **kwargs):
        res = np.zeros(bbox.rect.shape())
        super(GroundTruthViewer, self).visit_note(bbox, res, *args, **kwargs)
        return res
    def visit_text(self, bbox, res, *args, **kwargs):
        x0, y0, x1, y1 = bbox.rect.x0, bbox.rect.y0, bbox.rect.x1, bbox.rect.y1
        res[y0:y1,x0:x1] = GroundTruthViewer.classes['text']
    def visit_eqn(self, bbox, res, *args, **kwargs):
        x0, y0, x1, y1 = bbox.rect.x0, bbox.rect.y0, bbox.rect.x1, bbox.rect.y1
        res[y0:y1,x0:x1] = GroundTruthViewer.classes['eqn']
            