#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ietfparse

project = 'ietfparse'
copyright = '2014-2022, Dave Shawley'
version = ietfparse.version
release = '.'.join(str(x) for x in ietfparse.version_info[:2])

needs_sphinx = '1.0'
extensions = []
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

# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
extensions.append('sphinx.ext.autodoc')

# https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
extensions.append('sphinx.ext.viewcode')

# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
extensions.append('sphinx.ext.intersphinx')
intersphinx_mapping = {
    'python': ('http://docs.python.org/3/', None),
}

# https://sphinxcontrib-httpdomain.readthedocs.io/
extensions.append('sphinxcontrib.httpdomain')
