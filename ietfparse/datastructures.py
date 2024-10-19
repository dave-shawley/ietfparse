"""Important data structures.

- :class:`.ContentType`: MIME ``Content-Type`` header.
- :class:`.LinkHeader`: parsed ``Link`` header.

This module contains data structures that were useful in
implementing this library.  If a data structure might be
useful outside a particular piece of functionality, it is
fully fleshed out and ends up here.

"""

from __future__ import annotations

import functools
import typing

if typing.TYPE_CHECKING:
    from collections import abc


@functools.total_ordering
class ContentType(object):
    """A MIME ``Content-Type`` header.

    :param content_type: the primary content type
    :param content_subtype: the content sub-type
    :param content_suffix: optional content suffix
    :param parameters: optional dictionary of content type
        parameters

    Internet content types are described by the :mailheader:`Content-Type`
    header from :rfc:`2045`.  It was reused across many other protocol
    specifications, most notably HTTP (:rfc:`7231`).  This header's
    syntax is described in :rfc:`2045#section-5.1`.  In its most basic
    form, a content type header looks like ``text/html``.  The primary
    content type is ``text`` with a *subtype* of ``html``.  Content type
    headers can include *parameters* as ``name=value`` pairs separated
    by colons.

    :rfc:`6839` added the ability to use a content type to identify the
    semantic value of a representation with a content type and also identify
    the document format as a content type suffix.  For example,
    ``application/vnd.github.v3+json`` is used to identify documents that
    match version 3 of the GitHub API that are represented as JSON documents.
    The same entity encoded as msgpack would have the content type
    ``application/vnd.github.v3+msgpack``.  In this case, the content type
    identifies the information that is in the document and the suffix is used
    to identify the content format.

    """

    content_type: str
    content_subtype: str
    parameters: abc.MutableMapping[str, str]
    content_suffix: str | None
    quality: float | None

    def __init__(
        self,
        content_type: str,
        content_subtype: str,
        parameters: abc.Mapping[str, str | int] | None = None,
        content_suffix: str | None = None,
    ) -> None:
        self.content_type = content_type.strip().lower()
        self.content_subtype = content_subtype.strip().lower()
        self.quality = None
        if content_suffix is not None:
            self.content_suffix = content_suffix.strip().lower()
        else:
            self.content_suffix = None
        self.parameters = {}
        if parameters is not None:
            for name in parameters:
                self.parameters[name.lower()] = str(parameters[name])

    def __str__(self) -> str:
        suffix, params = '', ''
        if self.content_suffix:
            suffix = f'+{self.content_suffix}'
        if self.parameters:
            params = '; '.join(
                f'{name}={self.parameters[name]}'
                for name in sorted(self.parameters)
            )
            params = f'; {params}'
        return f'{self.content_type}/{self.content_subtype}{suffix}{params}'

    def __repr__(self) -> str:  # pragma: no cover
        if self.content_suffix:
            content_suffix = f'+{self.content_suffix}'
        else:
            content_suffix = ''
        return '<{0}.{1} {2}/{3}{4}, {5} parameters>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.content_type,
            self.content_subtype,
            content_suffix,
            len(self.parameters),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ContentType):
            return NotImplemented
        return (
            self.content_type == other.content_type
            and self.content_subtype == other.content_subtype
            and self.content_suffix == other.content_suffix
            and self.parameters == other.parameters
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ContentType):
            return NotImplemented
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
    """Represents a single link within a ``Link`` header.

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

    target: str
    parameters: abc.Sequence[tuple[str, str]]

    def __init__(
        self,
        target: str,
        parameters: abc.Sequence[tuple[str, str]] | None = None,
    ) -> None:
        self.target = target
        self.parameters = [] if parameters is None else parameters

    def __str__(self) -> str:
        formatted = '<{0}>'.format(self.target)
        if self.parameters:
            params = '; '.join(
                sorted(
                    [
                        '{0}="{1}"'.format(*pair)
                        for pair in self.parameters
                        if pair[0] != 'rel'
                    ]
                )
            )
            rel = [
                '{0}="{1}"'.format(*pair)
                for pair in self.parameters
                if pair[0] == 'rel'
            ]
            if rel:
                formatted += '; ' + rel[0]
            if params:
                formatted += '; ' + params

        return formatted
