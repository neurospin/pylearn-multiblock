# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 14:16:37 2013

@author: Tommy Löfstedt
@email: tommy.loefstedt@cea.fr
"""

__all__ = ['load']

import numpy as np
import structured.utils as utils
#import structured.algorithms as algorithms


def load(l, k, g, beta, M, e, Aa):
    """Returns data generated such that we know the exact solution.

    The data generated by this function is fit to the Linear regression + L1 +
    L2 + Smoothed total variation function, i.e.:

        f(b) = (1 / 2).|Xb - y|² + l.|b|_1 + (k / 2).|b|² + g.TVmu(b),

    where |.|_1 is the L1 norm, |.|² is the squared L2 norm and TVmu is the
    smoothed total variation penalty.

    Parameters
    ----------
    l : The L1 regularisation parameter.

    k : The L2 regularisation parameter.

    g : The total variation regularisation parameter.

    beta : The regression vector to generate data from.

    M : The matrix to use when building data. This matrix carries the desired
            distribution of the generated data. The generated data will be a
            column-scaled version of this matrix.

    e : The error vector e = Xb - y. This vector carries the desired
            distribution of the residual.

    Aa : The gradient of the total variation loss function, without the
            regularisation constant.

    Returns
    -------
    X : The generated X matrix.

    y : The generated y vector.
    """

#    density : The density of the returned regression vector (fraction of
#            non-zero elements). Must be in (0, 1].
#
#    snr : Signal to noise ratio between model and residual.
#
#    beta : The generated regression vector.

#    seed = np.random.randint(2147483648)
#
#    low = 0.0
#    high = 1.0
#    for i in xrange(30):
#        np.random.seed(seed)
#        X, y, beta = _generate(l, k, g, density, high, M, e, tv, mu)
#        val = np.sqrt(np.sum(np.dot(X, beta) ** 2.0) / np.sum(e ** 2.0))
#        if val > snr:
#            break
#        else:
#            low = high
#            high = high * 2.0
#
#    def f(x):
#        np.random.seed(seed)
#        X, y, beta = _generate(l, k, g, density, x, M, e, tv, mu)
#        return np.sqrt(np.sum(np.dot(X, beta) ** 2.0) / np.sum(e ** 2.0)) - snr
#
#    bm = algorithms.BisectionMethod(max_iter=20)
#    bm.run(utils.AnonymousClass(f=f), low, high)
#
#    np.random.seed(seed)
#    X, y, beta = _generate(l, k, g, density, bm.x, M, e, tv, mu)
#    print "snr = %.5f = %.5f = |X.b| / |e| = %.5f / %.5f" \
#            % (snr, np.linalg.norm(np.dot(X, beta) / np.linalg.norm(e)),
#               np.linalg.norm(np.dot(X, beta)), np.linalg.norm(e))
#
#    return X, y, beta
    return _generate(l, k, g, beta, M, e, Aa)


def _generate(l1, l2, gamma, beta, M, e, Aa):

    l1 = float(l1)
    l2 = float(l2)
    gamma = float(gamma)
#    density = float(density)
#    snr = float(snr)
#    mu = float(mu)
    p = M.shape[1]
#    ps = int(round(p * density))

#    beta = np.zeros((p, 1))
#    for i in xrange(p):
#        if i < ps:
#            beta[i, 0] = U(0, 1) * snr / np.sqrt(ps)
#        else:
#            beta[i, 0] = 0.0
#    beta = np.flipud(np.sort(beta, axis=0))
#
#    alpha_sqsum = 0.0
#    for a in tv.alpha(beta, mu):
#        alpha_sqsum += np.sum(a ** 2.0)
#    Aa = tv.Aa(tv.alpha(beta, mu))

    X = np.zeros(M.shape)
    for i in xrange(p):
        Mte = np.dot(M[:, i].T, e)

        alpha = 0.0

        # L1
#        if i < ps:
        if abs(beta[i, 0]) > utils.TOLERANCE:
            alpha += -l1 * sign(beta[i, 0])
        else:
            alpha += -l1 * U(-1, 1)

        # L2
        alpha += -l2 * beta[i, 0]

        # TV
        alpha += -gamma * Aa[i, 0]

        alpha /= Mte

        X[:, i] = alpha * M[:, i]

    y = np.dot(X, beta) - e

    return X, y


def U(a, b):
    t = max(a, b)
    a = float(min(a, b))
    b = float(t)
    return (np.random.rand() * (b - a)) + a


def sign(x):
    if x > 0:
        return 1.0
    elif x < 0:
        return -1.0
    else:
        return 0.0