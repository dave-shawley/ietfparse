"""Compatibility helpers for supported Python versions."""

from __future__ import annotations

import enum
import sys
import typing as t

__all__ = ['StrEnum', 'assert_never', 'tomllib']

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover -- Python 3.10 fallback
    import tomli as tomllib

if hasattr(enum, 'StrEnum'):
    StrEnum = enum.StrEnum
else:  # pragma: no cover -- Python 3.10 fallback

    class StrEnum(str, enum.Enum):
        """Backport of :class:`enum.StrEnum` for Python 3.10."""

        def __str__(self) -> str:
            return str.__str__(self)


if hasattr(t, 'assert_never'):
    assert_never = t.assert_never
else:  # pragma: no cover -- Python 3.10 fallback

    def assert_never(value: t.NoReturn) -> t.NoReturn:
        """Backport of :func:`typing.assert_never` for Python 3.10."""
        msg = f'Expected code to be unreachable, but got: {value!r}'
        raise AssertionError(msg)
