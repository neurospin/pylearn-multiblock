# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 09:05:21 2013

@author:  Tommy Löfstedt
@email:   tommy.loefstedt@cea.fr
@license: BSD Style
"""

__all__ = ['Normalisation', 'NoNormalisation', 'UnitNormWeights',
           'UnitVarianceScores']

import abc
from multiblock.utils import norm, dot, sqrt


class Normalisation(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(Normalisation, self).__init__()

    @abc.abstractmethod
    def apply(self, w, X=None):
        raise NotImplementedError('Abstract method "apply" must be '\
                                  'specialised!')


class NoNormalisation(object):
    def __init__(self):
        super(NoNormalisation, self).__init__()

    def apply(self, w, X=None):
        return w


class UnitNormWeights(object):
    def __init__(self):
        super(UnitNormWeights, self).__init__()

    def apply(self, w, X=None):
        return w / norm(w)


class UnitVarianceScores(object):
    def __init__(self):
        super(UnitVarianceScores, self).__init__()

    def apply(self, w, X):
        w = w / norm(dot(X, w))
        w = w * sqrt(X.shape[0])  # N, number of elements in t = Xw
        return w