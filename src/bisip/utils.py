#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: cberube
# @Date:   05-03-2020
# @Email:  charles@goldspot.ca
# @Last modified by:   charles
# @Last modified time: 2020-03-09T18:29:06-04:00


import warnings

import numpy as np


class utils:

    def get_model_percentile(self, p, chain=None, **kwargs):
        """Gets percentiles of the model values for a MCMC chain.

        Args:
            p (:obj:`float` or :obj:`list` of :obj:`float`): percentiles values
                to compute.
            chain (:obj:`ndarray`): A numpy array containing the MCMC chain to
                plot. Should have a shape (nwalkers, nsteps, ndim) or
                (nsteps, ndim). If None, the full, unflattened chain will be
                used and all walkers will be plotted. Defaults to None.

        Keyword Args:
            **kwargs: See kwargs of the get_chain method.
        """
        chain = self.parse_chain(chain, **kwargs)
        results = np.empty((chain.shape[0], 2, self.data['N']))
        for i in range(chain.shape[0]):
            results[i] = self.forward(chain[i], self.data['w'])
        return np.percentile(results, p, axis=0)

    def get_param_percentile(self, p, chain=None, **kwargs):
        """Gets percentiles of the parameter values for a MCMC chain.

        Args:
            p (:obj:`float` or :obj:`list` of :obj:`float`): percentiles values
                to compute.
            chain (:obj:`ndarray`): A numpy array containing the MCMC chain to
                plot. Should have a shape (nwalkers, nsteps, ndim) or
                (nsteps, ndim). If None, the full, unflattened chain will be
                used and all walkers will be plotted. Defaults to None.

        Keyword Args:
            **kwargs: See kwargs of the get_chain method.

        """
        chain = self.parse_chain(chain, **kwargs)
        return np.percentile(chain, p, axis=0)

    def get_param_mean(self, chain=None, **kwargs):
        """Gets the mean of the model parameters for a MCMC chain.

        Args:
            chain (:obj:`ndarray`): A numpy array containing the MCMC chain to
                plot. Should have a shape (nwalkers, nsteps, ndim) or
                (nsteps, ndim). If None, the full, unflattened chain will be
                used and all walkers will be plotted. Defaults to None.

        Keyword Args:
            **kwargs: See kwargs of the get_chain method.

        """
        chain = self.parse_chain(chain, **kwargs)
        return np.mean(chain, axis=0)

    def get_param_std(self, chain=None, **kwargs):
        """Gets the standard deviation of the model parameters.

        Args:
            chain (:obj:`ndarray`): A numpy array containing the MCMC chain to
                plot. Should have a shape (nwalkers, nsteps, ndim) or
                (nsteps, ndim). If None, the full, unflattened chain will be
                used and all walkers will be plotted. Defaults to None.

        Keyword Args:
            **kwargs: See kwargs of the get_chain method.

        """
        chain = self.parse_chain(chain, **kwargs)
        return np.std(chain, axis=0)

    def parse_chain(self, chain, **kwargs):
        if chain is None:
            # if discard is not None and thin is not None:
            kwargs['flat'] = True
            chain = self.get_chain(**kwargs)
            if 'discard' not in kwargs and 'thin' not in kwargs:
                warnings.warn(('No samples were discarded from the chain.\n'
                               'Pass discard and thin keywords to remove '
                               'burn-in samples and reduce autocorrelation.'),
                              UserWarning)

        else:
            if chain.ndim > 2:
                raise ValueError('Flatten chain by passing flat=True.')

            if 'discard' in kwargs or 'thin' in kwargs:
                raise ValueError('Please pass either a chain obtained with '
                                 'the get_chain() method or pass '
                                 'discard and thin keywords to parse '
                                 'the full chain. Do not pass both.')
        return chain

    def load_data(self, filename, headers=1, ph_units='mrad'):
        """Imports a data file and prepares it for inversion.

        Args:
            filepath (:obj:`str`): The path to the data file.
            headers (:obj:`int`): The number of header lines in the file.
                Defaults to 1.
            ph_units (:obj:`str`): The units of the phase shift measurements.
                Choices: 'mrad', 'rad', 'deg'. Defaults to 'mrad'.

        """
        # Importation des données .DAT
        dat_file = np.loadtxt(f"{filename}", skiprows=headers, delimiter=',')
        labels = ["freq", "amp", "pha", "amp_err", "pha_err"]
        data = {l: dat_file[:, i] for (i, l) in enumerate(labels)}
        if ph_units == "mrad":
            data["pha"] = data["pha"]/1000  # mrad to rad
            data["pha_err"] = data["pha_err"]/1000  # mrad to rad
        if ph_units == "deg":
            data["pha"] = np.radians(data["pha"])  # deg to rad
            data["pha_err"] = np.radians(data["pha_err"])  # deg to rad
        data["phase_range"] = abs(max(data["pha"])-min(data["pha"]))  # Range of phase measurements (used in NRMS error calculation)
        data["Z"] = data["amp"]*(np.cos(data["pha"]) + 1j*np.sin(data["pha"]))
        EI = np.sqrt(((data["amp"]*np.cos(data["pha"])*data["pha_err"])**2)+(np.sin(data["pha"])*data["amp_err"])**2)
        ER = np.sqrt(((data["amp"]*np.sin(data["pha"])*data["pha_err"])**2)+(np.cos(data["pha"])*data["amp_err"])**2)
        data["Z_err"] = ER + 1j*EI
        # Normalization of amplitude
        data["Z_max"] = max(abs(data["Z"]))  # Maximum amplitude
        zn, zn_e = data["Z"]/data["Z_max"], data["Z_err"]/data["Z_max"]  # Normalization of impedance by max amplitude
        data["zn"] = np.array([zn.real, zn.imag])  # 2D array with first column = real values, second column = imag values
        data["zn_err"] = np.array([zn_e.real, zn_e.imag])  # 2D array with first column = real values, second column = imag values
        data['N'] = len(data['freq'])
        data['w'] = 2*np.pi*data['freq']

        return data
