# Reads image marked as text and returns (annotates?) the text written in it
# Should receive a list of lines, identified as text, possibly straightened or binarized

# Source for model: https://arxiv.org/pdf/1507.05717.pdf

import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
import torch.autograd as ag
import tensorflow as tf
import editdistance as ed

from ..bbox import bbox as bb
from ..utils import imgprep as ip
# import textdataset as ds
# import textprep as pr
from .textenc import *

class TextRecognizer(bb.BBoxVisitor):
    
    def __init__(self, nh=256, encoding=None, lr=1e-3, par=True, path=None):
        '''
        Module to recognize written text in segments.
        nh: number of hidden states for LSTM (256)
        encoding: which range of characters to encode ['lower', 'alpha', 'lowerspace', 'alphaspace', 'all']
        lr: learning rate for Adam (1e-3)
        par: whether to use multiple cores to execute model (True)
        path: file to load pretrained model from, if provided (None)
        '''
        if encoding is None:
            encoding = LowerEncoding
        else:
            encoding = encodings[encoding]
        self.encoding = encoding()
        
        self.rec = TextRecModule(nh, len(self.encoding) + 1) # for blank character
        if par:
            self.rec = nn.DataParallel(self.rec)
        self.loss = nn.CTCLoss()
        self.loss1 = nn.CTCLoss(reduction='none') # to check if a sample from batch yields inf loss
        self.optim = optim.Adam(self.rec.parameters(), lr=lr)
        
        if path is not None:
            self.load(path)
            
    def visit_line(self, line, **kwargs):
        self.visit_children(line, **kwargs)
        # TODO combine the text read from each word in line
    
    def visit_word(self, word, image=None, binarize=True, normalize=False, straighten=False, *args, **kwargs):
        '''
        Given a word of text, infer and write the text written in it.
        Optional kwargs:
        image: the image of the note to which the line belongs, opened with cv2
        binarize, normalize, straighten etc.
        '''
        # obtain image of line, either as attribute or in kwargs
        image = self.get_image(word, image)
        
        # resize, binarize line etc.
        # possibly move these to another preprocessing module
        if binarize:
            image = ip.binarize(image, otsu=True) # text is supposed to be bimodal
        if normalize:
            pass
        if straighten:
            pass
        image = cv2.morphologyEx(image, cv2.MORPH_ERODE, np.ones((3,3), np.uint8))
        image = ip.rescale(image, h=32)
        
        # call infer on batch(es), either store returned list directly as lines or concatenate them in some way
        text, c = self.infer(image)
        # possibly some postprocessing, check spelling and punctuation
        word.annot.text = text
        word.c = c
    
    def encode(self, text):
        'Encode string into array of class numbers.'
        return np.array([self.encoding.encode(c) + 1 for c in text])
    
    def decode(self, l):
        'Decode array of class numbers into string.'
        return ''.join(self.encoding.decode(n - 1) for n in l if n != 0)
    
    def load(self, path):
        self.rec.load_state_dict(torch.load(path)) # later add conds for par and otherwise
    
    def save(self, path):
        torch.save(self.rec.state_dict(), path)
    
    def infer(self, inputs):
        if len(inputs.shape) == 2:
            reshape = True
            inputs = inputs.reshape((1,)+inputs.shape)
        n, h, w = inputs.shape
        with torch.no_grad():
            outputs = self.rec(ag.Variable(torch.Tensor(inputs.reshape(n,1,h,w))))
        
        # really didn't want to do this
        tf_inputs = tf.convert_to_tensor(outputs.detach().numpy())
        tf_seq_length = tf.convert_to_tensor([w//8]*n)
        dec = tf.nn.ctc_beam_search_decoder(tf_inputs, tf_seq_length)
        with tf.Session() as sess:
            out, logprobs = sess.run(dec)
        out = out[0]
        prob = np.exp(logprobs.sum(axis=-1))
        
        strs = [''] * n
        for ind, val in zip(out.indices, out.values):
            if val != 0:
                strs[ind[0]] += self.decode([val]) # inds [sample, character] sorted lexicographically
        
        if reshape:
            strs = strs[0]
        
        return strs, prob
    
    def validate(self, dataset, verbose=10, scores=True):
        if scores:
            scs = np.zeros(len(dataset))
        cost = 0
        i = 0
        for sam in dataset:
            try:
                cost = self.validatebatch(sam)
            except RuntimeError:
                if verbose:
                    print('Iteration %d threw exception' % i)
            if scores:
                scs[i] = cost
            i += 1
            if verbose:
                if not i % verbose:
                    print('Iteration %d: %f' % (i, cost))
        if scores:
            return scs
        
    def validatebatch(self, batch):
        # load batch
        bb = np.load(batch.path)
        bb = self.check(batch, bb)
        
        # infer 
        strs = self.infer(bb)
        
        # calculate edit distance to text
        dists = np.zeros(len(batch.lengths))
        pref = 0 # prefix sum
        for i, l in enumerate(batch.lengths):
            # text = self.decode(self.encode(batch.text[pref:pref+1]))
            dists[i] = ed.eval(strs[i], batch.text[pref:pref+1])
            pref += l
        
        return dists.mean()
    
    def train(self, dataset, eps=1, verbose=10, scores=True):
        if scores:
            scs = np.zeros(eps*len(dataset))
        cost = 0
        i = 0
        for ep in range(eps):
            for sam in dataset:
                try:
                    cost = self.trainbatch(sam)
                except RuntimeError:
                    if verbose:
                        print('Iteration %d threw exception' % i)
                if scores:
                    scs[i] = cost
                i += 1
                if verbose:
                    if not i % verbose:
                        print('Iteration %d: %f' % (i, cost))
        if scores:
            return scs
    
    def trainbatch(self, batch):
        # load batch
        bb = np.load(batch.path)
        
        bb = self.check(batch, bb)
        
        n, h, w = bb.shape
        input = ag.Variable(torch.Tensor(bb.reshape(n,1,h,w)))
        targets = ag.Variable(torch.IntTensor(self.encode(batch.text)))
        in_lengths = ag.Variable(torch.IntTensor([int(w/8)]*n))
        tar_lengths = ag.Variable(torch.IntTensor(batch.lengths))
        
        self.optim.zero_grad()
        output = self.rec(input)
        cost = self.loss(output, targets, in_lengths, tar_lengths)#/w
        
        if np.all(np.isfinite(cost.detach().numpy())):
            cost.backward()
            self.optim.step()
        
        return cost#*w

    def check(self, batch, bb):
        if batch.checked:
            return bb
        
        n, h, w = bb.shape
        input = ag.Variable(torch.Tensor(bb.reshape(n,1,h,w)))
        targets = ag.Variable(torch.IntTensor(self.encode(batch.text)))
        in_lengths = ag.Variable(torch.IntTensor([int(w/8)]*n))
        tar_lengths = ag.Variable(torch.IntTensor(batch.lengths))
        
        # run it forward once to see if any sample returns inf
        with torch.no_grad():
            output = self.rec(input)
            cost = self.loss1(output, targets, in_lengths, tar_lengths)
        infs = np.isinf(cost.detach().numpy())
        if not np.any(infs):
            batch.checked = True
            return bb
        
        # get indices of each inf cost
        infs = [int(a[0]) for a in np.argwhere(infs)]
        infs.sort(reverse=True) # needed in order to remove indices one by one
        
        # for each element in infs, remove it from batch, text and lengths
        bb1 = bb
        text1 = batch.text
        lengths1 = batch.lengths
        for ind in infs:
            bb1 = np.delete(bb1, ind, axis=0)
            text1 = text1[:lengths1[:ind].sum()] + text1[lengths1[:ind+1].sum():]
            lengths1 = np.delete(lengths1, ind)
        assert bb1.shape[0] == len(lengths1) and len(text1) == sum(lengths1)
        
        np.save(batch.path, bb1)
        batch.text = text1
        batch.lengths = lengths1
        batch.checked = True
        
        return bb1

class TextRecModule(nn.Module):
    def __init__(self, nh, ncl, nci=1, nc=64, nco=512, w=16):
        '''
        CRNN model for recognizing handwritten text.
        nh: dimension of hidden layer of lstm
        ncl: no of classes
        nci: no of channels of input data
        nc: no of channels of first conv layer
        nco: no of channels of last conv layer
        w: width of last conv layer (16 or 32)
        '''
        super(TextRecModule, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1), # (64,32,128)
            nn.ReLU(True),
            nn.MaxPool2d((2,2)), # (64,16,64)
            nn.Conv2d(64, 128, kernel_size=3, padding=1), # (128,16,64)
            nn.ReLU(True),
            nn.MaxPool2d((2,2)), # (128,8,32)
            nn.Conv2d(128, 256, kernel_size=3, padding=1), # (256,8,32)
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d((2,2)), # (256,4,w) w=16
            nn.Conv2d(256, 512, kernel_size=3, padding=1), # (512,4,w)
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d((2,2), (2,1), (0,1)), # (256,2,w)
            nn.Conv2d(512, 512, kernel_size=2, padding=0) # (256,1,w)
        )
        
        self.lstm = nn.LSTM(512, nh, num_layers=2, bidirectional=True)
        
        self.embed = nn.Linear(2*nh, ncl) # bidirectional layers concatenated
    
    def forward(self, input):
        conv = self.cnn(input)
        n, c, h, w = conv.size()
        assert h == 1
        conv = conv.squeeze(2).permute(2,0,1)
        # conv = torch.einsum('nchw->wnc', conv)
        
        lstm, _ = self.lstm(conv)
        w, n, nh = lstm.size()
        
        embed = self.embed(lstm.view(-1, nh))
        _, ncl = embed.size()
        return embed.view(w, n, ncl).log_softmax(2)