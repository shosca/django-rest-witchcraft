#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages
from pipenv.project import Project

here = os.path.abspath(os.path.dirname(__file__))

project = Project()

about = {}
with open(os.path.join(here, "rest_witchcraft", "__version__.py")) as f:
    exec(f.read(), about)

setup(
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    install_requires=project.parsed_pipfile['packages'].keys(),
    license='MIT',
    name=project.name,
    packages=find_packages(exclude=['tests']),
    url='https://github.com/shosca/django-rest-witchcraft',
    version=about['__version__'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 2 - Pre-Alpha',
    ])
