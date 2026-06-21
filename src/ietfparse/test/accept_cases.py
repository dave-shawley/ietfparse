"""Curated Accept header selection cases for implementation comparisons."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class AcceptCase:
    """One Accept/content-negotiation sample used for comparisons."""

    case_id: str
    description: str
    accept: str
    available: tuple[str, ...]
    default: str | None = None


CASES: tuple[AcceptCase, ...] = (
    AcceptCase(
        case_id='exact-match',
        description='exact match beats lower-quality fallback',
        accept='application/json, text/plain;q=0.5',
        available=('text/plain', 'application/json'),
    ),
    AcceptCase(
        case_id='parameter-specificity',
        description='parameter-specific match beats generic variant',
        accept=(
            'text/html;level=1, text/html;q=0.7, text/plain;q=0.5, */*;q=0.1'
        ),
        available=('text/html', 'text/html;level=1'),
    ),
    AcceptCase(
        case_id='range-rejection',
        description='zero-quality range rejection excludes matching candidate',
        accept='text/*;q=0, application/*;q=0.5',
        available=('text/plain', 'application/json'),
    ),
    AcceptCase(
        case_id='specific-over-broader-rejection',
        description='more-specific positive match overrides broader rejection',
        accept='text/plain, text/*;q=0, */*;q=0.5',
        available=('text/plain', 'application/json'),
    ),
    AcceptCase(
        case_id='default-fallback',
        description='default is returned when no acceptable match exists',
        accept='image/png',
        available=('application/json', 'text/plain'),
        default='application/json',
    ),
    AcceptCase(
        case_id='no-match',
        description='no acceptable match without a default',
        accept='image/png',
        available=('application/json', 'text/plain'),
    ),
    AcceptCase(
        case_id='available-order-tie-break',
        description='multiple equal wildcard matches preserve available order',
        accept='text/*;q=0.8',
        available=('text/plain', 'text/html'),
    ),
)
