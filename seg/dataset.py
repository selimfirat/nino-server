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

class TextSample(Sample):
    def __init__(self, path, fname, text):
        Sample.__init__(self, path, fname)
        self.text = text
        # self.bboxes = [] # TODO single box

# may store samples of words as bboxes or samples with single box
# or simply not involve boxes for now
class WordSample(TextSample):
    def __init__(self, path, fname, text, stat, thres, x, y, w, h): # imgname, bbox, line):
        TextSample.__init__(self, path, fname, text)
        self.stat = stat
        self.thres = int(thres)
        self.x = x = int(x)
        self.y = y = int(y)
        self.w = w = int(w)
        self.h = h = int(h)
        self.bbox = Rect(x,y,x+w,y+h)
        # self.imgname = imgname # name of parent image
        # self.bbox = bbox # bbox in parent image
        # self.line = line

class LineSample(TextSample):
    def __init__(self, path, fname, tokens, stat, thres, comps, x, y, w, h): # imgname, bbox, line):
        TextSample.__init__(self, path, fname, tokens)
        self.stat = stat
        self.thres = int(thres)
        self.comps = int(comps)
        self.x = x = int(x)
        self.y = y = int(y)
        self.w = w = int(w)
        self.h = h = int(h)
        self.bbox = Rect(x,y,x+w,y+h)
        # self.imgname = imgname # name of parent image
        # self.bbox = bbox # bbox in parent image
        # self.line = line
        
class Dataset:
    def __init__(self, topdir, msb=True, tabulate=True, sort=True):
        # general dataset class maintaining sample filenames in various structures:
        # nested dictionary, multidimensional table, sorted list
        # msb: whether to sort data msb first (lexicographically) or reverse (may be better for randomization)
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

class IAMDataset(Dataset): # generalize to Dataset class
    def __init__(self, datatype, topdir, skip_err=True, msb=True, tabulate=True, sort=True):
        super(IAMDataset, self).__init__(topdir, msb, tabulate, sort)
        
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
                # store samples in tree or list sorted lexicographically, or maybe multidim array
                # to each sample attach bboxes first indexed by line perhaps
                # maybe store preprocessed binary images in bboxes
                # for training words, each image will be a single word
        
        # postprocess sample set, sort keys and collapse into list(s) or nparray for better iteration
        self.sort_samples(msb, tabulate, sort)
    
    def word_sample(self, line, skip_err=True):
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
        