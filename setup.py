#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
import os

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

thelibFolder = os.path.dirname(os.path.realpath(__file__))
requirementPath = thelibFolder + '/requirements.txt'
requirements = []
if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        requirements = f.read().splitlines()

setup_requirements = [ ]

test_requirements = [ "pytest" ]

setup(
    author="Simon Cozens",
    author_email='simon@simon-cozens.org',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Routines for extracting information from fontTools glyphs",
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='babelfont',
    name='babelfont',
    package_dir= {'': 'lib'},
    packages= find_packages("lib"),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/simoncozens/babelfont',
    version='0.4.0',
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "babelfont = babelfont.__main__:main"
        ]
    },
)
