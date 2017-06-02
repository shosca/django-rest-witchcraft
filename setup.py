#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import shutil

from setuptools import setup, find_packages
from pipenv.project import Project

here = os.path.abspath(os.path.dirname(__file__))

project = Project()

about = {}
with open(os.path.join(here, "rest_witchcraft", "__version__.py")) as f:
    exec(f.read(), about)


try:
    from pypandoc import convert

    def read_md(f):
        return convert(f, 'rst')
except ImportError:
    print("pypandoc not installed.\nUse `pip install pypandoc`.\nExiting.")
    sys.exit()


if sys.argv[-1] == 'publish':
    twine = shutil.which('twine')
    if twine is None:
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m %s" % (about['__version__'], about['__version__']))
    print("  git push --tags")
    os.system("make clean")
    sys.exit()


setup(
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    install_requires=project.parsed_pipfile['packages'].keys(),
    license='MIT',
    long_description=read_md('README.md'),
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
