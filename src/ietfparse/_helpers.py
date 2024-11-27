from __future__ import annotations

import typing

from ietfparse import headers

if typing.TYPE_CHECKING:
    from collections import abc

    from ietfparse import datastructures


class ParameterParser:
    """Utility class to parse Link headers.

    :param strict: controls whether parsing follows all
        rules laid out in [RFC-8288-section-3]

    This class parses the parameters for a single [HTTP-Link]
    value.  It is used from within the guts of
    [ietfparse.headers.parse_link_header][] and not readily
    suited for other uses.

    If *strict mode* is enabled, then the first value for the
    `rel`, `media`, `type`, `title`, and `title*` parameters
    is retained and additional values are ignored as described
    in [RFC-8288-section-3].

    """

    def __init__(self, *, strict: bool = True) -> None:
        self.strict = strict
        self._values: list[tuple[str, str]] = []
        self._rfc_values: dict[str, str | None] = {
            'rel': None,
            'media': None,
            'type': None,
            'title': None,
            'title*': None,
        }

    def add_value(self, name: str, value: str) -> None:
        """Add a new value to the list.

        :param str name: name of the value that is being parsed
        :param str value: value that is being parsed
        :raises ietfparse.errors.MalformedLinkValue:
            if *strict mode* is enabled and a validation error
            is detected

        This method implements most of the validation mentioned in
        sections 5.3 and 5.4 of :rfc:`5988`.  The ``_rfc_values``
        dictionary contains the appropriate values for the attributes
        that get special handling.  If *strict mode* is enabled, then
        only values that are acceptable will be added to ``_values``.

        """
        try:
            if self._rfc_values[name] is None:
                self._rfc_values[name] = value
            elif self.strict:
                return
        except KeyError:
            pass

        if self.strict and name in ('title', 'title*'):
            return

        self._values.append((name, value))

    @property
    def values(self) -> list[tuple[str, str]]:
        """The name/value mapping that was parsed."""
        values = self._values[:]
        if self.strict:
            preferred_title = self._rfc_values['title*']
            fallback_title = self._rfc_values['title']
            if preferred_title is not None:
                values.append(('title*', preferred_title))
                if fallback_title is not None:
                    values.append(('title', preferred_title))
            elif fallback_title is not None:
                values.append(('title', fallback_title))
        return values


@typing.overload
def parse_header(
    parser_name: typing.Literal['parse_accept'], value: str
) -> abc.Sequence[datastructures.ContentType]: ...


@typing.overload
def parse_header(
    parser_name: typing.Literal['parse_content_type'], value: str
) -> datastructures.ContentType: ...


@typing.overload
def parse_header(
    parser_name: typing.Literal['parse_link'], value: str
) -> abc.Sequence[datastructures.LinkHeader]: ...


def parse_header(parser_name: str, value: str) -> object:
    try:
        return getattr(headers, parser_name)(value)
    except AttributeError:
        raise NotImplementedError(f'unknown parser {parser_name}') from None
    except ValueError:
        return value
