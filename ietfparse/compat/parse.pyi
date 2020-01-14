from typing import Optional, Sequence, Tuple


class _ParseResult:
    fragment: Optional[str]
    hostname: Optional[str]
    password: Optional[str]
    scheme: Optional[str]
    username: Optional[str]
    port: Optional[int]
    path: Optional[str]
    query: str
    params: str


def quote(a: bytes, safe: bytes) -> str:
    ...


def unquote_to_bytes(a: str) -> bytes:
    ...


def urlencode(pairs: Sequence[Tuple[int, int]]) -> str:
    ...


def urlparse(url: str) -> _ParseResult:
    ...


def urlunparse(parsed: Tuple[str, str, str, str, str, str]) -> str:
    ...
