"""Important data structures.

- :class:`.ContentType`: MIME ``Content-Type`` header.
- :class:`.LinkHeader`: parsed ``Link`` header.

This module contains data structures that were useful in
implementing this library.  If a data structure might be
useful outside a particular piece of functionality, it is
fully fleshed out and ends up here.

"""

from __future__ import annotations

import collections
import functools
import typing
from collections import abc

from ietfparse import _helpers


@functools.total_ordering
class ContentType:
    """A MIME ``Content-Type`` header.

    Internet content types are described by the [HTTP-Content-Type]
    header from [RFC-2045-section-5].  It was reused across many other
    protocol specifications, most notably HTTP ([RFC-9110]). In its most
    basic form, a content type header looks like `text/html`. The primary
    content type is `text` with a *subtype* of `html`.  Content type
    headers may include *parameters* as `name=value` pairs separated
    by colons.

    [RFC-6839] added the ability to use a content type to identify the
    semantic value of a representation with a content type and also identify
    the document format as a content type suffix.  For example,
    ``application/vnd.github.v3+json`` is used to identify documents that
    match version 3 of the GitHub API that are represented as JSON documents.
    The same entity encoded as msgpack would have the content type
    ``application/vnd.github.v3+msgpack``.  In this case, the content type
    identifies the information that is in the document and the suffix is used
    to identify the content format.

    :param content_type: the primary content type
    :param content_subtype: the content subtype
    :param content_suffix: optional content suffix
    :param parameters: optional dictionary of content type
        parameters

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
        # disabled ruff: UP032 since the f-string version is horrid
        return '<{}.{} {}/{}{}, {} parameters>'.format(  # noqa: UP032
            self.__class__.__module__,
            self.__class__.__name__,
            self.content_type,
            self.content_subtype,
            content_suffix,
            len(self.parameters),
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            other = _helpers.parse_header('parse_content_type', other)
        if not isinstance(other, ContentType):
            return NotImplemented
        return (
            self.content_type == other.content_type
            and self.content_subtype == other.content_subtype
            and self.content_suffix == other.content_suffix
            and self.parameters == other.parameters
        )

    def __lt__(self, other: object) -> bool:
        if isinstance(other, str):
            other = _helpers.parse_header('parse_content_type', other)
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


T = typing.TypeVar('T')


class ImmutableSequence(abc.Sequence[T], typing.Generic[T]):
    """Immutable sequence."""

    def __init__(self, seq: abc.Iterable[T]) -> None:
        self.__data = list(seq)

    def __len__(self) -> int:
        return len(self.__data)

    def __repr__(self) -> str:
        return repr(self.__data)

    @typing.overload
    def __getitem__(self, index: int) -> T: ...  # pragma: nocover

    @typing.overload
    def __getitem__(
        self, index: slice
    ) -> abc.Sequence[T]: ...  # pragma: nocover

    def __getitem__(self, index: slice | int) -> abc.Sequence[T] | T:
        return self.__data[index]

    def index(self, value: T, start: int = 0, stop: int | None = None) -> int:
        """Find `value` in the subsequence [`start`,`stop`)."""
        return self.__data.index(
            value, start, len(self.__data) if stop is None else stop
        )

    def count(self, value: T) -> int:
        """Count the number of occurrences of `value`."""
        return self.__data.count(value)

    def __eq__(self, other: object) -> bool:
        try:
            return len(other) == len(self.__data) and all(  # type: ignore[arg-type]
                a == b
                for a, b in zip(self.__data, other)  # type: ignore[call-overload]
            )
        except TypeError:
            return NotImplemented

    def __contains__(self, item: object) -> bool:
        return item in self.__data

    def __iter__(self) -> abc.Iterator[T]:
        return iter(self.__data)

    def __reversed__(self) -> abc.Iterator[T]:
        return reversed(self.__data)

    def __setitem__(self, index: int, value: str) -> None:
        raise TypeError('Cannot modify ImmutableSequence')


class LinkHeader:
    """Represents a single link within a `Link` header.

    The [HTTP-Link] header is specified by [RFC-8288]. It is one
    of the methods used to represent HyperMedia links between
    HTTP resources.
    """

    def __init__(
        self,
        target: str,
        parameters: abc.Sequence[tuple[str, str]] | None = None,
    ) -> None:
        self._target = target
        param_dict = collections.defaultdict(list)
        for name, value in parameters or []:
            param_dict[name].append(value)
        self._params = dict(param_dict.items())

    @property
    def target(self) -> str:
        """The target URL of the link.

        This may be a relative URL so the caller may have to make the
        link absolute by resolving it against a base URL as described
        in [RFC-3986-section-5].
        """
        return self._target

    @functools.cached_property
    def parameters(self) -> abc.Sequence[tuple[str, str]]:
        """Possibly empty sequence of name and value pairs.

        Parameters are represented as a sequence since a single
        parameter may occur more than once.
        """
        return ImmutableSequence[tuple[str, str]](
            (item, value)
            for item, values in self._params.items()
            for value in values
        )

    @functools.cached_property
    def rel(self) -> str:
        """Space-separated relationship parameter.

        This will be the empty string if the `rel` parameter
        was not included.
        """
        return ' '.join(self._params.get('rel', [])).strip()

    def __getitem__(self, param_name: str) -> abc.Sequence[str]:
        """Return the parameter values for `param_name` as a list.

        If `param_name` is not present, then an empty sequence is returned.
        """
        return ImmutableSequence[str](self._params.get(param_name, []))

    def __contains__(self, param_name: object) -> bool:
        return param_name in self._params

    def __str__(self) -> str:
        formatted = [f'<{self.target}>']
        if self.rel:
            formatted.append(f'rel="{self.rel}"')
        formatted.extend(
            sorted(
                f'{name}="{value}"'
                for name in self._params
                for value in self._params[name]
                if name != 'rel'
            )
        )
        return '; '.join(formatted)
