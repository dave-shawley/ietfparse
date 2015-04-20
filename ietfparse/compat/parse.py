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
        quote,
        splitnport,
        splitpasswd,
        splituser,
        unquote,
        unquote_to_bytes,
        urlencode,
        urlsplit,
        urlunsplit,
    )
except ImportError:  # pragma: no cover, coverage with tox
    from urllib import (
        quote,
        splitnport,
        splitpasswd,
        splituser,
        unquote,
        urlencode as _urlencode,
    )
    from urlparse import urlsplit, urlunsplit

    # unquote_to_bytes is extremely useful when you need to cleanly
    # unquote a percent-encoded UTF-8 sequence into a unicode string
    # in either Python 2.x or 3.x with unicode_literals enabled.
    # The only good way that I could find to do this in Python 2.x
    # is to take advantage of the "raw_unicode_escape" codec.
    #
    # The return value of this function is the percent decoded raw
    # byte string - NOT A UNICODE STRING
    def unquote_to_bytes(s):
        return unquote(s).encode('raw_unicode_escape')

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
        except (TypeError, ValueError):  # pragma no cover
            # doesn't look like a sequence of tuples, maybe a dict?
            try:
                quoted = {}
                for name, value in query.items():
                    quoted[encode_value(name)] = encode_value(value)
                query = quoted
            except AttributeError:  # not a dictionary either
                pass

        return _urlencode(query, doseq=doseq)
