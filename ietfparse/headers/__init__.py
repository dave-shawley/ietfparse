"""
Functions for parsing headers.

- :func:`.parse_content_type`: parse a ``Content-Type`` value
- :func:`.parse_http_accept_header`: parse an ``Accept`` style header

This module also defines classes that might be of some use outside
of the module.  They are not designed for direct usage unless otherwise
mentioned.

"""

import functools
import re


_COMMENT_RE = re.compile(r'\(.*\)')


@functools.total_ordering
class ContentType(object):

    """A MIME ``Content-Type`` header.

    :param str content_type: the primary content type
    :param str content_subtype: the content sub-type
    :param dict parameters: optional dictionary of content type
        parameters

    Internet content types are described by the :mailheader:`Content-Type`
    header from :rfc:`2045`.  It was reused across many other protocol
    specifications, most notably HTTP (:rfc:`7231`).  This header's
    syntax is described in :rfc:`2045#section-5.1`.  In its most basic
    form, a content type header looks like ``text/html``.  The primary
    content type is ``text`` with a *subtype* of ``html``.  Content type
    headers can include *parameters* as ``name=value`` pairs separated
    by colons.

    """

    def __init__(self, content_type, content_subtype, parameters=None):
        self.content_type = content_type.strip().lower()
        self.content_subtype = content_subtype.strip().lower()
        self.parameters = {}
        if parameters is not None:
            for name in parameters:
                self.parameters[name.lower()] = parameters[name]

    def __str__(self):
        if self.parameters:
            return '{0}/{1}; {2}'.format(
                self.content_type, self.content_subtype,
                '; '.join('{0}={1}'.format(name, self.parameters[name])
                          for name in sorted(self.parameters))
            )
        else:
            return '{0}/{1}'.format(self.content_type, self.content_subtype)

    def __repr__(self):  # pragma: no cover
        return '<{0}.{1} {2}/{3}, {4} parameters>'.format(
            self.__class__.__module__, self.__class__.__name__,
            self.content_type, self.content_subtype,
            len(self.parameters),
        )

    def __eq__(self, other):
        return (self.content_type == other.content_type and
                self.content_subtype == other.content_subtype and
                self.parameters == other.parameters)

    def __lt__(self, other):
        if self.content_type == '*' and other.content_type != '*':
            return True
        if self.content_subtype == '*' and other.content_subtype != '*':
            return True
        if len(self.parameters) < len(other.parameters):
            return True
        if self.content_type == other.content_type:
            return self.content_subtype < other.content_subtype
        return self.content_type < other.content_type


def _remove_comments(value):
    """:rtype: str"""  # makes PyCharm happy
    return _COMMENT_RE.sub('', value)


def parse_content_type(content_type, normalize_parameter_values=True):
    """Parse a content type like header.

    :param str content_type: the string to parse as a content type
    :param bool normalize_parameter_values:
        setting this to ``False`` will enable strict RFC2045 compliance
        in which content parameter values are case preserving.
    :return: a :class:`.ContentType` instance

    """
    parts = _remove_comments(content_type).split(';')
    content_type, content_subtype = parts.pop(0).split('/')
    parameters = {}
    for type_parameter in parts:
        name, value = type_parameter.split('=')
        if normalize_parameter_values:
            value = value.lower()
        parameters[name.strip()] = value.strip('"').strip()

    return ContentType(content_type, content_subtype, parameters)


def parse_http_accept_header(header_value):
    """Parse an HTTP accept-like header.

    :param header_value: the header value to parse
    :return: a ``list`` of :class:`.ContentType` instances in
        decreasing quality order.  Each instance is augmented
        with the associated quality as a ``float`` property
        named ``quality``.

    ``Accept`` is a class of headers that contain a list of values
    and an associated preference value.  The ever present `Accept`_
    header is a perfect example.  It is a list of content types and
    an optional parameter named ``q`` that indicates the relative
    weight of a particular type.  The most basic example is::

        Accept: audio/*;q=0.2, audio/basic

    Which states that I prefer the ``audio/basic`` content type
    but will accept other ``audio`` sub-types with an 80% mark down.

    .. _Accept: http://tools.ietf.org/html/rfc7231#section-5.3.2

    """
    headers = [parse_content_type(header)
               for header in header_value.split(',')]
    for header in headers:
        header.quality = float(header.parameters.pop('q', 1.0))

    def ordering(left, right):
        if left.quality != right.quality:
            return right.quality - left.quality
        if left == right:
            return 0
        if left > right:
            return -1
        return 1

    return sorted(headers, key=functools.cmp_to_key(ordering))
