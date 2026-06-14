"""Implementations of algorithms from various specifications.

- select_content_type: select the best match between an
  HTTP Accept header and a list of available Content-Type's

This module implements some of the more interesting algorithms
described in IETF RFCs.

"""

from __future__ import annotations

import operator
import typing as t
from operator import attrgetter

from ietfparse import _helpers, constants, datastructures, errors

if t.TYPE_CHECKING:
    from collections import abc


def _content_type_matches(
    candidate: datastructures.ContentType, pattern: datastructures.ContentType
) -> bool:
    """Is ``candidate`` an exact match or sub-type of ``pattern``?"""  # noqa: D400

    def _wildcard_compare(type_spec: str, type_pattern: str) -> bool:
        return type_pattern in ('*', type_spec)

    return _wildcard_compare(
        candidate.content_type, pattern.content_type
    ) and _wildcard_compare(candidate.content_subtype, pattern.content_subtype)


MatchKey = tuple[int, int, int]


class _Match(t.NamedTuple):
    candidate: datastructures.ContentType
    pattern: datastructures.ContentType
    match_type: int
    exactness: int
    parameter_distance: int

    @property
    def key(self) -> MatchKey:
        return self.match_type, self.exactness, self.parameter_distance


def _match_type(pattern: datastructures.ContentType) -> int:
    if pattern.content_type == pattern.content_subtype == '*':
        return 2
    if pattern.content_subtype == '*':
        return 1
    return 0


def _parameter_distance(
    candidate: datastructures.ContentType, pattern: datastructures.ContentType
) -> int:
    distance = len(candidate.parameters)
    for key, value in candidate.parameters.items():
        if key in pattern.parameters:
            if pattern.parameters[key] == value:
                distance -= 1
            else:
                distance += 1
    return distance


def _build_match(
    candidate: datastructures.ContentType, pattern: datastructures.ContentType
) -> _Match | None:
    if not _content_type_matches(candidate, pattern):
        return None
    return _Match(
        candidate,
        pattern,
        _match_type(pattern),
        0 if candidate == pattern else 1,
        _parameter_distance(candidate, pattern),
    )


def _is_rejected(
    match: _Match, rejected: abc.Sequence[datastructures.ContentType]
) -> bool:
    return any(
        (rejected_match := _build_match(match.candidate, rejected_pattern))
        is not None
        and rejected_match.key <= match.key
        for rejected_pattern in rejected
    )


def select_content_type(
    requested: abc.Sequence[datastructures.ContentType | str] | str | None,
    available: abc.Sequence[datastructures.ContentType | str],
    *,
    default: datastructures.ContentType | str | None = None,
) -> tuple[datastructures.ContentType, datastructures.ContentType]:
    """Select the best content type.

    This function implements the *Proactive Content Negotiation*
    algorithm as described in [RFC-9110-name-proactive-negotiation].
    The input is the [HTTP-Accept] header as parsed by
    [ietfparse.headers.parse_accept][] and a list of parsed
    [ietfparse.datastructures.ContentType][] instances.
    The `available` sequence should be a sequence of content types
    that the server is capable of producing.  The selected value
    should ultimately be used as the [HTTP-Content-Type] header in
    the generated response.

    :param requested: a sequence of
        [ietfparse.datastructures.ContentType][] instances
    :param available: a sequence of
        [ietfparse.datastructures.ContentType][] instances that the
        server is capable of producing
    :param default: optional default value to return if there is
        no acceptable match
    :returns: the selected content type (from `available`) and the
        pattern that it matched (from `requested`)

    :raises ietfparse.errors.NoMatch: when a suitable match was not found
    :raises ValueError: when `default` is specified and it is not in
        `available`

    """
    _requested, _available, _default = _normalize_parameters(
        requested, available, default
    )

    requested_by_quality = sorted(
        _requested, key=attrgetter('quality'), reverse=True
    )
    rejected = [
        pattern
        for pattern in requested_by_quality
        if pattern.quality < constants.SMALLEST_QUALITY
    ]
    matches = [
        match
        for pattern in requested_by_quality
        if pattern.quality >= constants.SMALLEST_QUALITY
        for candidate in _available
        if (match := _build_match(candidate, pattern)) is not None
        and not _is_rejected(match, rejected)
    ]
    if not matches:
        if _default is not None:
            return _default, _default
        raise errors.NoMatch

    best = min(matches, key=operator.attrgetter('key'))
    return best.candidate, best.pattern


def _normalize_parameters(
    requested: abc.Sequence[datastructures.ContentType | str] | str | None,
    available: abc.Sequence[datastructures.ContentType | str],
    default: datastructures.ContentType | str | None,
) -> tuple[
    abc.Sequence[datastructures.ContentType],
    abc.Sequence[datastructures.ContentType],
    datastructures.ContentType | None,
]:
    if requested is None:
        requested = [default] if default is not None else []
    if isinstance(requested, str):
        _requested = _helpers.parse_header('parse_accept', requested)
    else:
        _requested = [
            r
            if isinstance(r, datastructures.ContentType)
            else _helpers.parse_header('parse_content_type', r)
            for r in requested
        ]

    _available = [
        a
        if isinstance(a, datastructures.ContentType)
        else _helpers.parse_header('parse_content_type', a)
        for a in available
    ]

    if isinstance(default, str):
        default = _helpers.parse_header('parse_content_type', default)
        if default not in _available:
            raise ValueError('default content type not in available')

    return _requested, sorted(_available), default
