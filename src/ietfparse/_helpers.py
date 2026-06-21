from __future__ import annotations

import typing as t

from ietfparse import headers

if t.TYPE_CHECKING:
    from collections import abc

    from ietfparse import datastructures


@t.overload
def parse_header(
    parser_name: t.Literal['parse_accept'], value: str
) -> abc.Sequence[datastructures.ContentType]: ...


@t.overload
def parse_header(
    parser_name: t.Literal['parse_content_type'], value: str
) -> datastructures.ContentType: ...


@t.overload
def parse_header(
    parser_name: t.Literal['parse_link'], value: str
) -> abc.Sequence[datastructures.LinkHeader]: ...


def parse_header(parser_name: str, value: str) -> object:
    try:
        return getattr(headers, parser_name)(value)
    except AttributeError:
        raise NotImplementedError(f'unknown parser {parser_name}') from None
    except ValueError:
        return value
