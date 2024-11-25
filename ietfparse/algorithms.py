"""Implementations of algorithms from various specifications.

- select_content_type: select the best match between an
  HTTP Accept header and a list of available Content-Type's

This module implements some of the more interesting algorithms
described in IETF RFCs.

"""

from __future__ import annotations

import typing
from operator import attrgetter

from ietfparse import _helpers, datastructures, errors

if typing.TYPE_CHECKING:
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


def select_content_type(  # noqa: C901 -- overly complex
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

    class Match:
        """Sorting assistant.

        Sorting matches is a tricky business.  We need a way to
        prefer content types by *specificity*.  The definition of
        *more specific* is a little less than clear.  This class
        treats the strength of a match as the most important thing.
        Wild cards are less specific in all cases.  This is tracked
        by the ``match_type`` attribute.

        If we the candidate and pattern differ only by parameters,
        then the strength is based on the number of pattern parameters
        that match parameters from the candidate.  The easiest way to
        track this is to count the number of candidate parameters that
        are matched by the pattern.  This is what ``parameter_distance``
        tracks.

        The final key to the solution is to order the result set such
        that the most specific matches are first in the list.  This
        is done by carefully choosing values for ``match_type`` such
        that full matches bubble up to the front.  We also need a
        scheme of counting matching parameters that pushes stronger
        matches to the front of the list.  The `parameter_distance`
        attribute starts at the number of candidate parameters and
        decreases for each matching parameter - the lesser the value,
        the stronger the match.

        """

        FULL_TYPE = 0
        PARTIAL = 1
        WILDCARD = 2

        def __init__(
            self,
            candidate: datastructures.ContentType,
            pattern: datastructures.ContentType,
        ) -> None:
            self.candidate = candidate
            self.pattern = pattern

            if pattern.content_type == pattern.content_subtype == '*':
                self.match_type = self.WILDCARD
            elif pattern.content_subtype == '*':
                self.match_type = self.PARTIAL
            else:
                self.match_type = self.FULL_TYPE

            self.parameter_distance = len(self.candidate.parameters)
            for key, value in candidate.parameters.items():
                if key in pattern.parameters:
                    if pattern.parameters[key] == value:
                        self.parameter_distance -= 1
                    else:
                        self.parameter_distance += 1

    def extract_quality(obj: datastructures.ContentType) -> float:
        return 1.0 if obj.quality is None else obj.quality

    _requested, _available, _default = _normalize_parameters(
        requested, available, default
    )

    matches = []
    for pattern in sorted(_requested, key=extract_quality, reverse=True):
        for candidate in _available:
            if _content_type_matches(candidate, pattern):
                if candidate == pattern:  # exact match!!!
                    if extract_quality(pattern) == 0.0:
                        raise errors.NoMatch  # quality of 0 means NO
                    return candidate, pattern
                matches.append(Match(candidate, pattern))

    if not matches:
        if _default is not None:
            return _default, _default
        raise errors.NoMatch

    matches = sorted(
        matches, key=attrgetter('match_type', 'parameter_distance')
    )
    return matches[0].candidate, matches[0].pattern


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
