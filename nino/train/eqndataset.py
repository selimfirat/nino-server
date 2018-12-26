# Samples from im2latex
# Obtained by calling "make build" on https://github.com/guillaumegenthial/im2latex

import cv2

from .dataset import *
from .textdataset import *

class EqnSample(TextSample):
    def __init__(self, path, fname, latex, w, h):
        TextSample.__init__(self, path, fname, latex, 0, 0, w, h)

class HarvardDataset(Dataset):
    def __init__(self, topdir, dataset, msb=True, tabulate=True, sort=True):
        super(HarvardDataset, self).__init__(topdir, msb, tabulate, sort)
        
        # assert dataset in ['small', 'train', 'val', 'test']
        self.dataset = dataset
        self.imgdir = ('images_' if dataset != 'small' else '') + dataset
        
        # create samples for each image
        self.init_samples()
        try:
            with open('%s/%s.sizes.txt' % (topdir, dataset)) as f:
                lines = f.read().split('\n')
                if lines[-1] == '':
                    lines = lines[:-1]
                self.sizes = [s.split(' ') for s in lines]
        except FileNotFoundError:
            self.sizes = []
                
        with open('%s/%s.matching.txt' % (topdir, dataset)) as fm:
            for i, lm in enumerate(fm):
                [fname, n] = lm.split(' ')
                n = int(n)
                assert fname == '%d.png' % n
                path = '%s/%s/%s' % (topdir, self.imgdir, fname)
                if len(self.sizes) <= i:
                    assert len(self.sizes) == i
                    self.sizes.append(cv2.imread(path, cv2.IMREAD_GRAYSCALE).shape)
                sam = EqnSample(path, fname, '', *self.sizes[i])
                self.add_sample(sam, [n])

        # assign formulas to each sample
        with open('%s/%s.formulas.norm.txt' % (topdir, dataset)) as fn:
            for i, ln in enumerate(fn):
                sam = self.get_sample(i)
                if sam is not None:
                    if ln[-1] == '\n':
                        ln = ln[:-1]
                    sam.text = ln
        
        self.sort_samples(msb, tabulate, sort)
        