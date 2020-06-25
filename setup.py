#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

config = {
    'name': 'babelfont',
    'author': 'Simon Cozens',
    'author_email': 'simon@simon-cozens.org',
    'url': 'https://github.com/simoncozens/babelfont',
    'description': 'Interrogate and manipulate UFO, TTF and OTF fonts with a common interface',
    'long_description': open('README.rst', 'r').read(),
    'license': 'MIT',
    'version': '0.0.1',
    'install_requires': [
        "defcon",
        "fontparts",
        "fonttools"
    ],
    'classifiers': [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta"

    ],
    'package_dir': {'': 'Lib'},
    'packages': find_packages("Lib"),
}

if __name__ == '__main__':
    setup(**config)
