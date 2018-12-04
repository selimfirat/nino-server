# Preprocess dataset in batches, save arrays to disk for faster loading

# Given that the IAM dataset is ordered hierarchically,
# save each top level folder as a single file
# Concatenate ground truth for each folder into single string [for CTCLoss]
# Encode characters into integers, store lengths of words in separate array

import numpy as np
import cv2
import os

from .textdataset import *
from ..textrec import textenc as enc
from ..utils import imgprep as ip

class WordTrainSample(TextSample):
    def __init__(self, path, fname, text, lengths):
        super(WordTrainSample, self).__init__(path, fname, text)
        self.lengths = lengths # 1d array of lengths of each text
        self.checked = False

class IAMTrainDataset(TrainDataset):
    def __init__(self, iam, subdir, batchsiz, 
                 create=True, encoding='all', verbose=False, binarize=True, normalize=False,
                 msb=True, tabulate=True, sort=True):
        super(IAMTrainDataset, self).__init__(iam, msb, tabulate, sort)
        self.topdir = '%s/%s/%s' % (iam.topdir, subdir, iam.datatype)
        assert iam.sort
        self.batchsiz = batchsiz # max size of each batch
        self.create = create
        
        encoding = enc.encodings[encoding]
        
        # first sort iam by rounded width, gather indices in sinds for each batch
        rwidths = np.array(list(map(self.normalize_width, iam.samlist)))
        vals, inds, cnts = np.unique(rwidths, return_inverse=True, return_counts=True)
        sinds = np.argsort(inds)
        # divide indices into sections of same width, then divide into batches online
        cs = np.array_split(sinds, np.cumsum(cnts[:-1]))
        
        # iterate through each batch, open each image, resize and collect in array
        # save array for each batch as well as ground truth array
        # TODO remove topdir if create
        self.mkdir('%s/%s' % (iam.topdir, subdir))
        self.mkdir(self.topdir)
        for i, c in enumerate(cs):
            cdir = '%s/c%d' % (self.topdir, i)
            nbs = cnts[i]//batchsiz+1 # possibly modify batch size based on width
            self.mkdir(cdir)
            if verbose:
                print('Processing %d batches of %d images of width %d (%d/%d)' % \
                      (nbs, cnts[i], vals[i], i+1, cnts.shape[0]))
            bs = np.array_split(c, nbs)
            for j, b in enumerate(bs):
                # create new batch (i,j)
                
                # collect all images, create new array
                arr = []
                texts = ''
                lens = []
                for k in b:
                    text = iam.samlist[k].text
                    if text[-1] == '\n':
                        text = text[:-1]
                    if encoding is not None:
                        text = enc.check(encoding, text)
                    if len(text) == 0:
                        continue
                    texts += text
                    lens.append(len(text))
                    if not create:
                        continue
                    a = cv2.imread(iam.samlist[k].path, cv2.IMREAD_GRAYSCALE)
                    if a is None:
                        if verbose:
                            print('Could not read %s' % iam.samlist[k].fname)
                        continue
                    a = ip.rescale(a, h=32) # cv2.resize(a, (int(rwidths[k]), 32))
                    if binarize:
                        a = ip.binarize(a, iam.samlist[k].thres) # cv2.threshold(a, iam.samlist[k].thres, 255, cv2.THRESH_BINARY)[1]
                    if normalize:
                        a = (a - a.mean()) / a.std()
                    arr.append(a)
                arr = np.array(arr)
                lens = np.array(lens, dtype='int32')
                
                # create file
                # affix ground truth array to batch (new subclass of sample)
                fname = '%d-%d' % (i, j)
                path = '%s/%s.npy' % (cdir, fname)
                self.add_sample(WordTrainSample(path, fname, texts, lens)) # , fname.split('-'))
                
                # save array in subfolder i of self.topdir
                if create:
                    np.save(path, arr) # can also save to npz
        
        self.sort_samples(msb, tabulate, sort)
    
    def normalize_width(self, sam):
        return np.ceil(2*sam.w/sam.h)*16 # rework to minimize distance while avoiding 0 width
    
    def mkdir(self, path):
        if not self.create:
            return
        try:
            os.mkdir(path)
        except FileExistsError:
            pass