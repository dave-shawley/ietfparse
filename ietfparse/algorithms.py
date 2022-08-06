"""
Implementations of algorithms from various specifications.

- :func:`.select_content_type`: select the best match between a
  HTTP ``Accept`` header and a list of available ``Content-Type`` s

This module implements some of the more interesting algorithms
described in IETF RFCs.

"""
from __future__ import annotations

from collections import abc
from operator import attrgetter

from ietfparse import datastructures, errors


def _content_type_matches(candidate: datastructures.ContentType,
                          pattern: datastructures.ContentType) -> bool:
    """Is ``candidate`` an exact match or sub-type of ``pattern``?"""
    def _wildcard_compare(type_spec: str, type_pattern: str) -> bool:
        return type_pattern == '*' or type_spec == type_pattern

    return (_wildcard_compare(candidate.content_type, pattern.content_type)
            and _wildcard_compare(candidate.content_subtype,
                                  pattern.content_subtype))


def select_content_type(
    requested: abc.Sequence[datastructures.ContentType],
    available: abc.Sequence[datastructures.ContentType]
) -> tuple[datastructures.ContentType, datastructures.ContentType]:
    """Selects the best content type.

    :param requested: a sequence of :class:`.ContentType` instances
    :param available: a sequence of :class:`.ContentType` instances
        that the server is capable of producing

    :returns: the selected content type (from ``available``) and the
        pattern that it matched (from ``requested``)
    :rtype: :class:`tuple` of :class:`.ContentType` instances
    :raises: :class:`.NoMatch` when a suitable match was not found

    This function implements the *Proactive Content Negotiation*
    algorithm as described in sections 3.4.1 and 5.3 of :rfc:`7231`.
    The input is the `Accept`_ header as parsed by
    :func:`.parse_http_accept_header` and a list of
    parsed :class:`.ContentType` instances.  The ``available`` sequence
    should be a sequence of content types that the server is capable of
    producing.  The selected value should ultimately be used as the
    `Content-Type`_ header in the generated response.

    .. _Accept: https://tools.ietf.org/html/rfc7231#section-5.3.2
    .. _Content-Type: https://tools.ietf.org/html/rfc7231#section-3.1.1.5

    """
    class Match(object):
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
        matches to the front of the list.  The ``parameter_distance``
        attribute starts at the number of candidate parameters and
        decreases for each matching parameter - the lesser the value,
        the stronger the match.

        """
        WILDCARD, PARTIAL, FULL_TYPE, = 2, 1, 0

        def __init__(self, candidate: datastructures.ContentType,
                     pattern: datastructures.ContentType) -> None:
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

    matches = []
    for pattern in sorted(requested, key=extract_quality, reverse=True):
        for candidate in sorted(available):
            if _content_type_matches(candidate, pattern):
                if candidate == pattern:  # exact match!!!
                    if extract_quality(pattern) == 0.0:
                        raise errors.NoMatch  # quality of 0 means NO
                    return candidate, pattern
                matches.append(Match(candidate, pattern))

    if not matches:
        raise errors.NoMatch

    matches = sorted(matches,
                     key=attrgetter('match_type', 'parameter_distance'))
    return matches[0].candidate, matches[0].pattern
