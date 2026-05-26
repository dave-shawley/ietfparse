"""Helpers for normalizing HTTP quality values."""

from __future__ import annotations

import decimal
import math

_THOUSANDTH = decimal.Decimal('0.001')
_SMALLEST_QUALITY = _THOUSANDTH
_LARGEST_NONMAXIMAL_QUALITY = decimal.Decimal('0.999')

SMALLEST_QUALITY = float(_SMALLEST_QUALITY)
LARGEST_NONMAXIMAL_QUALITY = float(_LARGEST_NONMAXIMAL_QUALITY)


def normalize_quality(
    value: str | float | decimal.Decimal,
) -> float:
    """Normalize quality values to thousandth precision."""
    try:
        quality = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f'invalid quality value: {value!r}') from error
    if not math.isfinite(quality):
        raise ValueError(f'invalid quality value: {value!r}')

    if quality < SMALLEST_QUALITY:
        return 0.0
    if quality > LARGEST_NONMAXIMAL_QUALITY:
        return 1.0
    return math.floor((quality * 1000.0) + 0.5) / 1000.0
