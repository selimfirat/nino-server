# Sample and Dataset subclasses specific to training TextRecognizer

import numpy as np
import cv2
import os

from ..utils.rect import *
from .dataset import *

class TextSample(Sample):
    def __init__(self, path, fname, text):
        Sample.__init__(self, path, fname)
        self.text = text
        # self.bboxes = [] # TODO single box, or possibly sets of lines

# may store samples of words as bboxes or samples with single box
# or simply not involve boxes for now
class WordSample(TextSample): # does not include image itself, only path to image, ground truth and other metadata
    def __init__(self, path, fname, text, stat, thres, x, y, w, h): # imgname, bbox, line):
        'For images of individual words listed in IAM'
        TextSample.__init__(self, path, fname, text)
        self.stat = stat
        self.thres = int(thres)
        self.x = x = int(x)
        self.y = y = int(y)
        self.w = w = int(w)
        self.h = h = int(h)
        self.bbox = Rect(x,y,x+w,y+h) # bbox in parent image
        # self.imgname = imgname # name of parent image (accessible via fname or dataset)
        # self.line = line # which line it belongs to in parent image

class LineSample(TextSample):
    def __init__(self, path, fname, tokens, stat, thres, comps, x, y, w, h): # imgname, bbox, line):
        'For images of lines of text listed in IAM'
        TextSample.__init__(self, path, fname, ' '.join(tokens))
        self.stat = stat
        self.thres = int(thres)
        self.comps = int(comps)
        self.x = x = int(x)
        self.y = y = int(y)
        self.w = w = int(w)
        self.h = h = int(h)
        self.bbox = Rect(x,y,x+w,y+h)
        self.tokens = tokens
        # self.imgname = imgname # name of parent image
        # self.bbox = bbox # bbox in parent image
        # self.line = line

class IAMDataset(Dataset):
    def __init__(self, datatype, topdir, skip_err=True, msb=True, tabulate=True, sort=True):
        '''
        Dataset subclass for the IAM handwritten text dataset
        datatype: the specific type of samples the dataset is to be built up from {'forms', 'lines', 'sentences', 'words'}
        topdir: directory the complete IAM dataset is stored in
        skip_err: whether to skip samples marked 'err' in the index (True)
        '''
        super(IAMDataset, self).__init__(topdir, msb, tabulate, sort)
        
        # store samples in tree or list sorted lexicographically, or maybe multidim array
        # to each sample attach bboxes first indexed by line perhaps
        # maybe store preprocessed binary images in bboxes
        # for training words, each image will be a single word
        
        # assert datatype in ['forms', 'lines', 'sentences', 'words'] # TODO
        assert datatype in ['lines', 'words']
        self.datatype = datatype
        func = {'lines':self.line_sample, 'words':self.word_sample}[datatype]
        
        # open txt file
        self.init_samples()
        with open('%s/ascii/%s.txt' % (topdir, datatype)) as f:
            # scan each line
            for line in f:
                func(line, skip_err)
        
        # postprocess sample set, sort keys and collapse into list(s) or nparray for better iteration
        self.sort_samples(msb, tabulate, sort)
    
    def word_sample(self, line, skip_err=True):
        'Process line from index as representing a word sample'
        # line format: 'path1-path2-path3-line stat thres x y w h tag word'
        try:
            [fname, stat, thres, x, y, w, h, tag, word] = line.split(' ')
        except ValueError: # line not of given format
            return 
        if skip_err and stat == 'err':
            return 
        if word[-1] == '\n':
            word = word[:-1]
        
        fpaths = fname.split('-')
        assert len(fpaths) == 4
        
        # file path topdir/datatype/path1/path1-path2/path1-path2-path3-line.png
        # positions do not concern image of word but of the image path1-path2-path3 the image was taken from
        sam = WordSample('%s/%s/%s/%s-%s/%s.png' % (self.topdir, self.datatype, fpaths[0], fpaths[0], fpaths[1], fname), 
                          fname, word, stat, thres, x, y, w, h)
        self.add_sample(sam, fpaths)
    
    def line_sample(self, line, skip_err=True):
        'Process line from index as representing a line sample'
        # line format: path1-path2-path3 stat thres comps x y w h tokens
        if line[0] == '#': # comment line
            return 
        tokens = line.split(' ')
        if len(tokens) < 8:
            return 
        [fname, stat, thres, comps, x, y, w, h] = tokens[:8]
        if skip_err and stat == 'err':
            return 
        tokens = ' '.join(tokens[8:])
        if tokens[-1] == '\n':
            tokens = tokens[:-1]
        tokens = tokens.split('|')
        # assert int(comps) == len(tokens)
        
        fpaths = fname.split('-')
        assert len(fpaths) == 3
        
        # file path topdir/datatype/path1/path1-path2/path1-path2-path3.png
        sam = LineSample('%s/%s/%s/%s-%s/%s.png' % (self.topdir, self.datatype, fpaths[0], fpaths[0], fpaths[1], fname), 
                          fname, tokens, stat, thres, comps, x, y, w, h)
        self.add_sample(sam, fpaths)