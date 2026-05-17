"""Helpers for parsing HTTP Link headers."""

import typing
from collections import abc

from ietfparse import errors

_OWS = ' \t'
_TOKEN_CHARS = frozenset(
    "!#$%&'*+-.^_`|~"
    '0123456789'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abcdefghijklmnopqrstuvwxyz'
)


LinkTarget: typing.TypeAlias = str
QuotedString: typing.TypeAlias = str
Token: typing.TypeAlias = str
ParamValue: typing.TypeAlias = QuotedString | Token
Parameter: typing.TypeAlias = tuple[Token, ParamValue]
ParseOffset: typing.TypeAlias = int


class ParameterParser:
    """Apply RFC 8288 parameter semantics to a parsed link value.

    :param strict: controls whether parsing follows all
        rules laid out in [RFC-8288-section-3]

    This class processes the parameters for a single [HTTP-Link]
    value after its syntax has already been parsed. It is used from
    within the guts of [ietfparse.headers.parse_link][] and not
    readily suited for other uses.

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
        """Add a new parameter to the parsed value list."""
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
        """The normalized parameter mapping that was parsed."""
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


def parse_values(
    value: str,
) -> abc.Iterable[tuple[LinkTarget, list[Parameter]]]:
    """Parse an HTTP Link header.

    Parses the [HTTP-Link] header into a sequence of
    (target, parameters) tuples.
    """
    index = _skip_ows(value, ParseOffset(0))
    while index < len(value):
        target, index = _parse_link_target(value, index)
        parameters, index = _parse_link_parameters(value, index)
        yield target, parameters


def _parse_link_target(
    value: str, index: ParseOffset
) -> tuple[LinkTarget, ParseOffset]:
    if value[index] != '<':
        raise errors.MalformedLinkValue('Malformed link header', value[index:])

    index = index + 1
    target_start = index
    while index < len(value) and value[index] != '>':
        index = index + 1
    if index >= len(value):
        raise errors.MalformedLinkValue('Malformed link header', value)

    return value[target_start:index].strip(), index + 1


def _parse_link_parameters(
    value: str, index: ParseOffset
) -> tuple[list[Parameter], ParseOffset]:
    parameters = []

    while True:
        index = _skip_ows(value, index)
        if index >= len(value):
            return parameters, index
        if value[index] == ',':
            return parameters, _skip_ows(value, index + 1)

        parameter, index = _parse_link_parameter(value, index)
        if parameter is not None:
            parameters.append(parameter)


def _parse_link_parameter(
    value: str, index: ParseOffset
) -> tuple[Parameter | None, ParseOffset]:
    if value[index] != ';':
        raise errors.MalformedLinkValue('Param list missing opening semicolon')

    index = index + 1
    index = _skip_ows(value, index)
    if index >= len(value) or value[index] in ',;':
        return None, index

    param_name, index = _parse_link_token(value, index)
    index = _skip_ows(value, index)

    if index >= len(value) or value[index] != '=':
        return (param_name.lower(), ''), index

    index = index + 1
    param_value, index = _parse_link_parameter_value(value, index)
    return (param_name.lower(), param_value), index


def _parse_link_parameter_value(
    value: str, index: ParseOffset
) -> tuple[ParamValue, ParseOffset]:
    index = _skip_ows(value, index)
    if index >= len(value):
        raise errors.MalformedLinkValue('Malformed link header', value)
    if value[index] == '"':
        return _parse_link_quoted_string(value, index)
    return _parse_link_token(value, index)


def _skip_ows(value: str, index: ParseOffset) -> ParseOffset:
    while index < len(value) and value[index] in _OWS:
        index = index + 1
    return index


def _parse_link_token(
    value: str, index: ParseOffset
) -> tuple[Token, ParseOffset]:
    """Consume characters from the `token' production starting at index."""
    start = index
    while index < len(value) and value[index] in _TOKEN_CHARS:
        index = index + 1
    if start == index:
        raise errors.MalformedLinkValue('Malformed link header', value[index:])
    return value[start:index], index


def _parse_link_quoted_string(
    value: str, index: ParseOffset
) -> tuple[QuotedString, ParseOffset]:
    """Parse the remainder of a quoted string from value.

    Assumes that the first quote character has already been consumed.
    """
    parsed = []
    index = index + 1
    while index < len(value):
        if value[index] == '\\':
            index = index + 1
            if index >= len(value):
                raise errors.MalformedLinkValue('Malformed link header', value)
            parsed.append(value[index])
        elif value[index] == '"':
            return ''.join(parsed), index + 1
        else:
            parsed.append(value[index])
        index = index + 1

    raise errors.MalformedLinkValue('Malformed link header', value)
