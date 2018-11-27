from dataset import *

# samples from im2latex

class EqnSample(TextSample):
    def __init__(self, path, fname, latex):
        TextSample.__init__(self, path, fname, latex)

class HarvardDataset(Dataset):
    def __init__(self, topdir, dataset, msb=True, tabulate=True, sort=True):
        super(HarvardDataset, self).__init__(topdir, msb, tabulate, sort)
        
        assert dataset in ['small', 'train', 'val', 'test']
        self.dataset = dataset
        self.imgdir = ('images_' if dataset != 'small' else '') + dataset
        
        # create samples for each image
        self.init_samples()
        with open('%s/%s.matching.txt' % (topdir, dataset)) as fm:
            for lm in fm:
                [fname, n] = lm.split(' ')
                n = int(n)
                assert fname == '%d.png' % n
                sam = EqnSample('%s/%s/%s' % (topdir, self.imgdir, fname), fname, '')
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
        