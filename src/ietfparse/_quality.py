"""Helpers for normalizing HTTP quality values."""

from __future__ import annotations

import decimal

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
        quality = decimal.Decimal(str(value))
    except decimal.InvalidOperation as error:
        raise ValueError(f'invalid quality value: {value!r}') from error
    if quality.is_nan() or quality.is_infinite():
        raise ValueError(f'invalid quality value: {value!r}')

    if quality < _SMALLEST_QUALITY:
        return 0.0
    if quality > _LARGEST_NONMAXIMAL_QUALITY:
        return 1.0
    return float(quality.quantize(_THOUSANDTH, rounding=decimal.ROUND_HALF_UP))
