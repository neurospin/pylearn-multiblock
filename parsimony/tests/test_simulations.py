# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 15:28:08 2014

@author:  Tommy Löfstedt
@email:   lofstedt.tommy@gmail.com
@license: BSD 3-clause.
"""
import unittest
from nose.tools import assert_less, assert_equal

import numpy as np
import matplotlib.pyplot as plot

from tests import TestCase


class TestSimulations(TestCase):

    def test_linear_regression_l1_l2_tv(self):

        from parsimony.functions.losses import LinearRegression
        from parsimony.functions.losses import RidgeRegression
        from parsimony.functions.penalties import L1
        from parsimony.functions.penalties import L2
        import parsimony.functions.nesterov.tv as tv
        from parsimony.functions import CombinedFunction
        import parsimony.datasets.simulated.l1_l2_tv as l1_l2_tv
        import parsimony.datasets.simulated.l1_l2_tvmu as l1_l2_tvmu
        import parsimony.algorithms.explicit as explicit
        import parsimony.start_vectors as start_vectors

        start_vector = start_vectors.RandomStartVector(normalise=True)

        np.random.seed(42)

        px = 4
        py = 4
        pz = 1
        shape = (pz, py, px)
        n, p = 50, np.prod(shape)

        alpha = 1.0
        Sigma = alpha * np.eye(p, p) \
              + (1.0 - alpha) * np.random.randn(p, p)
        mean = np.zeros(p)
        M = np.random.multivariate_normal(mean, Sigma, n)
        e = np.random.randn(n, 1)

        beta = start_vector.get_vector((p, 1))
        beta = np.sort(beta, axis=0)
        beta[0:5, :] = 0.0

#        print beta

        l = 0.618
        k = 1.0 - l
        g = 1.618

        A, _ = tv.A_from_shape(shape)
        snr = 100.0
        eps = 1e-8
        mus = [5e-2, 5e-4, 5e-6, 5e-8]
        mu = mus[-1]

        X, y, beta_star = l1_l2_tvmu.load(l=l, k=k, g=g, beta=beta, M=M, e=e,
                                          A=A, mu=mu, snr=snr, intercept=False)

        max_iter = 1000
        errs = []
        effs = []
        v = g
#        print "opt:", v
        lagranges = np.linspace(v * 0.95, v, 2).tolist()[:-1] \
                  + np.linspace(v, v * 1.05, 2).tolist()
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            beta_start = start_vector.get_vector((p, 1))

            beta_nonsmooth_penalty = beta_start
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(LinearRegression(X, y, mean=False))
                function.add_penalty(tv.TotalVariation(l=L, A=A, mu=mu,
                                                       penalty_start=0))
                function.add_penalty(L2(k))
                function.add_prox(L1(l))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star)
            effs.append(eff)

#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 5e-10,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 5e-16,
                    msg="Error is too large!")
#        plot.show()

        # TODO: Note done. Add more!!

#        mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#        print "mse:", mse
#        assert_less(mse, 1e-5, "The found regression vector is not correct.")
#
#        f_nonsmooth_star = function.f(beta_star)
#        f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#        err = abs(f_nonsmooth_penalty - f_nonsmooth_star) / f_nonsmooth_star
#        print "err:", err
#        assert_less(err, 1e-3, "The found regression vector does not give " \
#                               "the correct function value.")
#
#        beta_nonsmooth_rr = beta_start
#        for mu in mus:
#            function = CombinedFunction()
#            function.add_function(RidgeRegression(X, y, k))
#            function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
#                                                   penalty_start=0))
#            function.add_prox(L1(l))
#            beta_nonsmooth_rr = fista.run(function, beta_nonsmooth_rr)
#
#        mse = (np.linalg.norm(beta_nonsmooth_rr - beta_star) ** 2.0) / p
##        print "mse:", mse
#        assert_less(mse, 1e-5, "The found regression vector is not correct.")
#
#        f_nonsmooth_star = function.f(beta_star)
#        f_nonsmooth_rr = function.f(beta_nonsmooth_rr)
#        err = abs(f_nonsmooth_rr - f_nonsmooth_star)
##        print "err:", err
#        assert_less(err, 1e-3, "The found regression vector does not give " \
#                               "the correct function value.")
#
#        mu_min = mus[-1]
#        X, y, beta_star = l1_l2_tvmu.load(l=l, k=k, g=g, beta=beta, M=M, e=e,
#                                          A=A, mu=mu_min, snr=snr)
#        beta_smooth_penalty = beta_start
#        for mu in mus:
#            function = CombinedFunction()
#            function.add_function(LinearRegression(X, y, mean=False))
#            function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
#                                                   penalty_start=0))
#            function.add_penalty(L2(k))
#            function.add_prox(L1(l))
#            beta_smooth_penalty = \
#                    fista.run(function, beta_smooth_penalty)
#
#        mse = (np.linalg.norm(beta_smooth_penalty - beta_star) ** 2.0) / p
##        print "mse:", mse
#        assert_less(mse, 1e-5, "The found regression vector is not correct.")
#
#        f_smooth_star = function.f(beta_star)
#        f_smooth_penalty = function.f(beta_smooth_penalty)
#        err = abs(f_smooth_penalty - f_smooth_star)
##        print "err:", err
#        assert_less(err, 1e-3, "The found regression vector does not give " \
#                               "the correct function value.")
#
#        beta_smooth_rr = beta_start
#        for mu in mus:
#            function = CombinedFunction()
#            function.add_function(RidgeRegression(X, y, k))
#            function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
#                                                   penalty_start=0))
#            function.add_prox(L1(l))
#            beta_smooth_rr = fista.run(function, beta_smooth_rr)
#
#        mse = (np.linalg.norm(beta_smooth_rr - beta_star) ** 2.0) / p
##        print "mse:", mse
#        assert_less(mse, 1e-5, "The found regression vector is not correct.")
#
#        f_smooth_star = function.f(beta_star)
#        f_smooth_rr = function.f(beta_smooth_rr)
#        err = abs(f_smooth_rr - f_smooth_star)
##        print "err:", err
#        assert_less(err, 1e-3, "The found regression vector does not give " \
#                               "the correct function value.")

    def test_linear_regression_l1_l2_tv_intercept(self):

        from parsimony.functions.losses import LinearRegression
        from parsimony.functions.losses import RidgeRegression
        from parsimony.functions.penalties import L1
        from parsimony.functions.penalties import L2
        import parsimony.functions.nesterov.tv as tv
        from parsimony.functions import CombinedFunction
#        import parsimony.datasets.simulated.l1_l2_tv as l1_l2_tv
        import parsimony.datasets.simulated.l1_l2_tvmu as l1_l2_tvmu
        import parsimony.algorithms.explicit as explicit
        import parsimony.start_vectors as start_vectors
        import parsimony.estimators as estimators
        from parsimony.functions import RR_L1_TV

        start_vector = start_vectors.RandomStartVector(normalise=True)

        np.random.seed(42)

        px = 4
        py = 4
        pz = 4
        shape = (pz, py, px)
        n, p = 50, np.prod(shape) + 1

        alpha = 1.0
        Sigma = alpha * np.eye(p - 1, p - 1) \
              + (1.0 - alpha) * np.random.randn(p - 1, p - 1)
        mean = np.zeros(p - 1)
        X0 = np.random.multivariate_normal(mean, Sigma, n)
        M = np.hstack((np.ones((n, 1)), X0))
        e = 0.1 * np.random.randn(n, 1)

        beta = start_vector.get_vector((p, 1))
        beta = np.sort(beta, axis=0)
        beta[0:5, :] = 0.0
        beta = np.flipud(beta)

        l = 0.618
        k = 1.0 - l
        g = 1.618

        A, _ = tv.A_from_shape(shape)
        snr = 100.0
        eps = 1e-8
        mus = [5e-2, 5e-4, 5e-6, 5e-8]
        mu = mus[-1]

        X, y, beta_star = l1_l2_tvmu.load(l=l, k=k, g=g, beta=beta, M=M, e=e,
                                          A=A, mu=mu, snr=snr, intercept=True)

        max_iter = 750
        errs = []
        effs = []
        v = l
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(LinearRegression(X, y, mean=False))
                function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
                                                       penalty_start=1))
                function.add_penalty(L2(k, penalty_start=1))
                function.add_prox(L1(L, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.0065,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 5e-05,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 1300
        errs = []
        effs = []
        v = k
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(LinearRegression(X, y, mean=False))
                function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
                                                       penalty_start=1))
                function.add_penalty(L2(L, penalty_start=1))
                function.add_prox(L1(l, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.000351,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 1.0e-07,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 1300
        errs = []
        effs = []
        v = k
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(RidgeRegression(X, y, L,
                                                      penalty_start=1,
                                                      mean=False))
                function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
                                                       penalty_start=1))
                function.add_prox(L1(l, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.000351,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 1.0e-07,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 750
        errs = []
        effs = []
        v = g
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(LinearRegression(X, y, mean=False))
                function.add_penalty(tv.TotalVariation(l=L, A=A, mu=mu,
                                                       penalty_start=1))
                function.add_penalty(L2(k, penalty_start=1))
                function.add_prox(L1(l, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.0060508,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 5e-05,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 5000
        estimator = estimators.RidgeRegression_L1_TV(k, l, g,
                     A, mu=mu,
                     output=False,
                     algorithm=explicit.FISTA(eps=eps, max_iter=max_iter),
                     penalty_start=1,
                     mean=False)
        estimator.fit(X, y)
        function = RR_L1_TV(X, y, k, l, g, A=A, mu=estimator.mu,
                            penalty_start=1)

        err = np.linalg.norm(estimator.beta - beta_star) \
                    / np.linalg.norm(beta_star)
#        print err
        assert_less(err, 0.25, msg="The found minimum is not correct!")

        f_star = function.f(beta_star)
        f_penalty = function.f(estimator.beta)
        eff = abs(f_penalty - f_star) / f_star
#        print eff
        assert_less(eff, 0.27, msg="Error is too large!")

    def test_linear_regression_l1_l2_gl_intercept(self):

        from parsimony.functions.losses import LinearRegression
        from parsimony.functions.losses import RidgeRegression
        from parsimony.functions.penalties import L1
        from parsimony.functions.penalties import L2
        import parsimony.functions.nesterov.gl as gl
        from parsimony.functions import CombinedFunction
#        import parsimony.datasets.simulated.l1_l2_tv as l1_l2_tv
        import parsimony.datasets.simulated.l1_l2_glmu as l1_l2_glmu
        import parsimony.algorithms.explicit as explicit
        import parsimony.start_vectors as start_vectors
        import parsimony.estimators as estimators
        from parsimony.functions import RR_L1_GL

        start_vector = start_vectors.RandomStartVector(normalise=True)

        np.random.seed(42)

        px = 4
        py = 4
        pz = 4
        shape = (pz, py, px)
        n, p = 50, np.prod(shape) + 1

        alpha = 1.0
        Sigma = alpha * np.eye(p - 1, p - 1) \
              + (1.0 - alpha) * np.random.randn(p - 1, p - 1)
        mean = np.zeros(p - 1)
        X0 = np.random.multivariate_normal(mean, Sigma, n)
        M = np.hstack((np.ones((n, 1)), X0))
        e = 0.1 * np.random.randn(n, 1)

        beta = start_vector.get_vector((p, 1))
        beta = np.sort(beta, axis=0)
        beta[0:5, :] = 0.0
        beta = np.flipud(beta)

        l = 0.618
        k = 1.0 - l
        g = 1.618

        groups = [range(0, 2 * p / 3), range(p / 3, p - 1)]
        A = gl.A_from_groups(p - 1, groups=groups)

        snr = 100.0
        eps = 1e-8
        mus = [5e-2, 5e-4, 5e-6, 5e-8]
        mu = mus[-1]

        X, y, beta_star = l1_l2_glmu.load(l=l, k=k, g=g, beta=beta, M=M, e=e,
                                          A=A, mu=mu, snr=snr, intercept=True)

        max_iter = 2000
        errs = []
        effs = []
        v = l
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(LinearRegression(X, y, mean=False))
                function.add_penalty(gl.GroupLassoOverlap(l=g, A=A, mu=mu,
                                                          penalty_start=1))
                function.add_penalty(L2(k, penalty_start=1))
                function.add_prox(L1(L, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.010326,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 5e-05,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 2500
        errs = []
        effs = []
        v = k
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(LinearRegression(X, y, mean=False))
                function.add_penalty(gl.GroupLassoOverlap(l=g, A=A, mu=mu,
                                                          penalty_start=1))
                function.add_penalty(L2(L, penalty_start=1))
                function.add_prox(L1(l, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.001130,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 5e-07,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 2500
        errs = []
        effs = []
        v = k
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(RidgeRegression(X, y, L,
                                                      penalty_start=1,
                                                      mean=False))
                function.add_penalty(gl.GroupLassoOverlap(l=g, A=A, mu=mu,
                                                          penalty_start=1))
                function.add_prox(L1(l, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.000982,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 1e-07,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 2000
        errs = []
        effs = []
        v = g
#        print "opt:", v
        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
                  + np.linspace(v, v * 1.5, 3).tolist()
        beta_start = start_vector.get_vector((p, 1))
        beta_nonsmooth_penalty = beta_start
        for L in lagranges:
            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
            function = None
            for mu in mus:
                function = CombinedFunction()
                function.add_function(LinearRegression(X, y, mean=False))
                function.add_penalty(gl.GroupLassoOverlap(l=L, A=A, mu=mu,
                                                          penalty_start=1))
                function.add_penalty(L2(k, penalty_start=1))
                function.add_prox(L1(l, penalty_start=1))
                beta_nonsmooth_penalty = \
                        fista.run(function, beta_nonsmooth_penalty)

            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
                    / np.linalg.norm(beta_star)
            errs.append(mse)

            f_nonsmooth_star = function.f(beta_star)
            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
                        / f_nonsmooth_star
            effs.append(eff)

#        print lagranges
#        plot.subplot(2, 1, 1)
#        plot.plot(lagranges, errs)
#        print lagranges[np.argmin(errs)]
        assert_equal(lagranges[np.argmin(errs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(errs)
        assert_less(np.min(errs), 0.017904,
                    msg="Error is too large!")
#        plot.subplot(2, 1, 2)
#        plot.plot(lagranges, effs)
#        print lagranges[np.argmin(effs)]
        assert_equal(lagranges[np.argmin(effs)], v,
                               msg="The found minimum is not correct!")
#        print np.min(effs)
        assert_less(np.min(effs), 5e-05,
                    msg="Error is too large!")
#        plot.show()

        max_iter = 2500
        estimator = estimators.RidgeRegression_L1_GL(k, l, g,
                     A, mu=mu,
                     output=False,
                     algorithm=explicit.FISTA(eps=eps, max_iter=max_iter),
                     penalty_start=1,
                     mean=False)
        estimator.fit(X, y)
        function = RR_L1_GL(X, y, k, l, g, A=A, mu=estimator.mu,
                            penalty_start=1)

        err = np.linalg.norm(estimator.beta - beta_star) \
                / np.linalg.norm(beta_star)
#        print err
        assert_less(err, 0.47, msg="The found minimum is not correct!")

        f_star = function.f(beta_star)
        f_penalty = function.f(estimator.beta)
        eff = abs(f_penalty - f_star) / f_star
#        print eff
        assert_less(eff, 0.17, msg="Error is too large!")

#    def test_logistic_regression_l1_l2_tv_intercept(self):
#
#        from parsimony.functions.losses import LogisticRegression
#        from parsimony.functions.losses import RidgeLogisticRegression
#        from parsimony.functions.penalties import L1
#        from parsimony.functions.penalties import L2
#        import parsimony.functions.nesterov.tv as tv
#        from parsimony.functions import CombinedFunction
##        import parsimony.datasets.simulated.l1_l2_tv as l1_l2_tv
#        import parsimony.datasets.simulated.l1_l2_tvmu as l1_l2_tvmu
#        import parsimony.algorithms.explicit as explicit
#        import parsimony.start_vectors as start_vectors
#        import parsimony.estimators as estimators
#        from parsimony.functions import RR_L1_TV
#
#        start_vector = start_vectors.RandomStartVector(normalise=True)
#
#        np.random.seed(42)
#
#        px = 4
#        py = 4
#        pz = 4
#        shape = (pz, py, px)
#        n, p = 50, np.prod(shape) + 1
#
#        alpha = 1.0
#        Sigma = alpha * np.eye(p - 1, p - 1) \
#              + (1.0 - alpha) * np.random.randn(p - 1, p - 1)
#        mean = np.zeros(p - 1)
#        X0 = np.random.multivariate_normal(mean, Sigma, n)
#        M = np.hstack((np.ones((n, 1)), X0))
#        e = 0.1 * np.random.randn(n, 1)
#
#        beta = start_vector.get_vector((p, 1))
#        beta = np.sort(beta, axis=0)
#        beta[0:5, :] = 0.0
#        beta = np.flipud(beta)
#
#        l = 0.618
#        k = 1.0 - l
#        g = 1.618
#
#        A, _ = tv.A_from_shape(shape)
#        snr = 100.0
#        eps = 1e-8
#        mus = [5e-2, 5e-4, 5e-6, 5e-8]
#        mu = mus[-1]
#
#        X, y, beta_star = l1_l2_tvmu.load(l=l, k=k, g=g, beta=beta, M=M, e=e,
#                                          A=A, mu=mu, snr=snr, intercept=True)
#
#        max_iter = 750
#        errs = []
#        effs = []
#        v = l
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(LinearRegression(X, y, mean=False))
#                function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
#                                                       penalty_start=1))
#                function.add_penalty(L2(k, penalty_start=1))
#                function.add_prox(L1(L, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.0065,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 5e-05,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 1300
#        errs = []
#        effs = []
#        v = k
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(LinearRegression(X, y, mean=False))
#                function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
#                                                       penalty_start=1))
#                function.add_penalty(L2(L, penalty_start=1))
#                function.add_prox(L1(l, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.000351,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 1.0e-07,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 1300
#        errs = []
#        effs = []
#        v = k
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(RidgeRegression(X, y, L,
#                                                      penalty_start=1))
#                function.add_penalty(tv.TotalVariation(l=g, A=A, mu=mu,
#                                                       penalty_start=1))
#                function.add_prox(L1(l, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.000351,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 1.0e-07,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 750
#        errs = []
#        effs = []
#        v = g
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(LinearRegression(X, y, mean=False))
#                function.add_penalty(tv.TotalVariation(l=L, A=A, mu=mu,
#                                                       penalty_start=1))
#                function.add_penalty(L2(k, penalty_start=1))
#                function.add_prox(L1(l, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.0060508,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 5e-05,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 5000
#        estimator = estimators.RidgeRegression_L1_TV(k, l, g,
#                     A, mu=mu,
#                     output=False,
#                     algorithm=explicit.FISTA(eps=eps, max_iter=max_iter),
#                     penalty_start=1)
#        estimator.fit(X, y)
#        function = RR_L1_TV(X, y, k, l, g, A=A, mu=estimator.mu,
#                            penalty_start=1)
#
#        err = np.linalg.norm(estimator.beta - beta_star) \
#                    / np.linalg.norm(beta_star)
##        print err
#        assert_less(err, 0.25, msg="The found minimum is not correct!")
#
#        f_star = function.f(beta_star)
#        f_penalty = function.f(estimator.beta)
#        eff = abs(f_penalty - f_star) / f_star
##        print eff
#        assert_less(eff, 0.27, msg="Error is too large!")
#
#    def test_logistic_regression_l1_l2_gl_intercept(self):
#
#        from parsimony.functions.losses import LogisticRegression
#        from parsimony.functions.losses import RidgeLogisticRegression
#        import parsimony.estimators as estimators
#        from parsimony.functions.penalties import L1
#        from parsimony.functions.penalties import L2
#        import parsimony.functions.nesterov.gl as gl
#        from parsimony.functions import CombinedFunction
#        import parsimony.datasets.simulated.l1_l2_glmu as l1_l2_glmu
#        import parsimony.algorithms.explicit as explicit
#        import parsimony.start_vectors as start_vectors
#        from parsimony.functions import RR_L1_GL
#
#        start_vector = start_vectors.RandomStartVector(normalise=True)
#
#        np.random.seed(42)
#
#        px = 4
#        py = 4
#        pz = 4
#        shape = (pz, py, px)
#        n, p = 50, np.prod(shape) + 1
#
#        alpha = 1.0
#        Sigma = alpha * np.eye(p - 1, p - 1) \
#              + (1.0 - alpha) * np.random.randn(p - 1, p - 1)
#        mean = np.zeros(p - 1)
#        X0 = np.random.multivariate_normal(mean, Sigma, n)
#        M = np.hstack((np.ones((n, 1)), X0))
#        e = 0.1 * np.random.randn(n, 1)
#
#        beta = start_vector.get_vector((p, 1))
#        beta = np.sort(beta, axis=0)
#        beta[0:5, :] = 0.0
#        beta = np.flipud(beta)
#
#        l = 0.618
#        k = 1.0 - l
#        g = 1.618
#
#        groups = [range(0, 2 * p / 3), range(p / 3, p - 1)]
#        A = gl.A_from_groups(p - 1, groups=groups)
#
#        snr = 100.0
#        eps = 1e-8
#        mus = [5e-2, 5e-4, 5e-6, 5e-8]
#        mu = mus[-1]
#
#        X, y, beta_star = l1_l2_glmu.load(l=l, k=k, g=g, beta=beta, M=M, e=e,
#                                          A=A, mu=mu, snr=snr, intercept=True)
#
#        max_iter = 2000
#        errs = []
#        effs = []
#        v = l
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(LinearRegression(X, y, mean=False))
#                function.add_penalty(gl.GroupLassoOverlap(l=g, A=A, mu=mu,
#                                                          penalty_start=1))
#                function.add_penalty(L2(k, penalty_start=1))
#                function.add_prox(L1(L, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.010326,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 5e-05,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 2500
#        errs = []
#        effs = []
#        v = k
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(LinearRegression(X, y, mean=False))
#                function.add_penalty(gl.GroupLassoOverlap(l=g, A=A, mu=mu,
#                                                          penalty_start=1))
#                function.add_penalty(L2(L, penalty_start=1))
#                function.add_prox(L1(l, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.001130,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 5e-07,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 2500
#        errs = []
#        effs = []
#        v = k
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(RidgeRegression(X, y, L,
#                                                      penalty_start=1))
#                function.add_penalty(gl.GroupLassoOverlap(l=g, A=A, mu=mu,
#                                                          penalty_start=1))
#                function.add_prox(L1(l, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.000982,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 1e-07,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 2000
#        errs = []
#        effs = []
#        v = g
##        print "opt:", v
#        lagranges = np.linspace(v * 0.5, v, 3).tolist()[:-1] \
#                  + np.linspace(v, v * 1.5, 3).tolist()
#        beta_start = start_vector.get_vector((p, 1))
#        beta_nonsmooth_penalty = beta_start
#        for L in lagranges:
#            fista = explicit.FISTA(eps=eps, max_iter=max_iter / len(mus))
#            function = None
#            for mu in mus:
#                function = CombinedFunction()
#                function.add_function(LinearRegression(X, y, mean=False))
#                function.add_penalty(gl.GroupLassoOverlap(l=L, A=A, mu=mu,
#                                                          penalty_start=1))
#                function.add_penalty(L2(k, penalty_start=1))
#                function.add_prox(L1(l, penalty_start=1))
#                beta_nonsmooth_penalty = \
#                        fista.run(function, beta_nonsmooth_penalty)
#
#            mse = np.linalg.norm(beta_nonsmooth_penalty - beta_star) \
#                    / np.linalg.norm(beta_star)
#            errs.append(mse)
#
#            f_nonsmooth_star = function.f(beta_star)
#            f_nonsmooth_penalty = function.f(beta_nonsmooth_penalty)
#            eff = abs(f_nonsmooth_penalty - f_nonsmooth_star) \
#                        / f_nonsmooth_star
#            effs.append(eff)
#
##        print lagranges
##        plot.subplot(2, 1, 1)
##        plot.plot(lagranges, errs)
##        print lagranges[np.argmin(errs)]
#        assert_equal(lagranges[np.argmin(errs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(errs)
#        assert_less(np.min(errs), 0.017904,
#                    msg="Error is too large!")
##        plot.subplot(2, 1, 2)
##        plot.plot(lagranges, effs)
##        print lagranges[np.argmin(effs)]
#        assert_equal(lagranges[np.argmin(effs)], v,
#                               msg="The found minimum is not correct!")
##        print np.min(effs)
#        assert_less(np.min(effs), 5e-05,
#                    msg="Error is too large!")
##        plot.show()
#
#        max_iter = 2500
#        estimator = estimators.RidgeRegression_L1_GL(k, l, g,
#                     A, mu=mu,
#                     output=False,
#                     algorithm=explicit.FISTA(eps=eps, max_iter=max_iter),
#                     penalty_start=1)
#        estimator.fit(X, y)
#        function = RR_L1_GL(X, y, k, l, g, A=A, mu=estimator.mu,
#                            penalty_start=1)
#
#        err = np.linalg.norm(estimator.beta - beta_star) \
#                / np.linalg.norm(beta_star)
##        print err
#        assert_less(err, 0.47, msg="The found minimum is not correct!")
#
#        f_star = function.f(beta_star)
#        f_penalty = function.f(estimator.beta)
#        eff = abs(f_penalty - f_star) / f_star
##        print eff
#        assert_less(eff, 0.17, msg="Error is too large!")

if __name__ == "__main__":
    unittest.main()