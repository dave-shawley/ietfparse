"""Helpers for parsing HTTP Link headers."""

from __future__ import annotations

import typing

from ietfparse import _parser, errors

LinkTarget: typing.TypeAlias = str
Parameter: typing.TypeAlias = tuple[str, str]


class ParameterParser(_parser.CursorParser):
    """Parse a Link header and apply RFC 8288 parameter semantics.

    :param value: the raw Link header value to parse
    :param strict: controls whether parsing follows all
        rules laid out in [RFC-8288-section-3]

    If *strict mode* is enabled, then the first value for the
    `rel`, `media`, `type`, `title`, and `title*` parameters
    is retained and additional values are ignored as described
    in [RFC-8288-section-3].

    """

    def __init__(self, value: str, *, strict: bool = True) -> None:
        super().__init__(value)
        self.strict = strict
        self._reset_parameter_state()

    def parse(self) -> list[tuple[LinkTarget, list[Parameter]]]:
        """Parse the Link header into a sequence of target/parameter pairs."""
        links = []
        self._skip_ows()
        while self.index < len(self.value):
            target = self._parse_target()
            links.append((target, self._parse_parameters()))
        return links

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

    def _error_message(self) -> str:
        return 'Malformed link header'

    def _raise(self, message: str) -> typing.NoReturn:
        raise errors.MalformedLinkValue(message, self.value)

    def _parse_target(self) -> LinkTarget:
        if self.value[self.index] != '<':
            self._raise(self._error_message())

        self.index = self.index + 1
        target_start = self.index
        while self.index < len(self.value) and self.value[self.index] != '>':
            self.index = self.index + 1
        if self.index >= len(self.value):
            self._raise(self._error_message())

        target = self.value[target_start : self.index].strip()
        self.index = self.index + 1
        return target

    def _parse_parameters(self) -> list[Parameter]:
        self._reset_parameter_state()

        while True:
            self._skip_ows()
            if self.index >= len(self.value):
                return self.values
            if self.value[self.index] == ',':
                self.index = self.index + 1
                self._skip_ows()
                return self.values

            self._parse_parameter()

    def _parse_parameter(self) -> None:
        if self.value[self.index] != ';':
            self._raise('Param list missing opening semicolon')

        self.index = self.index + 1
        self._skip_ows()
        if self.index >= len(self.value) or self.value[self.index] in ',;':
            return

        name = self._parse_token().lower()
        self._skip_ows()

        if self.index >= len(self.value) or self.value[self.index] != '=':
            self.add_value(name, '')
            return

        self.index = self.index + 1
        self.add_value(name, self._parse_parameter_value())

    def _reset_parameter_state(self) -> None:
        self._values: list[Parameter] = []
        self._rfc_values: dict[str, str | None] = {
            'rel': None,
            'media': None,
            'type': None,
            'title': None,
            'title*': None,
        }
