#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sphinx_rtd_theme

import ietfparse


project = 'ietfparse'
copyright = '2014-2017, Dave Shawley'
version = ietfparse.version
release = '.'.join(str(x) for x in ietfparse.version_info[:2])

needs_sphinx = '1.0'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinxcontrib.httpdomain',
]
templates_path = []
source_suffix = '.rst'
source_encoding = 'utf-8-sig'
master_doc = 'index'
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = []
exclude_patterns = []

intersphinx_mapping = {
    'python': ('http://docs.python.org/3/', None),
}
