"""Curated Cache-Control parsing cases for implementation comparisons."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class CacheControlCase:
    """One Cache-Control sample used for implementation comparisons."""

    case_id: str
    description: str
    sample: str


CASES: tuple[CacheControlCase, ...] = (
    CacheControlCase(
        case_id='boolean-directives',
        description='boolean directives become explicit flags',
        sample='public, no-store',
    ),
    CacheControlCase(
        case_id='numeric-directives',
        description='numeric directives keep their numeric values',
        sample='min-fresh=20, max-age=100',
    ),
    CacheControlCase(
        case_id='quoted-string-directives',
        description='quoted directive values preserve embedded spacing',
        sample='community="UCI", x-token=" foo bar "',
    ),
    CacheControlCase(
        case_id='private-field-list',
        description='token directives can carry quoted field-name lists',
        sample='no-cache, private="Set-Cookie"',
    ),
    CacheControlCase(
        case_id='empty-value',
        description='empty directive values are ignored or preserved',
        sample='x-should-be-ignored=',
    ),
    CacheControlCase(
        case_id='trailing-empty-item',
        description='trailing empty list members are ignored',
        sample='max-age=100,',
    ),
    CacheControlCase(
        case_id='empty-segments',
        description='completely empty segments are ignored',
        sample=',,',
    ),
)
