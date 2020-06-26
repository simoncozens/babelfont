#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

thelibFolder = os.path.dirname(os.path.realpath(__file__))
requirementPath = thelibFolder + '/requirements.txt'
install_requires = []
if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        install_requires = f.read().splitlines()

config = {
    'name': 'babelfont',
    'author': 'Simon Cozens',
    'author_email': 'simon@simon-cozens.org',
    'url': 'https://github.com/simoncozens/babelfont',
    'description': 'Interrogate and manipulate UFO, TTF and OTF fonts with a common interface',
    'long_description': open('README.rst', 'r').read(),
    'license': 'MIT',
    'version': '0.0.2',
    'install_requires': install_requires,
    'classifiers': [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta"

    ],
    'package_dir': {'': 'lib'},
    'packages': find_packages("lib"),
}

if __name__ == '__main__':
    setup(**config)
