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
        index = self.index
        value_len = len(self.value)
        value = self.value
        while index < value_len and value[index] in _TOKEN_CHARS:
            index += 1
        self.index = index
        if start == index:
            raise ParseError(f'malformed parser input: {self.value!r}')
        return value[start:index]

    def parse_quoted_string(self) -> str:
        parsed = []
        value = self.value
        index = self.index + 1
        value_len = len(value)
        while index < value_len:
            if value[index] == '\\':
                index += 1
                if index >= value_len:
                    self.index = index
                    raise ParseError(f'malformed parser input: {self.value!r}')
                parsed.append(value[index])
            elif value[index] == '"':
                self.index = index + 1
                return ''.join(parsed)
            else:
                parsed.append(value[index])
            index += 1

        self.index = index
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
    if '\\' not in value:
        return _parse_list_items_without_escapes(value)

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


def _parse_list_items_without_escapes(value: str) -> list[str]:
    """Parse list items when quoted strings cannot contain escapes."""
    parsed: list[str] = []
    start = 0
    in_quotes = False

    for index, char in enumerate(value):
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            parsed.append(value[start:index].strip())
            start = index + 1

    if in_quotes:
        raise ParseError(f'malformed parser input: {value!r}')

    parsed.append(value[start:].strip())
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
