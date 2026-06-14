"""Helpers for parsing HTTP Link headers."""

from __future__ import annotations

import typing as t

from ietfparse import _parser, errors

LinkTarget: t.TypeAlias = str
Parameter: t.TypeAlias = tuple[str, str]


class ParameterParser:
    """Parse a Link header and apply RFC 8288 parameter semantics.

    :param strict: controls whether parsing follows all
        rules laid out in [RFC-8288-section-3]

    If *strict mode* is enabled, then the first value for the
    `rel`, `media`, `type`, `title`, and `title*` parameters
    is retained and additional values are ignored as described
    in [RFC-8288-section-3].

    """

    def __init__(self, *, strict: bool = True) -> None:
        self.strict = strict

    def parse(self, value: str) -> list[tuple[LinkTarget, list[Parameter]]]:
        """Parse the Link header into a sequence of target/parameter pairs."""
        cursor = _parser.CursorParser(value)
        links = []
        try:
            cursor.skip_ows()
            while cursor.index < len(cursor.value):
                target = self._parse_target(cursor)
                links.append((target, self._parse_parameters(cursor)))
        except _parser.ParseError as exc:
            raise errors.MalformedLinkValue(*exc.args, value) from exc
        else:
            return links

    def _add_value(
        self,
        values: list[Parameter],
        rfc_values: dict[str, str | None],
        name: str,
        value: str,
    ) -> None:
        """Add a new parameter to the parsed value list."""
        try:
            if rfc_values[name] is None:
                rfc_values[name] = value
            elif self.strict:
                return
        except KeyError:
            pass

        if self.strict and name in ('title', 'title*'):
            return

        values.append((name, value))

    def _normalized_values(
        self,
        values: list[Parameter],
        rfc_values: dict[str, str | None],
    ) -> list[Parameter]:
        normalized = values[:]
        if self.strict:
            preferred_title = rfc_values['title*']
            fallback_title = rfc_values['title']
            if preferred_title is not None:
                normalized.append(('title*', preferred_title))
                if fallback_title is not None:
                    normalized.append(('title', preferred_title))
            elif fallback_title is not None:
                normalized.append(('title', fallback_title))
        return normalized

    @staticmethod
    def _parse_target(cursor: _parser.CursorParser) -> LinkTarget:
        if cursor.value[cursor.index] != '<':
            raise _parser.ParseError('Malformed link header')

        cursor.index = cursor.index + 1
        target_start = cursor.index
        while (
            cursor.index < len(cursor.value)
            and cursor.value[cursor.index] != '>'
        ):
            cursor.index = cursor.index + 1
        if cursor.index >= len(cursor.value):
            raise _parser.ParseError('Malformed link header')

        target = cursor.value[target_start : cursor.index].strip()
        cursor.index = cursor.index + 1
        return target

    def _parse_parameters(
        self,
        cursor: _parser.CursorParser,
    ) -> list[Parameter]:
        values: list[Parameter] = []
        rfc_values: dict[str, str | None] = {
            'rel': None,
            'media': None,
            'type': None,
            'title': None,
            'title*': None,
        }

        while True:
            cursor.skip_ows()
            if cursor.index >= len(cursor.value):
                return self._normalized_values(values, rfc_values)
            if cursor.value[cursor.index] == ',':
                cursor.index = cursor.index + 1
                cursor.skip_ows()
                return self._normalized_values(values, rfc_values)

            self._parse_parameter(cursor, values, rfc_values)

    def _parse_parameter(
        self,
        cursor: _parser.CursorParser,
        values: list[Parameter],
        rfc_values: dict[str, str | None],
    ) -> None:
        if cursor.value[cursor.index] != ';':
            raise _parser.ParseError('Param list missing opening semicolon')

        cursor.index = cursor.index + 1
        cursor.skip_ows()
        if (
            cursor.index >= len(cursor.value)
            or cursor.value[cursor.index] in ',;'
        ):
            return

        name = cursor.parse_token().lower()
        cursor.skip_ows()

        if (
            cursor.index >= len(cursor.value)
            or cursor.value[cursor.index] != '='
        ):
            self._add_value(values, rfc_values, name, '')
            return

        cursor.index = cursor.index + 1
        self._add_value(
            values,
            rfc_values,
            name,
            cursor.parse_parameter_value(),
        )


def parse_link_header(
    value: str, *, strict: bool = True
) -> list[tuple[LinkTarget, list[Parameter]]]:
    """Parse a Link header into target/parameter pairs."""
    return ParameterParser(strict=strict).parse(value)
