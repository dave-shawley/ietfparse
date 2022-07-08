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
exclude_patterns = []
html_theme_options = {}

# https://github.com/bashtage/sphinx-material
html_theme = 'sphinx_material'
html_css_files = ['custom.css']
html_theme_options.update({
    'globaltoc_depth': 2,
    'repo_type': 'github',
    'repo_url': 'https://github.com/dave-shawley/ietfparse',
})
html_sidebars = {'**': ['globaltoc.html', 'localtoc.html', 'searchbox.html']}

# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
extensions.append('sphinx.ext.autodoc')

# https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
extensions.append('sphinx.ext.viewcode')

# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
extensions.append('sphinx.ext.extlinks')
extlinks = {
    'issue': ('https://github.com/dave-shawley/ietfparse/issues/%s', '#%s'),
    'compare': ('https://github.com/dave-shawley/ietfparse/compare/%s', '%s'),
}

# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
extensions.append('sphinx.ext.intersphinx')
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

# https://sphinxcontrib-httpdomain.readthedocs.io/
extensions.append('sphinxcontrib.httpdomain')

# https://github.com/tox-dev/sphinx-autodoc-typehints
extensions.append('sphinx_autodoc_typehints')
