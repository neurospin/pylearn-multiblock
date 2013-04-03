# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 14:43:21 2013

@author:  Tommy Löfstedt
@email:   tommy.loefstedt@cea.fr
@license: BSD Style
"""

__all__ = ['Preprocess', 'Center', 'Scale']

import abc
from multiblock.utils import TOLERANCE


class PreprocessQueue(object):
    def __init__(self, pq):
        """ Preprocess queue.

        Arguments
        ---------
        pq : Either a PreprocessQueue, a list of Preprocess instances or an
             instance of Preprocess.
        """
        if isinstance(pq, (tuple, list)):
            for p in pq:
                if not isinstance(p, Preprocess):
                    raise ValueError('If argument "preprocess" is a list, it '\
                                     'must be a list of Preprocess instances')
            self.queue = pq
        elif isinstance(pq, PreprocessQueue):
            self.queue = pq.queue
        elif isinstance(pq, Preprocess):
            self.queue = [pq]
        else:
            raise ValueError('Argument "pq" must either be a PreprocessQueue,'\
                             ' a list of Preprocess instances or an instance '\
                             'of Preprocess')

    def process(self, X):
        for p in self.queue:
            X = p.process(X)
        return X

    def revert(self, X):
        for p in self.queue.reverse():
            X = p.revert(X)
        return X


class Preprocess(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        self.params = kwargs

    @abc.abstractmethod
    def process(self, X):
        raise NotImplementedError('Abstract method "process" must be '\
                                  'specialised!')

    @abc.abstractmethod
    def revert(self, X):
        raise NotImplementedError('Abstract method "revert" must be '\
                                  'specialised!')


class Center(Preprocess):

    def __init__(self, **kwargs):
        Preprocess.__init__(self, **kwargs)
        self.means = None

    def process(self, X):
        """ Centers the numpy array in X

        Arguments
        ---------
        X : The matrix to center

        Returns
        -------
        Centered X
        """

        if self.means == None:
            self.means = X.mean(axis=0)
        X = X - self.means

        return X

    def revert(self, X):
        """ Un-centers the previously centered numpy array in X

        Arguments
        ---------
        X : The matrix to center

        Returns
        -------
        Un-centered X
        """

        if self.means == None:
            raise ValueError('The method "process" must be applied before ' \
                             '"revert" can be applied.')

        X = X + self.means

        return X


class Scale(Preprocess):

    def __init__(self, **kwargs):
        Preprocess.__init__(self, **kwargs)
        self.centered = kwargs.pop('centered', True)
        self.stds = None

    def process(self, X):
        """ Scales the numpy array in X to standard deviation 1

        Arguments
        ---------
        X : The matrix to scale

        Returns
        -------
        Scaled X
        """

        if self.stds == None:
            ddof = 1 if self.centered else 0
            self.stds = X.std(axis=0, ddof=ddof)
            self.stds[self.stds < TOLERANCE] = 1.0

        X = X / self.stds

        return X

    def revert(self, X):
        """ Un-scales the previously scaled numpy array in X to standard
        deviation 1

        Arguments
        ---------
        X : The matrix to un-scale

        Returns
        -------
        Un-scaled X
        """

        if self.stds == None:
            raise ValueError('The method "process" must be applied before ' \
                             '"revert" can be applied.')

        X = X * self.stds

        return X