#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: cberube
# @Date:   05-03-2020
# @Email:  charles@goldspot.ca
# @Last modified by:   charles
# @Last modified time: 2020-03-12T19:11:30-04:00
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 16:18:50 2017

@author: Charles
"""

from setuptools import setup, find_packages

from distutils.extension import Extension
import numpy

SRC_DIR = 'src'
PACKAGES = find_packages(where=SRC_DIR)
PREREQ = ['setuptools>=18.0', 'cython', 'numpy']
REQUIRES = ['emcee', 'corner', 'matplotlib', 'tqdm']

cmdclass = {}
EXT_MODULES = [Extension("bisip.cython_funcs",
                         sources=["./src/bisip/cython_funcs.pyx"])]

setup(
    name='bisip',
    setup_requires=PREREQ,
    packages=PACKAGES,
    package_dir={"": SRC_DIR},
    version='0.0.1',
    license='MIT',
    install_requires=REQUIRES,
    description='Bayesian inversion of SIP data',
    long_description='README.md',
    author='Charles L. Berube',
    author_email='charleslberube@gmail.com',
    url='https://github.com/clberube/bisip2',
    keywords=['stochastic inversion', 'spectral induced polarization', 'mcmc'],
    classifiers=[],
    cmdclass=cmdclass,
    ext_modules=EXT_MODULES,
    include_dirs=[numpy.get_include()],
    include_package_data=True,
    package_data={'': ['data/*.dat']},
)
