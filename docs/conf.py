#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ietfparse


project = 'ietfparse'
copyright = '2014-2020, Dave Shawley'
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
html_static_path = ['.']
exclude_patterns = []
html_sidebars = {
    '**': ['about.html', 'navigation.html', 'searchbox.html'],
}
html_theme_options = {
    'github_user': 'dave-shawley',
    'github_repo': 'ietfparse',
    'github_banner': True,
}

intersphinx_mapping = {
    'python': ('http://docs.python.org/3/', None),
}
