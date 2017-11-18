#!/usr/bin/env python
from __future__ import absolute_import

import codecs
import sys

import setuptools

from ietfparse import version


def read_requirements_file(name):
    reqs = []
    try:
        with open(name) as req_file:
            for line in req_file:
                if '#' in line:
                    line = line[0:line.index('#')]
                line = line.strip()
                if line:
                    reqs.append(line)
    except IOError:
        pass
    return reqs


install_requirements = read_requirements_file('requirements.txt')
test_requirements = read_requirements_file('test-requirements.txt')
if sys.version_info < (2, 7):
    test_requirements.append('unittest2')
if sys.version_info < (3, ):
    test_requirements.append('mock>1.0,<2')


with codecs.open('README.rst', 'rb', encoding='utf-8') as file_obj:
    long_description = '\n' + file_obj.read()

setuptools.setup(
    name='ietfparse',
    version=version,
    author='Dave Shawley',
    author_email='daveshawley@gmail.com',
    url='http://github.com/dave-shawley/ietfparse',
    description='Parse formats defined in IETF RFCs.',
    long_description=long_description,
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    zip_safe=True,
    platforms='any',
    install_requires=install_requirements,
    test_suite='nose.collector',
    tests_require=test_requirements,
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
