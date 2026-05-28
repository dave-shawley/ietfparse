"""Shared cursor-based parsing helpers for HTTP-style field values."""

from __future__ import annotations

import re

_OWS = ' \t'
_TOKEN_CHARS = frozenset(
    "!#$%&'*+-.^_`|~"
    '0123456789'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abcdefghijklmnopqrstuvwxyz'
)
_TOKEN_PATTERN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


class ParseError(RuntimeError):
    """Raised internally when cursor-based parsing fails."""


class CursorParser:
    """Walk a string value with reusable token and quoted-string parsers."""

    def __init__(self, value: str) -> None:
        self.value = value
        self.index = 0

    def skip_ows(self) -> None:
        while self.index < len(self.value) and self.value[self.index] in _OWS:
            self.index = self.index + 1

    def parse_parameter_value(self) -> str:
        self.skip_ows()
        if self.index >= len(self.value):
            raise ParseError(f'malformed parser input: {self.value!r}')
        if self.value[self.index] == '"':
            return self.parse_quoted_string()
        return self.parse_token()

    def parse_token(self) -> str:
        start = self.index
        while (
            self.index < len(self.value)
            and self.value[self.index] in _TOKEN_CHARS
        ):
            self.index = self.index + 1
        if start == self.index:
            raise ParseError(f'malformed parser input: {self.value!r}')
        return self.value[start : self.index]

    def parse_quoted_string(self) -> str:
        parsed = []
        self.index = self.index + 1
        while self.index < len(self.value):
            if self.value[self.index] == '\\':
                self.index = self.index + 1
                if self.index >= len(self.value):
                    raise ParseError(f'malformed parser input: {self.value!r}')
                parsed.append(self.value[self.index])
            elif self.value[self.index] == '"':
                self.index = self.index + 1
                return ''.join(parsed)
            else:
                parsed.append(self.value[self.index])
            self.index = self.index + 1

        raise ParseError(f'malformed parser input: {self.value!r}')

    def skip_comment(self) -> None:
        if self.index >= len(self.value) or self.value[self.index] != '(':
            raise ParseError(f'malformed parser input: {self.value!r}')

        depth = 1
        self.index = self.index + 1
        while self.index < len(self.value):
            if self.value[self.index] == '\\':
                self.index = self.index + 1
                if self.index >= len(self.value):
                    raise ParseError(f'malformed parser input: {self.value!r}')
            elif self.value[self.index] == '(':
                depth = depth + 1
            elif self.value[self.index] == ')':
                depth = depth - 1
                if depth == 0:
                    self.index = self.index + 1
                    return
            self.index = self.index + 1

        raise ParseError(f'malformed parser input: {self.value!r}')


class ParameterTokenizer:
    """Tokenize semicolon-delimited HTTP parameter strings."""

    def __init__(
        self,
        *,
        normalize_parameter_names: bool = False,
        normalize_parameter_values: bool = True,
    ) -> None:
        self.normalize_parameter_names = normalize_parameter_names
        self.normalize_parameter_values = normalize_parameter_values

    def parse(self, value: str) -> list[tuple[str, str]]:
        cursor = CursorParser(value)
        parameters = []
        try:
            while True:
                cursor.skip_ows()
                if cursor.index >= len(cursor.value):
                    return parameters
                if cursor.value[cursor.index] == ';':
                    cursor.index = cursor.index + 1
                    continue
                parameters.append(self._parse_parameter(cursor))
                cursor.skip_ows()
                if cursor.index >= len(cursor.value):
                    return parameters
                if cursor.value[cursor.index] != ';':
                    raise ValueError(self._error_message(cursor))
                cursor.index = cursor.index + 1
        except ParseError as exc:
            raise ValueError(self._error_message(cursor)) from exc

    @staticmethod
    def _error_message(cursor: CursorParser) -> str:
        return f'malformed parameter list: {cursor.value!r}'

    def _parse_parameter(self, cursor: CursorParser) -> tuple[str, str]:
        name = cursor.parse_token()
        cursor.skip_ows()
        if (
            cursor.index >= len(cursor.value)
            or cursor.value[cursor.index] != '='
        ):
            raise ParseError(self._error_message(cursor))

        cursor.index = cursor.index + 1
        value = cursor.parse_parameter_value()
        if self.normalize_parameter_names:
            name = name.lower()
        if self.normalize_parameter_values:
            value = value.lower()
        return name, value


_PARAMETER_TOKENIZERS = {
    (False, False): ParameterTokenizer(
        normalize_parameter_values=False,
    ),
    (False, True): ParameterTokenizer(),
    (True, False): ParameterTokenizer(
        normalize_parameter_names=True,
        normalize_parameter_values=False,
    ),
    (True, True): ParameterTokenizer(normalize_parameter_names=True),
}


def parse_http_parameters(
    value: str,
    *,
    normalize_parameter_names: bool = False,
    normalize_parameter_values: bool = True,
) -> list[tuple[str, str]]:
    """Parse semicolon-delimited HTTP parameters."""
    if '\\' not in value and '"' not in value:
        return _fast_parse_http_parameters(
            value,
            normalize_parameter_names=normalize_parameter_names,
            normalize_parameter_values=normalize_parameter_values,
        )

    return _PARAMETER_TOKENIZERS[
        (normalize_parameter_names, normalize_parameter_values)
    ].parse(value)


def parse_list_items(value: str) -> list[str]:
    """Parse a comma-delimited list while respecting quoted strings."""
    if '\\' not in value and '"' not in value:
        return [segment.strip() for segment in value.split(',')]

    cursor = CursorParser(value)
    parsed: list[str] = []
    current: list[str] = []

    while cursor.index < len(cursor.value):
        if cursor.value[cursor.index] == '"':
            start = cursor.index
            cursor.parse_quoted_string()
            current.append(cursor.value[start : cursor.index])
        elif cursor.value[cursor.index] == ',':
            parsed.append(''.join(current).strip())
            current = []
            cursor.index = cursor.index + 1
        else:
            current.append(cursor.value[cursor.index])
            cursor.index = cursor.index + 1

    parsed.append(''.join(current).strip())
    return parsed


def remove_http_comments(value: str) -> str:
    """Strip HTTP comments while preserving quoted strings."""
    if '(' not in value:
        return value

    cursor = CursorParser(value)
    parsed = []

    while cursor.index < len(cursor.value):
        if cursor.value[cursor.index] == '"':
            start = cursor.index
            cursor.parse_quoted_string()
            parsed.append(cursor.value[start : cursor.index])
            continue

        if cursor.value[cursor.index] == '(':
            cursor.skip_comment()
            continue

        parsed.append(cursor.value[cursor.index])
        cursor.index = cursor.index + 1

    return ''.join(parsed)


def _fast_parse_http_parameters(
    value: str,
    *,
    normalize_parameter_names: bool,
    normalize_parameter_values: bool,
) -> list[tuple[str, str]]:
    error_message = f'malformed parameter list: {value!r}'
    parameters: list[tuple[str, str]] = []
    for raw_segment in value.split(';'):
        segment = raw_segment.strip()
        if not segment:
            continue

        name, sep, parameter_value = segment.partition('=')
        if sep != '=':
            raise ValueError(error_message)

        name = name.strip()
        parameter_value = parameter_value.strip()
        if not name or not parameter_value:
            raise ValueError(error_message)
        if _TOKEN_PATTERN.fullmatch(name) is None:
            raise ValueError(error_message)

        if _TOKEN_PATTERN.fullmatch(parameter_value) is None:
            raise ValueError(error_message)

        if normalize_parameter_names:
            name = name.lower()
        if normalize_parameter_values:
            parameter_value = parameter_value.lower()
        parameters.append((name, parameter_value))

    return parameters
