# -*- coding: utf-8 -*-
"""
Created on Thu Feb 8 09:22:00 2013

@author:  Tommy Löfstedt and Edouard Duchesnay
@email:   lofstedt.tommy@gmail.com, edouard.duchesnay@cea.fr
@license: BSD 3-clause.
"""
import maths
import consts

from .utils import time_cpu, time_wall, deprecated, approx_grad
from .utils import optimal_shrinkage, AnonymousClass, Enum
from .utils import LimitedDict, Info
from .check_arrays import check_arrays
from .plot import plot_map2d
from .classif_label import class_weight_to_sample_weight, check_labels


__all__ = ["maths", "consts",
           "time_cpu", "time_wall", "deprecated", "approx_grad",
           "check_arrays",
           "optimal_shrinkage", "AnonymousClass", "Enum",
           "plot_map2d",
           "class_weight_to_sample_weight", "check_labels",
           "LimitedDict", "Info"
          ]