"""Helpers for parsing and serializing W3C Baggage headers.

The grammar is defined by <https://www.w3.org/TR/baggage/>:

    baggage-string  =  list-member *( OWS "," OWS list-member )
    list-member     =  key OWS "=" OWS value *( OWS ";" OWS property )
    property        =  key OWS "=" OWS value
    property        =/ key OWS
    key             =  token          ; RFC 7230
    value           =  *baggage-octet
    baggage-octet   =  %x21 / %x23-2B / %x2D-3A / %x3C-5B / %x5D-7E
    OWS             =  *( SP / HTAB )

Because every octet outside of the ``baggage-octet`` range (notably ``,``,
``;``, and whitespace) must be percent-encoded, splitting on those delimiters
is unambiguous and there are no quoted strings to contend with.

"""

from __future__ import annotations

import typing as t
import urllib.parse

from ietfparse import _parser

# Property values may be present but empty (``k=``), absent entirely (``k``),
# or a real string.  ``None`` distinguishes a valueless property from one whose
# value happens to be the empty string.
PropertyValue: t.TypeAlias = 'str | None'
Property: t.TypeAlias = 'tuple[str, PropertyValue]'
Member: t.TypeAlias = 'tuple[str, str, list[Property]]'

# baggage-octet minus the percent sign -- the spec requires ``%`` itself to be
# percent-encoded even though it falls inside the octet range.
_SAFE_VALUE_CHARS = "!#$&'()*+-./:<=>?@[]^_`{|}~"

# Matches the wire form of a ``value`` (percent-encoded ``baggage-octet``s).
_VALUE_OCTETS = frozenset(
    chr(code)
    for code in (
        0x21,
        *range(0x23, 0x2C),
        *range(0x2D, 0x3B),
        *range(0x3C, 0x5C),
        *range(0x5D, 0x7F),
    )
)
_PERCENT_ESCAPE_LENGTH = 2


def is_token(value: str) -> bool:
    """Return :data:`True` if `value` is a non-empty RFC 7230 token."""
    return _parser.is_token(value)


def encode_value(value: str) -> str:
    """Percent-encode `value` for inclusion in a baggage header."""
    return urllib.parse.quote(value, safe=_SAFE_VALUE_CHARS)


def decode_value(value: str) -> str:
    """Percent-decode a baggage `value`."""
    return urllib.parse.unquote(value)


def _valid_octets(value: str) -> bool:
    position = 0
    while position < len(value):
        char = value[position]
        if char == '%':
            escape = value[position + 1 : position + 3]
            if len(escape) != _PERCENT_ESCAPE_LENGTH or not all(
                char in '0123456789abcdefABCDEF' for char in escape
            ):
                return False
            position += 3
            continue
        if char not in _VALUE_OCTETS:
            return False
        position += 1
    return True


def parse_baggage_string(value: str, *, strict: bool) -> list[Member]:
    """Split a baggage header into decoded members.

    :param value: the header value to parse
    :param strict: when *truthy* a malformed list-member raises a
        :class:`_parser.ParseError`; otherwise it is skipped
    :return: a list of ``(key, value, properties)`` tuples where the key and
        (decoded) values are :class:`str` and ``properties`` is a list of
        ``(name, value)`` pairs

    """
    members: list[Member] = []
    for raw_member in value.split(','):
        segment = raw_member.strip(' \t')
        if not segment:
            if strict:
                raise _parser.ParseError(f'empty baggage member: {value!r}')
            continue
        try:
            members.append(_parse_member(segment))
        except _parser.ParseError:
            if strict:
                raise
    return members


def _parse_member(segment: str) -> Member:
    key_value, property_sep, property_str = segment.partition(';')
    key, sep, raw_value = key_value.partition('=')
    key = key.strip(' \t')
    if sep != '=' or not is_token(key):
        raise _parser.ParseError(f'malformed baggage member: {segment!r}')

    value = raw_value.strip(' \t')
    if not _valid_octets(value):
        raise _parser.ParseError(f'malformed baggage value: {segment!r}')

    properties = (
        _parse_properties(property_str, segment) if property_sep else []
    )
    return key, decode_value(value), properties


def _parse_properties(property_str: str, segment: str) -> list[Property]:
    properties: list[Property] = []
    for raw_property in property_str.split(';'):
        name, sep, raw_value = raw_property.partition('=')
        name = name.strip(' \t')
        if not is_token(name):
            raise _parser.ParseError(
                f'malformed baggage property: {segment!r}'
            )
        if sep != '=':
            properties.append((name, None))
            continue
        value = raw_value.strip(' \t')
        if not _valid_octets(value):
            raise _parser.ParseError(
                f'malformed baggage property: {segment!r}'
            )
        properties.append((name, decode_value(value)))
    return properties
