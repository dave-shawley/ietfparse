"""
Important data structures.

- :class:`.ContentType`: MIME ``Content-Type`` header.

This module contains data structures that were useful in
implementing this library.  If a data structure might be
useful outside of a particular piece of functionality, it
is fully fleshed out and ends up here.

"""
import functools


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


class LinkHeader(object):

    """
    Represents a single link within a ``Link`` header.

    .. attribute:: target

       The target URL of the link.  This may be a relative URL so
       the caller may have to make the link absolute by resolving
       it against a base URL as described in :rfc:`3986#section-5`.

    .. attribute:: parameters

       Possibly empty sequence of name and value pairs.  Parameters
       are represented as a sequence since a single parameter may
       occur more than once.

    The :mailheader:`Link` header is specified by :rfc:`5988`.  It
    is one of the methods used to represent HyperMedia links between
    HTTP resources.

    """

    def __init__(self, target, parameters=None):
        self.target = target
        self.parameters = parameters or []
