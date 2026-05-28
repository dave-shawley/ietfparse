from __future__ import annotations

import typing

from ietfparse import headers

if typing.TYPE_CHECKING:
    from collections import abc

    from ietfparse import datastructures


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
