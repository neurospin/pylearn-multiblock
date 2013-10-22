# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 17:34:59 2013

@author: Tommy Löfstedt
@email: tommy.loefstedt@cea.fr
"""

__all__ = ['load']

import numpy as np
import structured.utils as utils
import structured.algorithms as algorithms


def load(l, k, density, snr, M, e, shape):
    """Returns data generated such that we know the exact solution.

    The data generated by this function is fit to the Linear regression + L1 +
    L2 loss function, i.e.:

        f(b) = (1 / 2).|Xb - y|² + l.|b|_1 + (k / 2).|b|²,

    where |.|_1 is the L1 norm and |.|² is the squared L2 norm.

    Parameters
    ----------
    l : The L1 regularisation parameter.

    k : The L2 regularisation parameter.

    density : The density of the returned regression vector (fraction of
            non-zero elements). Must be in (0, 1]. This may be approximate
            if no exact factors exist. E.g. if shape=(11,11) and
            density=0.2, then the closest density we actually get is 0.2066.

    snr : Signal to noise ratio between model and residual.

    M : The matrix to use when building data. This matrix carries the desired
            distribution of the generated data. The generated data will be a
            column-scaled version of this matrix.

    e : The error vector e = Xb - y. This vector carries the desired
            distribution of the residual.

    shape : A 2-list or -tuple with the shape (rows-by-columns) of the
            2D-structure.

    Returns
    -------
    X : The generated X matrix.

    y : The generated y vector.

    beta : The generated regression vector.
    """
    seed = np.random.randint(2147483648)

    low = 0.0
    high = 1.0
    for i in xrange(30):
        np.random.seed(seed)
        X, y, beta = _generate(l, k, density, high, M, e, shape)
        val = np.sqrt(np.sum(np.dot(X, beta) ** 2.0) / np.sum(e ** 2.0))
        if val > snr:
            break
        else:
            low = high
            high = high * 2.0

    def f(x):
        np.random.seed(seed)
        X, y, beta = _generate(l, k, density, x, M, e, shape)
        return np.sqrt(np.sum(np.dot(X, beta) ** 2.0) / np.sum(e ** 2.0)) - snr

    bm = algorithms.BisectionMethod(max_iter=20)
    bm.run(utils.AnonymousClass(f=f), low, high)

    np.random.seed(seed)
    X, y, beta = _generate(l, k, density, bm.x, M, e, shape)
    print "snr = %.5f = %.5f = |X.b| / |e| = %.5f / %.5f" \
            % (snr, np.linalg.norm(np.dot(X, beta) / np.linalg.norm(e)),
               np.linalg.norm(np.dot(X, beta)), np.linalg.norm(e))

    return X, y, beta
#    return _generate(l, density, snr, M, e)


def _generate(l1, l2, density, snr, M, e, shape):

    l1 = float(l1)
    l2 = float(l2)
    density = float(density)
    snr = float(snr)
    p = M.shape[1]

    px = shape[1]
    py = shape[0]
    pys, pxs = find_dense(density, shape)

    beta = np.zeros((py, px))
    for i in xrange(py):
        for j in xrange(px):
            if i < pys and j < pxs:
                beta[i, j] = U(0, 1) * snr / np.sqrt(pys * pxs)
            else:
                beta[i, j] = 0.0
#    beta = np.fliplr(np.sort(np.flipud(np.sort(beta, axis=0)), axis=1))

    X = np.zeros(M.shape)
    for i in xrange(py):
        for j in xrange(px):
            k = px * i + j
            Mte = np.dot(M[:, k].T, e)
            if abs(Mte) < utils.TOLERANCE:  # Avoid to make alpha very large
                Mte = 1.0
            alpha = 0.0

            # L1
            sign_beta = sign(beta[i, j])
            if i < pys and j < pxs:
                alpha += -l1 * sign_beta
            else:
                alpha += -l1 * U(-1, 1)

            # L2
            alpha += -l2 * beta[i, j]

            alpha /= Mte

            X[:, k] = alpha * M[:, k]

    beta = np.reshape(beta, (p, 1))
    y = np.dot(X, beta) - e

    return X, y, beta


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


def find_dense(density, shape):

    py = shape[0]
    px = shape[1]
    p = py * px
    s = np.sqrt(density * p / (px * py))
    part = s * s * px * py / p
    pys = int(round(py * s))
    pxs = int(round(px * s))
    # Search for better approximation of px and py
    best_x = 0
    best_y = 0
    best = float("inf")
    for i in xrange(-2, 3):
        for j in xrange(-2, 3):
            if pys + i < py and pxs + j < px:
                diff = abs(((pys + i) * (pxs + j) / float(p)) - part)
                if diff < best:
                    best = diff
                    best_x = j
                    best_y = i
    pys += best_y
    pxs += best_x

    return pys, pxs