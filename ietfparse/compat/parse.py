"""
Exports related to URL parsing.

This module exports standard library functionality so that it
matches :mod:`urllib.parse` from the Python 3 standard library.

"""
__all__ = (
    'quote',
    'splitnport',
    'urlsplit',
    'urlunsplit',
)

try:
    from urllib.parse import quote, splitnport, urlsplit, urlunsplit
except ImportError:
    from urllib import splitnport, quote
    from urlparse import urlsplit, urlunsplit
