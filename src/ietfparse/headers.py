"""Functions for parsing headers.

- :func:`.parse_accept`: parse an ``Accept`` value
- :func:`.parse_accept_charset`: parse a ``Accept-Charset`` value
- :func:`.parse_cache_control`: parse a ``Cache-Control`` value
- :func:`.parse_content_type`: parse a ``Content-Type`` value
- :func:`.parse_forwarded`: parse a :rfc:`7239` ``Forwarded`` value
- :func:`.parse_link`: parse a :rfc:`5988` ``Link`` value
- :func:`.parse_list`: parse a comma-separated list that is
  present in so many headers

"""

from __future__ import annotations

import contextlib
import operator
import typing

from ietfparse import _links, _parser, _quality, datastructures, errors

_CACHE_CONTROL_BOOL_DIRECTIVES = (
    'must-revalidate',
    'no-cache',
    'no-store',
    'no-transform',
    'only-if-cached',
    'public',
    'private',
    'proxy-revalidate',
)
T = typing.TypeVar('T')


class _QualifiedItem(typing.Generic[T]):
    def __init__(self, value: T, quality: str | None, index: int) -> None:
        self.value = value
        self.quality = (
            1.0 if quality is None else _quality.normalize_quality(quality)
        )
        self.explicit_quality = quality is not None
        self.index = index

    @property
    def is_explicit_max(self) -> bool:
        return self.explicit_quality and self.quality == 1.0

    @property
    def is_rejected(self) -> bool:
        return self.quality < _quality.SMALLEST_QUALITY


def parse_accept(
    header_value: str, *, strict: bool = False
) -> list[datastructures.ContentType]:
    """Parse an HTTP Accept header.

    "Accept" is a class of headers that contain a list of values
    and an associated preference value. The ever present [HTTP-Accept]
    header is a perfect example. It is a list of content types and
    an optional parameter named ``q`` that indicates the relative
    weight of a particular type.  The most basic example is:

        Accept: audio/*;q=0.2, audio/basic

    Which states that I prefer the `audio/basic` content type
    but will accept other `audio` subtypes with an 80% mark down.

    !!! warning
        This function will raise a [ValueError][] when in encounters
        an invalid value such as `*` which happens much more frequently
        than you might expect.

    :param header_value: the header value to parse
    :param strict: if truthy, then invalid content type values within
        `header_value` will raise [ValueError][]; otherwise, they are
        ignored
    :return: a [list][] of [ietfparse.datastructures.ContentType][]
        instances in decreasing quality order.  Each instance is
        augmented with the associated quality as a ``float`` property
        named ``quality``.
    :raise ValueError: if `strict` is *truthy* and at least one
        value in `header_value` could not be parsed by
        [ietfparse.headers.parse_content_type][]

    """
    guard: contextlib.AbstractContextManager[None]
    if strict:
        guard = contextlib.nullcontext()
    else:
        guard = contextlib.suppress(ValueError)

    decorated: list[_QualifiedItem[datastructures.ContentType]] = []
    for index, content_type in enumerate(parse_list(header_value)):
        if not content_type.strip():
            if strict:
                raise errors.MalformedContentType(content_type)
            continue
        header: datastructures.ContentType | None = None
        with guard:
            header = parse_content_type(content_type)
        if header is None:
            continue
        decorated.append(
            _QualifiedItem(header, header.parameters.pop('q', None), index)
        )
        header.quality = decorated[-1].quality

    explicit_max = [item.value for item in decorated if item.is_explicit_max]
    remaining = sorted(
        [item for item in decorated if not item.is_explicit_max],
        key=lambda item: (item.quality, item.value),
        reverse=True,
    )
    return explicit_max + [item.value for item in remaining]


def parse_accept_charset(header_value: str) -> list[str]:
    """Parse an Accept-Charset header into a sorted list.

    The [HTTP-Accept-Charset] header is a list of character set names with
    optional *quality* values. The quality value indicates the strength
    of the preference where 1.0 is a strong preference and less than 0.001
    is outright rejection by the client.

    !!! note
        Character sets are rejected if their quality value is less than
        0.001. If a wildcard is included in the header, then it will
        appear **BEFORE** any rejected values.

    :param header_value: header value to parse
    :return: list of character sets sorted from highest to lowest
        priority

    """
    return _parse_qualified_list(header_value)


def parse_accept_encoding(header_value: str) -> list[str]:
    """Parse an `Accept-Encoding` header into a sorted list.

    The [HTTP-Accept-Encoding] header is a list of encodings with
    optional *quality* values. The quality value indicates the strength
    of the preference where 1.0 is a strong preference and less than 0.001
    is outright rejection by the client.

    !!! note
        Encodings are rejected if their quality value is less than
        0.001. If a wildcard is included in the header, then it will
        appear **BEFORE** any rejected values.

    :param header_value: header value to parse
    :return: list of encodings sorted from highest to lowest priority

    """
    return _parse_qualified_list(header_value)


def parse_accept_language(header_value: str) -> list[str]:
    """Parse an Accept-Language header into a sorted list.

    The [HTTP-Accept-Language] header is a list of languages with
    optional *quality* values. The quality value indicates the strength
    of the preference where 1.0 is a strong preference and less than 0.001
    is outright rejection by the client.

    !!! note
        Languages are rejected if their quality value is less than
        0.001. If a wildcard is included in the header, then it will
        appear **BEFORE** any rejected values.

    :param header_value: header value to parse
    :return: list of languages sorted from highest to lowest priority

    """
    return _parse_qualified_list(header_value)


def parse_cache_control(
    header_value: str,
) -> dict[str, str | int | bool | None]:
    """Parse a Cache-Control header, returning a dict of key-value pairs.

    Any of the [HTTP-Cache-Control] parameters that do not have directives,
    such as `public` or `no-cache` will be returned with a value of `True`
    if they are set in the header.

    :param header_value: the header value to parse
    :return: the parsed Cache-Control directives

    """
    directives: dict[str, str | int | bool | None] = {}

    for segment in parse_list(header_value):
        if not segment.strip():
            continue
        name, sep, value = segment.partition('=')
        if not name.strip():
            continue
        if sep != '=':
            directives[name] = None
        elif sep and value:
            value = _dequote(value.strip())
            try:
                directives[name] = int(value)
            except ValueError:
                directives[name] = value
        # NB ``name='' is never valid and is ignored!

    # convert parameterless boolean directives
    for name in _CACHE_CONTROL_BOOL_DIRECTIVES:
        if directives.get(name, '') is None:
            directives[name] = True

    return directives


def parse_content_type(
    content_type: str, *, normalize_parameter_values: bool = True
) -> datastructures.ContentType:
    """Parse a content type like header.

    The [HTTP-Content-Type] header describes the format and semantics
    of the enclosed entity. Though they look similar, this header
    differs from the [HTTP-Accept] header which advertises the
    client's preferred response types.

    :param content_type: the string to parse as a content type
    :param normalize_parameter_values:
        setting this to `False` will enable strict [RFC-2045]
        compliance in which content parameter values are case
        preserving.
    :return: the parsed content type
    :raise ietfparse.errors.MalformedContentType:
        if the content type cannot be parsed (eg, `Content-Type: *`)

    """
    type_spec, _, parameter_str = _parser.remove_http_comments(
        content_type
    ).partition(';')
    try:
        content_type, content_subtype = type_spec.split('/')
    except ValueError as error:
        raise errors.MalformedContentType(content_type) from error

    parameters = _parse_parameter_list(
        parameter_str,
        normalize_parameter_values=normalize_parameter_values,
    )
    if '+' in content_subtype:
        try:
            content_subtype, content_suffix = content_subtype.split('+')
        except ValueError as error:
            raise errors.MalformedContentType(content_type) from error
        return datastructures.ContentType(
            content_type, content_subtype, dict(parameters), content_suffix
        )
    return datastructures.ContentType(
        content_type, content_subtype, dict(parameters)
    )


def parse_forwarded(
    header_value: str, *, only_standard_parameters: bool = False
) -> list[dict[str, str]]:
    """Parse an [RFC-7239] Forwarded header.

    This function parses a [HTTP-Forwarded] header into a [list][]
    of [dict][] instances with each instance containing the parameter
    values.  The list is ordered as received from left to right and
    the parameter names are folded to lower case strings.

    :param header_value: value to parse
    :param only_standard_parameters: if specified and *truthy*, then a
        non-standard parameter name will result in
        a [ietfparse.errors.StrictHeaderParsingFailure][]
    :return: an ordered [list][] of [dict][] instances
    :raises ietfparse.errors.StrictHeaderParsingFailure:
        if `only_standard_parameters` is enabled and a non-standard
        parameter name is encountered

    """
    standard_parameters = {'for', 'proto', 'by', 'host'}
    result = []
    for entry in parse_list(header_value):
        if not entry.strip():
            continue
        param_tuples = _parse_parameter_list(
            entry,
            normalize_parameter_names=True,
            normalize_parameter_values=False,
        )
        if only_standard_parameters and any(
            name not in standard_parameters for name, _ in param_tuples
        ):
            raise errors.StrictHeaderParsingFailure('Forwarded', header_value)
        result.append(dict(param_tuples))
    return result


def parse_link(
    header_value: str, *, strict: bool = True
) -> list[datastructures.LinkHeader]:
    """Parse an HTTP Link header.

    Parses the [HTTP-Link] header into a sequence of
    [ietfparse.datastructures.LinkHeader][] instances.

    :param header_value: the header value to parse
    :param strict: set this to [False][] to disable semantic
        checking.  Syntactical errors will still raise an
        exception. Use this if you want to receive all parameters.
    :return: a sequence of [ietfparse.datastructures.LinkHeader][]
        instances
    :raise ietfparse.errors.MalformedLinkValue:
        if the specified `header_value` cannot be parsed

    """
    return [
        datastructures.LinkHeader(target, params)
        for target, params in _links.parse_link_header(
            header_value, strict=strict
        )
    ]


def parse_list(value: str) -> list[str]:
    """Parse a comma-separated list header.

    :param value: header value to split into elements
    :return: list of header elements as strings

    """
    return [_dequote(segment) for segment in _parser.parse_list_items(value)]


def _parse_parameter_list(
    parameter_list: str,
    *,
    normalize_parameter_names: bool = False,
    normalize_parameter_values: bool = True,
) -> list[tuple[str, str]]:
    """Parse a named parameter list in the "common" format.

    :param parameter_list: semicolon-delimited parameter string
    :keyword normalize_parameter_names: if specified and *truthy*
        then parameter names will be case-folded to lower case
    :keyword normalize_parameter_values: if omitted or specified
        as *truthy*, then parameter values are case-folded to lower case
    :return: a sequence containing the name to value pairs

    The parsed values are normalized according to the keyword parameters
    and returned as :class:`tuple` of name to value pairs preserving the
    ordering from `parameter_list`. Quoted strings are unescaped while
    being tokenized.

    """
    return _parser.parse_http_parameters(
        parameter_list,
        normalize_parameter_names=normalize_parameter_names,
        normalize_parameter_values=normalize_parameter_values,
    )


def _parse_qualified_list(value: str) -> list[str]:
    """Parse `value` as a comma-separated list of qualified names.

    Returns a sorted list of values based upon the quality rules specified
    in https://tools.ietf.org/html/rfc7231 for the Accept-* headers.

    :param value: The value to parse into a list

    """
    accepted: list[_QualifiedItem[str]] = []
    wildcards: list[str] = []
    rejected_values: list[str] = []
    for index, raw_str in enumerate(parse_list(value)):
        if not raw_str.strip():
            continue
        charset, _, parameter_str = raw_str.partition(';')
        charset = charset.strip()
        params = dict(
            _parse_parameter_list(
                parameter_str,
                normalize_parameter_names=True,
            )
        )
        item = _QualifiedItem(charset, params.get('q'), index)
        if charset == '*':
            if item.is_rejected:
                rejected_values.append(charset)
            else:
                wildcards.append(charset)
        elif item.is_rejected:
            rejected_values.append(charset)
        else:
            accepted.append(item)

    explicit_max = [item.value for item in accepted if item.is_explicit_max]
    remaining = sorted(
        (item for item in accepted if not item.is_explicit_max),
        key=operator.attrgetter('quality'),
        reverse=True,
    )
    parsed = explicit_max
    parsed.extend(item.value for item in remaining)
    parsed.extend(wildcards)
    parsed.extend(rejected_values)
    return parsed


def _dequote(value: str) -> str:
    """Remove from value if the entire string is quoted.

    :param value: value to dequote

    :return: a new :class:`str` with leading and trailing quotes
        removed or `value` if not fully quoted

    >>> _dequote('"value"')
    'value'
    >>> _dequote('not="quoted"')
    'not="quoted"'

    >>> _dequote('" with spaces "')
    ' with spaces '

    """
    if value[:1] == '"' and value[-1:] == '"':
        return value[1:-1]
    return value
