"""
Exports related to URL parsing.

This module exports standard library functionality so that it
matches :mod:`urllib.parse` from the Python 3 standard library.

"""
import codecs

__all__ = (
    'quote',
    'splitnport',
    'splitpasswd',
    'splituser',
    'unquote',
    'unquote_to_bytes',
    'urlencode',
    'urlsplit',
    'urlunsplit',
)

try:
    from urllib.parse import (
        quote, splitnport, urlencode, urlsplit, urlunsplit)
    from urllib.parse import (
        splitpasswd,
        splituser,
        unquote,
        unquote_to_bytes,
    )
except ImportError:
    from urllib import quote, splitnport, urlencode as _urlencode
    from urllib import (
        splitpasswd,
        splituser,
        quote,
        unquote,
    )
    from urlparse import urlsplit, urlunsplit
    unquote_to_bytes = unquote

    # urlencode did not encode its parameters in Python 2.x so we
    # need to implement that ourselves for compatibility.
    def urlencode(query, doseq=0, safe='', encoding=None, errors=None):

        if encoding is None:
            encoding = 'utf-8'
        if errors is None:
            errors = 'strict'

        def encode_value(v):
            try:
                return codecs.encode(v, encoding, errors)
            except UnicodeError:
                raise
            except (AttributeError, TypeError):
                return str(v)

        try:
            quoted = []
            for name, value in query:
                quoted.append((encode_value(name), encode_value(value)))
            query = quoted
        except UnicodeError:
            raise
        except (TypeError, ValueError) as exc:  # pragma no cover
            # doesn't look like a sequence of tuples, maybe a dict?
            try:
                quoted = {}
                for name, value in query.items():
                    quoted[encode_value(name)] = encode_value(value)
                query = quoted
            except AttributeError:  # not a dictionary either
                pass

        return _urlencode(query, doseq=doseq)
