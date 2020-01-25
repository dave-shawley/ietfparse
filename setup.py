#!/usr/bin/env python
from __future__ import absolute_import

import setuptools

from ietfparse import version


setuptools.setup(
    name='ietfparse',
    version=version,
    author='Dave Shawley',
    author_email='daveshawley@gmail.com',
    url='http://github.com/dave-shawley/ietfparse',
    description='Parse formats defined in IETF RFCs.',
    long_description=open('README.rst').read(),
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    zip_safe=True,
    platforms='any',
    extras={
        'dev': [
            'coverage==5.0.3',
            'flake8==3.7.9',
            'mock>1.0,<2; python_version<"3"',
            'mypy==0.761',
            'sphinx==2.3.1',
            'sphinxcontrib-httpdomain==1.7.0',
            'tox==3.14.2',
            'yapf==0.29.0',
        ],
        'test': [
            'coverage==5.0.3',
            'mock>1.0,<2; python_version<"3"',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing',
    ],
)
