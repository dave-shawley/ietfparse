"""
Functions for parsing headers.

- :func:`.parse_content_type`: parse a ``Content-Type`` value

This module also defines classes that might be of some use outside
of the module.  They are not designed for direct usage unless otherwise
mentioned.

"""

import re


_COMMENT_RE = re.compile(r'\(.*\)')


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
        self.content_type = content_type.lower()
        self.content_subtype = content_subtype.lower()
        self.parameters = {}
        if parameters is not None:
            for name in parameters:
                self.parameters[name.lower()] = parameters[name]


def _remove_comments(value):
    return _COMMENT_RE.sub('', value)


def parse_content_type(content_type):
    """Parse a content type like header.

    :param str content_type: the string to parse as a content type
    :return: a :class:`.ContentType` instance

    """
    parts = _remove_comments(content_type).split(';')
    content_type, content_subtype = parts.pop(0).split('/')
    parameters = {}
    for type_parameter in parts:
        name, value = type_parameter.split('=')
        parameters[name.strip()] = value.strip('"').strip()

    return ContentType(content_type, content_subtype, parameters)
