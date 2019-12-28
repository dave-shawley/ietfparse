from typing import Optional, Sequence, Tuple


def quote(a: bytes, safe: bytes) -> str:
    ...


def splitnport(host: str, defport: Optional[int] = -1) -> Tuple[str, int]:
    ...


def splitpasswd(a: str) -> Tuple[str, str]:
    ...


def splituser(a: str) -> Tuple[str, str]:
    ...


def unquote(a: str) -> str:
    ...


def unquote_to_bytes(a: str) -> bytes:
    ...


def urlencode(pairs: Sequence[Tuple[int, int]]) -> str:
    ...


def urlsplit(url: str) -> Tuple[str, str, str, str, str]:
    ...


def urlunsplit(parts: Tuple[str, str, str, str, str]) -> str:
    ...
