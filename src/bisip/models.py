#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: cberube
# @Date:   05-03-2020
# @Email:  charles@goldspot.ca
# @Last modified by:   charles
# @Last modified time: 2020-03-06T12:31:21-05:00


import emcee
import numpy as np

from .cython_funcs import Decomp_cyth
from . import utils
from . import plotlib


def log_likelihood(theta, model, x, y, yerr):
    sigma2 = yerr**2
    return -0.5 * np.sum((y - model(theta, x))**2 / sigma2 + 2*np.log(sigma2))


def log_prior(theta, bounds):
    if not ((bounds[0] < theta).all() and (theta < bounds[1]).all()):
        return -np.inf
    else:
        return 0.0


def log_probability(theta, model, bounds, x, y, yerr):
    lp = log_prior(theta, bounds)
    if not np.isfinite(lp):
        return -np.inf
    return lp + log_likelihood(theta, model, x, y, yerr)


class Inversion(object):

    # Public plotting methods
    plot_traces = plotlib.plot_traces
    plot_histograms = plotlib.plot_histograms
    plot_fit = plotlib.plot_fit

    # Private utility methods
    _parse_chain = utils.parse_chain

    def __init__(self, nwalkers=32, nsteps=5000, pool=None, moves=None):
        self.nsteps = nsteps
        self.nwalkers = nwalkers
        self.pool = pool
        self.moves = moves
        # self.infer_obs_noise = infer_obs_noise

        self.params = {}
        # if infer_obs_noise:
        #     self.params.update({'log_noise': [0.0, 1.0]})

    def _start_sampling(self, **kwargs):
        self.ndim = self.bounds.shape[1]
        self.p0 = np.random.uniform(*self.bounds, (self.nwalkers, self.ndim))

        model_args = (self.forward, self.bounds, self.data['w'],
                      self.data['zn'], self.data['zn_err'])

        self.sampler = emcee.EnsembleSampler(self.nwalkers,
                                             self.ndim,
                                             log_probability,
                                             args=model_args,
                                             **kwargs,
                                             )
        self.sampler.run_mcmc(self.p0, self.nsteps, progress=True)

    def get_chain(self, **kwargs):
        return self.sampler.get_chain(**kwargs)

    def get_model_percentile(self, p, chain=None, **kwargs):
        chain = self._parse_chain(chain, **kwargs)
        results = np.empty((chain.shape[0], 2, self.data['N']))
        for i in range(chain.shape[0]):
            results[i] = self.forward(chain[i], self.data['w'])
        return np.percentile(results, p, axis=0)

    def get_param_percentile(self, p, chain=None, **kwargs):
        chain = self._parse_chain(chain, **kwargs)
        return np.percentile(chain, p, axis=0)

    def get_param_mean(self, chain=None, **kwargs):
        chain = self._parse_chain(chain, **kwargs)
        return np.mean(chain, axis=0)

    def get_param_std(self, chain=None, **kwargs):
        chain = self._parse_chain(chain, **kwargs)
        return np.std(chain, axis=0)

    @property
    def param_names(self):
        return list(self.params.keys())


class PolynomialDecomposition(Inversion):

    def __init__(self, poly_deg=5, c_exp=1.0, **kwargs):
        super().__init__(**kwargs)
        self.c_exp = c_exp
        self.poly_deg = poly_deg

    def forward(self, theta, w):
        # rho, *a = theta
        # a = np.array(a)
        return Decomp_cyth(w, self.taus, self.log_taus, self.c_exp,
                           R0=theta[0], a=theta[1:])

    def fit(self, filepath, **data_kwargs):
        self.data = utils.load_data(filepath, **data_kwargs)

        min_tau = np.floor(min(np.log10(1./self.data['w'])) - 1)
        max_tau = np.floor(max(np.log10(1./self.data['w'])) + 1)
        n_tau = 2*self.data['N']
        self.log_tau = np.linspace(min_tau, max_tau, n_tau)

        deg_range = list(range(self.poly_deg+1))
        rev_deg_range = list(reversed(deg_range))
        self.log_taus = np.array([self.log_tau**i for i in rev_deg_range])
        self.taus = 10**self.log_tau  # Accelerates sampling

        # Add polynomial decomposition parameters to dict
        self.params.update({'r0': [0.9, 1.1]})
        self.params.update({f'a{x}': [-1, 1] for x in rev_deg_range})

        self.bounds = np.array([self.params[x] for x in self.params.keys()]).T

        self._start_sampling(pool=self.pool, moves=self.moves)
