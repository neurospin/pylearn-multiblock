# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 10:35:12 2013

@author: edouard.duchesnay@cea.fr

Generative model to sample input features (image) and the associated target
variable. Provide a model of the structure between the input features for
both noizy and informative features. The structure can be controled at pixel
level and at object (connected component of pixels) level.


Generative sampling model
-------------------------

The signal within each pixel i and object k is a linear combination of some
information and object-level and pixel-level noize.

x_ki =  b_y * y + b_o^1/2 * o_k + (1 - b_o)^1/2 * e_i
       < info >   <------------- noize ------------->
                  <- object k ->   <--- pixel i ---->

e_i ~ N(0, 1) is the pixel-level noize, for all pixels i in [1, n_features]
o_k ~ N(0, 1) is the object-level noize, for all objects k in [1, n_objects]
y   ~ N(0, 1) is the target variable

Procedure: (1) Generate e_i; (2) Spatial Smoothing; (3) Add object level noize;
(4) Add y on causal pixels.

Parameters
----------
b_o: float
    Controls the amount of shared noize within
    objects. It is null outside objects. Thus (1 - b_o) control the amount of
    pixel level noize. b_o enable the mixing between pixel and object level noize.

R: float
    Is the desire correlation between causal pixels and
    the target y.

Details
-------

b_y is null outside objects. Within causal object, it is computed such that
corr(x_ki, y) = R

Moreovere the model assume that:
var(noize) = b_o var(o_k) + (1 - b_o) var(e_ki) = 1
cov(y, noize) = 0

Predictive model
----------------

Given X = [x_ki] for all pixels i in [1, n_features], the function return
beta = (X'X)^-1 X'y, for the OLS solution of the problem: min|y - X beta|_l2

[X'X]_ij = n_sample * E(x_ki, x_lj)
E(x_ki, x_kj) = b_y^2 + b_o + (1 - b_o) * E(e_ki, e_lj)
                if i,j belong to the same causal object (k=l)
              =         b_o + (1 - b_o) * E(e_ki, e_lj)
                if i belongs to a causal object and j belongs to its suppressor
              = is not computed in all other cases.

E(e_ki, e_lj): spatial cov after spatial smoothing
              = Rij * sigma_e^2 + 2 mu_e
Rij: spatial correlation after spatial smoothing
     = Rij = exp(-dist_euc^2/(4 * sigma_spatial_smoothing^2) )


X'_i y = n_sample * E(x_ki, y)
E(x_ki, y) = b_y * E(y^2)


i: sample index
k: object index
j: pixel index

1. Build images with noize => e_ij
2. Build Objects
3. Apply causal model for each objects
   => add y_i beta_y + Zi Beta_z + o_ik beta_o
4. Smooth
"""

import numpy as np
import scipy
import scipy.linalg
from scipy import ndimage
import matplotlib.pyplot as plt
import scipy.sparse as sparse
import scipy.sparse.linalg


def covmat_indices(cols):
    """Return indices in covariance matrix given indice in a matrix. The
    order respect the flattening of the matrix.
    Example
    -------
    >>> covmat_indices([1, 3])
    (array([1, 1, 3, 3]), array([1, 3, 1, 3]))
    >>> # order respect the flattening of the matrix
    >>> m = np.array([[1, 2], [3, 4]])
    >>> np.all(m[covmat_indices([0, 1])] == m.ravel())
    True
    """
    cols = np.asarray(cols)
    x_coord = cols[:, np.newaxis] + np.zeros(cols.shape[0], dtype=int)
    y_coord = cols + np.zeros(cols.shape[0], dtype=int)[:, np.newaxis]
    return x_coord.ravel(), y_coord.ravel()


def corr_to_coef(v_x, v_e, cov_xe, R):
    """In a linear model y = bx + e. Calculate b such corr(bx + e, x) = R.
    Parameters
    ----------
    v_x: float
        var(x)

    v_e: float
        var(e)

    cov_xe: float
        cov(x, e)

    R: float
        The desire correlation

    Example
    -------
    b = corr_to_coef(1, 1, 0, .5)
    """
    b2 = v_x ** 2 * (R ** 2 - 1)
    b1 = 2 * cov_xe * v_x * (R ** 2 - 1)
    b0 = R ** 2 * v_x * v_e - cov_xe ** 2
    delta = b1 ** 2 - 4 * b2 * b0
    sol1 = (-b1 - np.sqrt(delta)) / (2 * b2)
    sol2 = (-b1 + np.sqrt(delta)) / (2 * b2)
    return np.max([sol1, sol2]) if R >= 0 else  np.min([sol1, sol2])


def corr_to_coef_empirical(x, e, R):
    """In a linear model y = bx + e. Calculate b such corr(bx + e, x) = R.
    Parameters
    ----------
    x: array of shape [n]
    e: array of shape [n]
    R: float
        The desire correlation

    Example
    -------
    import numpy as np
    e = np.random.normal(1, 10, 100)
    x = np.random.normal(4, 3, 100)
    b = corr_to_coef_empirical(x, e, .5)
    np.corrcoef(b * x + e, x)[0, 1]
    """
    v_x = np.var(x)
    v_e = np.var(e)
    cov_xe = np.cov(x, e)[0, 1]
    return corr_to_coef(v_x, v_e, cov_xe, R)

############################################################################
## utils


############################################################################
## Objects classes

class ObjImage(object):
    """
    Parameters:
    -----------
    c_x, c_y: Center of object

    im_x, im_y: int
        Image x and y dimensions.

    beta_y: float

    beta_z: array of float [1 x n_regressors]

    beta_o: float
    """
    def __init__(self, c_x, c_y, im_x, im_y):
        self.c_x = c_x
        self.c_y = c_y
        self.x_grid, self.y_grid = np.ogrid[0:im_x, 0:im_y]
        self.is_suppressor = False
        self.suppressor = None
    def set_suppresor(self, suppressor):
        suppressor.is_suppressor = True
        self.suppressor = suppressor
    def get_suppresor(self):
        return self.suppressor

class Square(ObjImage):
    def __init__(self, size, **kwargs):
        super(Square, self).__init__(**kwargs)
        self.size = size
    def get_mask(self):
        hs = self.size / 2
        mask = (np.abs(self.x_grid - self.c_x) <= hs) & \
        (np.abs(self.y_grid - self.c_y) <= hs)
        return mask

class Dot(ObjImage):
    def __init__(self, size, **kwargs):
        super(Dot, self).__init__(**kwargs)
        self.size = size
    def get_mask(self):
        mask = np.sqrt((self.x_grid - self.c_x) ** 2 + \
                       (self.y_grid - self.c_y) ** 2) <= self.size / 2
        return mask

class Dimaond(ObjImage):
    def __init__(self, size, **kwargs):
        super(Square, self).__init__(**kwargs)
        self.size = size
    def get_mask(self):
        mask = np.abs(self.x_grid - self.c_x) + \
        np.abs(self.y_grid - self.c_y) <= self.size / 2
        return mask

def get_objects_edges(objects):
    m = objects[0].get_mask()
    m[::] = False
    for o in objects:
            m += o.get_mask()
    md = ndimage.binary_dilation(m)
    return md - m

############################################################################
## Objects builder
def dice_five(lx, ly):
    s_obj = np.floor(lx / 7)
    objects = list()
    ## corner dots
    for k in [1, 3]:
        c_x = k * lx / 4.
        c_y = ly / 4.
        o_info = Dot(c_x=c_x, c_y=c_y, size=s_obj, im_x=lx, im_y=ly)
        objects.append(o_info)
        c_y = ly - (ly / 4.)
        o_supp = Dot(c_x=c_x, c_y=c_y, size=s_obj, im_x=lx, im_y=ly)
        objects.append(o_supp)
        o_info.set_suppresor(o_supp)
    ## dot in the middle
    c_x = lx / 2.
    c_y = ly / 2.
    o_info = Dot(c_x=c_x, c_y=c_y, size=s_obj, im_x=lx, im_y=ly)
    objects.append(o_info)
    return objects


############################################################################
## Sptial smoothing
def spatial_smoothing(Xim, sigma, mu_e, sigma_e):
    for i in xrange(Xim.shape[0]):
        Xim[i, :, :] = ndimage.gaussian_filter(Xim[i, :, :],
            sigma=sigma)
    X = Xim.reshape((Xim.shape[0], Xim.shape[1] * Xim.shape[2]))
    # Spatial smoothing reduced the std-dev, reset it to 1
    X -= X.mean(axis=0) + mu_e  # Also ensure null mean
    X /= X.std(axis=0) * sigma_e
    return Xim


############################################################################
## Add objects-based variance
def object_model(objects, Xim, beta_o, sigma_o):
    """Add object variance: x_ki =  b_o^1/2 * o_k + (1 - b_o)^1/2 * e_i
    """
    for k in xrange(len(objects)):
        o = objects[k]
        #print o.is_suppressor, o.suppressor
        if o.is_suppressor:
            continue
        # A) Add object latent variable
        mask_o = o.get_mask()
        o_ik = np.random.normal(0, sigma_o, Xim.shape[0])
        o_ik -= o_ik.mean()  # - 0
        o_ik /= o_ik.std() * sigma_o
        Xim[:, mask_o] = (np.sqrt(beta_o) * o_ik + \
                        np.sqrt(1 - beta_o) * Xim[:, mask_o].T).T
        if o.suppressor is not None:
            mask_o_suppr = o.suppressor.get_mask()
            Xim[:, mask_o_suppr] = (np.sqrt(beta_o) * o_ik + \
                       np.sqrt(1 - beta_o) * Xim[:, mask_o_suppr].T).T
#        X = Xim.reshape((Xim.shape[0], Xim.shape[1] * Xim.shape[2]))
#        # Spatial smoothing reduced the std-dev, reset it to 1
#        X -= X.mean(axis=0) + (mu_o + mu_e)  # Also ensure null mean
#        X /= X.std(axis=0) * sigma_e
    return Xim


############################################################################
## Apply causal model on objects
def causal_model(objects, Xim, y, R):
    """Add predictive information: x_ki +=  b_y * y
    """
    beta_y = corr_to_coef(v_x=1, v_e=1, cov_xe=0, R=R)
    for k in xrange(len(objects)):
        o = objects[k]
        if o.is_suppressor:
            continue
        # A) Add object latent variable
        mask_o = o.get_mask()
        # Compute the coeficient according to a desire correlation
        Xim[:, mask_o] = (Xim[:, mask_o].T + (beta_y * y)).T
    return Xim, beta_y


def model_parameters(Xim, sigma_spatial_smoothing,
                     sigma_e, sigma_y,
                     beta_o, beta_y,
                     objects, y):
    """Compute theoretical and empirical model parameters.
    Parameters
    ----------
    Xim: array [n_samples, lx, ly]

    sigma_e float
        noize std-dev

    objects: list of ObjImage

    Details
    -------
    Estimate (X'X)^-1 X'y for each object (consider suppressor object if
    present)
    CovX = b_y^2 + b_o + (1 - b_o) * CovN
    CovN = CorN * sigma_e ** 2 + 2 * mu_e
    CorN = e(-dist ** 2 / (4 * sigma_spatial_smoothing ** 2) )

    Return
    ------
    CovX: array [n_features, n_features]
        X covariance matrix

    covXy: array [n_features,]
        X, y covariance matrix
    """
    n_samples, lx, ly = Xim.shape
    n_features = lx * ly
    # build global mask of objects and image of objects label
    labels_im = np.zeros((lx, ly), dtype=int)  # image of objects label
    label = 0
    for k in xrange(len(objects)):
        label += 1
        io = objects[k]
        io.label = label
        labels_im[io.get_mask()] = label
    mask_im = labels_im != 0
    ij_im = np.where(mask_im)  # ij of objects in image
    i_flt = np.where(mask_im.ravel())[0]  # i of objects in flatten image
    # get euclidian distances between pixel in the selection
    Dist_sel = np.sqrt((ij_im[0][np.newaxis].T - ij_im[0]) ** 2 + \
        (ij_im[1][np.newaxis].T - ij_im[1]) ** 2)
    # True correlation between noize pixels: CorN_sel
    CorN_sel = np.exp(-Dist_sel ** 2 / (4 * sigma_spatial_smoothing ** 2))
    # True cov between noize pixels: CovN_sel
    CovN_sel = CorN_sel * sigma_e ** 2  # + 2 * mu_e = 0
    # True cov between pixels: Cov. Depends on o_k and y
    CovX_sel = np.zeros(CovN_sel.shape)
    i_allio_sel = list()  # indices of all informative objects in selection
    i_allio_flt = list()  # indices of all informative objects in flatten image
    for o in objects:
        #o = objects[0]
        if o.is_suppressor:
            continue
        # mask of informative object in selection
        mask_io_sel = labels_im[mask_im] == o.label
        # mask of all objects (informative+suppressor) in selection
        mask_all_sel = mask_io_sel.copy()
        if o.suppressor is not None:
            mask_all_sel += labels_im[mask_im] == o.suppressor.label
        # i of both objects in selection
        i_both_sel = np.where(mask_all_sel)[0]
        # i of object in selection cov mat
        i_both_sel_cov = covmat_indices(i_both_sel)
        # CovX = b_y^2 + b_o + (1 - b_o) * CovN
        CovX_sel[i_both_sel_cov] = beta_o + (1 - beta_o)\
                                   * CovN_sel[i_both_sel_cov]
        # store indices of informative object
        i_allio_sel += np.where(mask_io_sel)[0].tolist()
        i_allio_flt += np.where(labels_im.ravel() == o.label)[0].tolist()
    # Add cov caused by y in ALL informative object
    ij_allio_sel_cov = covmat_indices(i_allio_sel)
    #labels_im[mask_im][ij_io_sel]
    CovX_sel[ij_allio_sel_cov] += beta_y ** 2
    ## Compare with empirical cov
    CovX_sel_hat = np.cov(Xim[:, mask_im].T)
    if False:
        plt.plot(CovX_sel, CovX_sel_hat, "ob")
        plt.plot(CovX_sel[ij_allio_sel_cov], CovX_sel_hat[ij_allio_sel_cov],
                 "or")
        plt.plot([0, 1, 2], [0, 1, 2])
        plt.ylabel('Empirical (estimated) Cov(X)')
        plt.xlabel('Theroretical Cov(X) (red=between informative pixels)')
        plt.show()
        ## Cov(X,y) = b_y * E(y^2) if causal else 0
    covXy = np.zeros(n_features)
    covXy[i_allio_flt] = beta_y * (sigma_y ** 2)  # + mu_y ** 2)
    if False:
        covXy_hat = np.dot(Xim[:, mask_im].T, y) / n_samples
        plt.plot(covXy[i_flt], covXy_hat, "ob")
        plt.plot([0, 1], [0, 1])
        plt.ylabel('Empirical (estimated) Cov(X,y)')
        plt.xlabel('Theroretical Cov(X,y)')
        plt.show()
    # indices of pixels in cov of flatten image
    ij_flt_cov = covmat_indices(i_flt)
    CovXs = sparse.csr_matrix((CovX_sel.ravel(), ij_flt_cov),
                              shape=(n_features, n_features))
    # Add diagonal where non null
    diag = CovXs.diagonal()
    diag[diag == 0] = float(sigma_e) ** 2
    CovXs.setdiag(diag)
    return CovXs, covXy, labels_im


############################################################################
## Parameters
def make_regression(n_samples=1000, n_features=900, R = .5,
                    sigma_spatial_smoothing=1, beta_o = .5,
                    objects=None):
    sigma_y = sigma_e = sigma_o = 1 # items std-dev
    mu_e = mu_y = 0
    lx = ly = int(np.round(np.sqrt(n_features)))

    ##########################################################################
    ## 1. Build images with noize => e_ij
    X = np.random.normal(mu_e, sigma_e, n_samples * lx * ly).reshape(n_samples,
                                                                     lx * ly)
    Xim = X.reshape(n_samples, lx, ly)
    y = np.random.normal(mu_y, sigma_y, n_samples)
    y -= y.mean()
    y /= y.std()
    #print X.mean(axis=0), X.std(axis=0)

    ##########################################################################
    ## 1. Pixel-level noize structure: spatial smoothing
    Xim = spatial_smoothing(Xim, sigma_spatial_smoothing, mu_e, sigma_e)
    X = Xim.reshape((Xim.shape[0], Xim.shape[1] * Xim.shape[2]))
    #print X.mean(axis=0), X.std(axis=0)
    #print y.mean()

    ##########################################################################
    ## 2. Build Objects
    if objects is None:
        objects = dice_five(lx, ly)

    ##########################################################################
    ## 3. Object-level noize structure
    Xim = object_model(objects, Xim, beta_o, sigma_o)
    #X = Xim.reshape((Xim.shape[0], Xim.shape[1]*Xim.shape[2]))
    #print X.mean(axis=0), X.std(axis=0)

    ##########################################################################
    ## 4. Causal model
    Xim, beta_y = causal_model(objects, Xim, y, R)
    
    #X = Xim.reshape((Xim.shape[0], Xim.shape[1]*Xim.shape[2]))
    #print X.mean(axis=0), X.std(axis=0)

    ##########################################################################
    ## 6. Compute model parameters
    CovX, covXy, labels_im = model_parameters(Xim, sigma_spatial_smoothing,
                     sigma_e, sigma_y,
                     beta_o, beta_y,
                     objects, y)
    return Xim, y, CovX, covXy, labels_im


if __name__ == '__main__':
    # utils

    def plot_map(plot, im):
        #fig, ax = plt.subplots()
        cax = plot.matshow(im, cmap=plt.cm.coolwarm)
        mx = np.abs(im).max()
        cbar = plt.colorbar(cax, ticks=[-mx, -mx/4 -mx/2, 0, mx/2, mx/2, mx])
        cbar.set_clim(vmin=-mx, vmax=mx)
        #return fig, ax

    def sinv(M):
        lu_obj = scipy.sparse.linalg.splu(M.tocsr())
        Minv = lu_obj.solve(np.eye(M.shape[0]))
        return Minv

    n_samples = 1000
    n_features = 2500
    R = .5
    Xim, y, CovX, covXy, labels = make_regression(n_samples=n_samples,
                                          n_features=n_features, R=R,
                                          sigma_spatial_smoothing=1,
                                          beta_o=.5, objects=None)
    _, lx, ly = Xim.shape

    X = Xim.reshape((n_samples, lx * ly))
    import sklearn
    from sklearn.metrics import r2_score
    n_train = min(100, int(X.shape[1] / 10))
    Xtr = X[:n_train, :]
    ytr = y[:n_train]
    Xte = X[n_train:, :]
    yte = y[n_train:]

    plt.figure(figsize=(10, 10))
    plot = plt.subplot(231)
    cax = plot.matshow(labels)
    plt.title("Objects: 2 and 5 are suppressors")

    cor = np.dot(Xtr.T, ytr).reshape(lx, ly) / ytr.shape[0]
    plot = plt.subplot(232)
    plot_map(plot, cor)
    plt.title("Corr(X, y) on training data")

    plot = plt.subplot(233)
    weights = np.dot(sinv(CovX), covXy)
    pred = np.dot(Xte, weights)
    plot_map(plot, weights.reshape((lx, ly)))
    plt.title("Optimal weigths. test R2=%.2f" % r2_score(yte, pred))

    plot = plt.subplot(234)
    weights_hat = np.dot(scipy.linalg.pinv(Xtr), ytr)
    pred = np.dot(Xte, weights_hat)
    plot_map(plot, weights_hat.reshape((lx, ly)))
    plt.title("OLS weigths. test R2=%.2f" % r2_score(yte, pred))

    from sklearn.linear_model import Lasso
    from sklearn.linear_model import ElasticNet

    alpha = 0.1

    plot = plt.subplot(235)
    lasso = Lasso(alpha=alpha)
    pred = lasso.fit(Xtr, ytr).predict(Xte)
    plot_map(plot, lasso.coef_.reshape((lx, ly)))
    plt.title("Lasso weigths. test R2=%.2f" % r2_score(yte, pred))

    plot = plt.subplot(236)
    enet = ElasticNet(alpha=alpha, l1_ratio=0.1)
    pred = enet.fit(Xtr, ytr).predict(Xte)
    plot_map(plot, enet.coef_.reshape((lx, ly)))
    plt.title("ElasticNet weigths. test R2=%.2f" % r2_score(yte, pred))
    plt.show()

