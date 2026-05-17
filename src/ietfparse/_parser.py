"""Shared cursor-based parsing helpers for HTTP-style field values."""

from __future__ import annotations

import typing

_OWS = ' \t'
_TOKEN_CHARS = frozenset(
    "!#$%&'*+-.^_`|~"
    '0123456789'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abcdefghijklmnopqrstuvwxyz'
)


class CursorParser:
    """Walk a string value with reusable token and quoted-string parsers."""

    def __init__(self, value: str) -> None:
        self.value = value
        self.index = 0

    def _error_message(self) -> str:
        """Override to customize the error message."""
        return f'malformed parser input: {self.value!r}'

    def _raise(self, message: str) -> typing.NoReturn:
        """Override to customize the raised exception."""
        raise ValueError(message)

    def _skip_ows(self) -> None:
        while self.index < len(self.value) and self.value[self.index] in _OWS:
            self.index = self.index + 1

    def _parse_parameter_value(self) -> str:
        self._skip_ows()
        if self.index >= len(self.value):
            self._raise(self._error_message())
        if self.value[self.index] == '"':
            return self._parse_quoted_string()
        return self._parse_token()

    def _parse_token(self) -> str:
        start = self.index
        while (
            self.index < len(self.value)
            and self.value[self.index] in _TOKEN_CHARS
        ):
            self.index = self.index + 1
        if start == self.index:
            self._raise(self._error_message())
        return self.value[start : self.index]

    def _parse_quoted_string(self) -> str:
        parsed = []
        self.index = self.index + 1
        while self.index < len(self.value):
            if self.value[self.index] == '\\':
                self.index = self.index + 1
                if self.index >= len(self.value):
                    self._raise(self._error_message())
                parsed.append(self.value[self.index])
            elif self.value[self.index] == '"':
                self.index = self.index + 1
                return ''.join(parsed)
            else:
                parsed.append(self.value[self.index])
            self.index = self.index + 1

        self._raise(self._error_message())
        raise AssertionError('unreachable')


class ParameterTokenizer(CursorParser):
    """Tokenize semicolon-delimited HTTP parameter strings."""

    def __init__(
        self,
        value: str,
        *,
        normalize_parameter_names: bool = False,
        normalize_parameter_values: bool = True,
    ) -> None:
        super().__init__(value)
        self.normalize_parameter_names = normalize_parameter_names
        self.normalize_parameter_values = normalize_parameter_values

    def parse(self) -> list[tuple[str, str]]:
        parameters = []
        while True:
            self._skip_ows()
            if self.index >= len(self.value):
                return parameters
            if self.value[self.index] == ';':
                self.index = self.index + 1
                continue
            parameters.append(self._parse_parameter())
            self._skip_ows()
            if self.index >= len(self.value):
                return parameters
            if self.value[self.index] != ';':
                self._raise(self._error_message())
            self.index = self.index + 1

    def _error_message(self) -> str:
        return f'malformed parameter list: {self.value!r}'

    def _parse_parameter(self) -> tuple[str, str]:
        name = self._parse_token()
        self._skip_ows()
        if self.index >= len(self.value) or self.value[self.index] != '=':
            self._raise(self._error_message())

        self.index = self.index + 1
        value = self._parse_parameter_value()
        if self.normalize_parameter_names:
            name = name.lower()
        if self.normalize_parameter_values:
            value = value.lower()
        return name, value
