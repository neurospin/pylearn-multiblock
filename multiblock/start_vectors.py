# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 15:35:26 2013

@author:  Tommy Löfstedt
@email:   tommy.loefstedt@cea.fr
@license: BSD Style
"""

__all__ = ['BaseStartVector', 'RandomStartVector', 'OnesStartVector',
           'LargestStartVector']

import abc
import numpy as np
from multiblock.utils import norm


class BaseStartVector(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, normalise=True):
        super(BaseStartVector, self).__init__()

        self.normalise = normalise

    @abc.abstractmethod
    def get_vector(self, X=None, shape=None):
        raise NotImplementedError('Abstract method "getVector" must be '\
                                  'specialised!')


class RandomStartVector(BaseStartVector):
    def __init__(self):
        super(RandomStartVector, self).__init__()

    def get_vector(self, X=None, shape=None):
        if X == None and shape == None:
            raise ValueError('Either a matrix X or the shape must be given')
        if X != None:
            shape = (X.shape[1], 1)

        w = np.random.rand(*shape)  # Random start vector

        if self.normalise:
            return w / norm(w)
        else:
            return w


class OnesStartVector(BaseStartVector):
    def __init__(self):
        super(OnesStartVector, self).__init__()

    def get_vector(self, X=None, shape=None):
        if X == None and shape == None:
            raise ValueError('Either a matrix X or the shape must be given')
        if X != None:
            shape = (X.shape[1], 1)

        w = np.ones(shape)  # Using a vector of ones

        if self.normalise:
            return w / norm(w)
        else:
            return w


class ZerosStartVector(BaseStartVector):
    def __init__(self):
        super(ZerosStartVector, self).__init__()

    def get_vector(self, X=None, shape=None):
        if X == None and shape == None:
            raise ValueError('Either a matrix X or the shape must be given')
        if X != None:
            shape = (X.shape[1], 1)

        w = np.zeros(shape)  # Using a vector of zeros

        if self.normalise:
            return w / norm(w)
        else:
            return w


class LargestStartVector(BaseStartVector):

    def __init__(self, axis=1, normalise=True):
#        BaseStartVector.__init__(self, size=None, normalise=normalise)
        super(LargestStartVector, self).__init__(normalise=normalise)
        self.axis = axis

    def get_vector(self, X):
        idx = np.argmax(np.sum(X ** 2, axis=self.axis))
        if self.axis == 0:
            w = X[:, [idx]]  # Using column with largest sum of squares
        else:
            w = X[[idx], :].T  # Using row with largest sum of squares

        if self.normalise:
            return w / norm(w)
        else:
            return w