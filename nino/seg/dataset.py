import numpy as np
import bisect

from bbox import Rect

class Sample:
    def __init__(self, path, fname):
        self.path = path
        self.fname = fname
        # self.bboxes = [] # stored in csv
    def __repr__(self):
        return 'Sample(%s)' % self.fname.__repr__()
    # possibly a load method, using cv2 etc.
        
class Dataset:
    def __init__(self, topdir, msb=True, tabulate=True, sort=True):
        '''
        General dataset class maintaining sample filenames in nested dictionary, multidim table or sorted list
        topdir: top directory of dataset
        msb: whether to sort data msb first (lexicographically) or reverse (may be better for randomization)
        tabulate: whether to create multidimensional array samtabl to store samples
        sort: whether to collect all samples in list sorted lexicographically
        '''
        if topdir[-1] == '/':
            topdir = topdir[:-1]
        self.topdir = topdir
        self.init_samples()
        self.msb = msb
        self.tabulate = tabulate
        self.sort = sort
    
    def init_samples(self):
        self.samples = {}
        self.indices = []
        self.samtabl = []
        self.samlist = []
    
    def add_sample(self, sam, index=None):
        'Add sample to dictionary, indexed by a list of strings.'
        if index is None:
            index = [sam.path]
        samples = self.samples
        for i, s in enumerate(index):
            if len(self.indices) <= i:
                assert len(self.indices) == i
                self.indices.append([s])
            # add s to indices[i] if not already in
            self.get_index(i, s)
            if i == len(index) - 1:
                samples[s] = sam
            else:
                if s not in samples:
                    samples[s] = {}
                samples = samples[s]
    
    def get_index(self, i, s):
        'To call multidimensional array, get the index of string s in the ith dimension.'
        j = bisect.bisect_left(self.indices[i], s)
        if j == len(self.indices[i]) or self.indices[i][j] != s:
            self.indices[i].insert(j, s)
        return j
    
    def sort_samples(self, msb=True, tabulate=True, sort=True):
        'Generate table or list from the nested dictionary of samples.'
        if tabulate or sort:
            self.samtabl = self.sample_table()
        if sort:
            self.samlist = self.sample_list(msb)
    
    def sample_table(self, df=True):
        'Generate table from dictionary via depth-first search.'
        stack = [(0, self.samples, [], 0)]
        while stack:
            i, samples, arr, j = stack.pop(-df)
            if j < len(self.indices[i]):
                stack.insert(-df, (i, samples, arr, j+1))
                s = self.indices[i][j]
                if i == len(self.indices) - 1:
                    arr.append(samples[s] if s in samples else None)
                else:
                    arr.append([])
                    stack.insert(-df, (i+1, samples[s] if s in samples else {}, arr[j], 0))
        return np.array(arr)
    
    def get_sample(self, *index):
        'Get sample with given index in dataset.'
        if self.samtabl != []:
            try:
                return self.samtabl[tuple(self.get_index(i,s) for (i,s) in enumerate(index))]
            except IndexError:
                return None
        else:
            samples = self.samples
            for (i,s) in enumerate(index):
                if s not in samples:
                    return None
                samples = samples[s]
            return samples
    
    def sample_list(self, msb=True):
        'Convert dictionary into sorted list.'
        arr = []
        stack = [(0, 0, [])]
        indices = self.indices if msb else list(reversed(self.indices))
        while stack:
            i, j, pref = stack.pop()
            if j < len(indices[i]):
                stack.append((i, j+1, pref))
                # s = indices[i][j]
                if i == len(indices) - 1:
                    # arr.append(self.samtabl[tuple(self.get_index(i1,s1) for (i1,s1) in enumerate(pref+[s]))])
                    pref1 = pref+[j] if msb else reversed(pref+[j])
                    if self.samtabl is not []:
                        sam = self.samtabl[tuple(pref1)]
                    else:
                        pref1 = tuple(self.indices[i1][j1] for (i1,j1) in enumerate(pref1))
                        sam = self.get_sample(*pref1)
                    # self.get_sample(*list(reversed(pref+[s]))) # inefficient cheat for lsb
                    if sam is not None:
                        arr.append(sam)
                else:
                    stack.append((i+1, 0, pref+[j]))
        return arr
    
    def __iter__(self):
        if self.samlist:
            for s in self.samlist:
                yield s # TODO open image, yield BBox
        
        # traverse dictionary lexicographically
        # for training, it may be useful to sort backwards to get even batches
        def gen(samples):
            if not isinstance(samples, dict):
                yield samples
            else:
                for sample in samples.values():
                    for s in gen(sample):
                        yield s
        for s in gen(self.samples):
            yield s

    def __len__(self):
        return len(self.samlist)

class TrainDataset(Dataset): 
    'Dataset used for training, preprocessed into batches (and possibly train, validation and test sets)'
    def __init__(self, dataset, msb=True, tabulate=True, sort=True):
        super(TrainDataset, self).__init__(dataset.topdir, msb, tabulate, sort)
        self.dataset = dataset 
        # load pictures from path in dataset
        # create new folder in topdir/../prep/datatype
        # preprocess each image, save to folder
        # store filenames of each image and ground truth in index
        
        # first gather the normalized widths and heights of each sample (available from words.txt)
        # then quantize and sort them, so that each batch has images of the same width
        # or pad images in batch to some maximum width and then specify their actual widths in another file
        pass