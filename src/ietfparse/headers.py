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
import decimal
import functools
import re
import typing

from ietfparse import _helpers, datastructures, errors

if typing.TYPE_CHECKING:
    from collections import abc

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
_COMMENT_RE = re.compile(r'\(.*\)')
_QUOTED_SEGMENT_RE = re.compile(r'"([^"]*)"')
_DEF_PARAM_VALUE = object()

# This is *here* instead of constants.py to avoid a ciecular import
_SMALLEST_QUALITY = 0.001


def parse_accept(  # noqa: C901 -- overly complex
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

    next_explicit_q = decimal.ExtendedContext.next_plus(decimal.Decimal('5.0'))
    headers: list[datastructures.ContentType] = []
    for content_type in parse_list(header_value):
        with guard:
            headers.append(parse_content_type(content_type))

    for header in headers:
        q = header.parameters.pop('q', None)
        if q is None:
            header.quality = 1.0
        elif q == '1.0':
            header.quality = float(next_explicit_q)
            next_explicit_q = next_explicit_q.next_minus()
        else:
            header.quality = float(q)

    def ordering(
        left: datastructures.ContentType, right: datastructures.ContentType
    ) -> int:
        assert left.quality is not None  # appease mypy  # noqa: S101
        assert right.quality is not None  # appease mypy  # noqa: S101
        if left.quality == right.quality:
            if left == right:
                return 0
            if left > right:
                return -1
            return 1
        if left.quality > right.quality:
            return -1
        return 1

    return sorted(headers, key=functools.cmp_to_key(ordering))


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
        name, sep, value = segment.partition('=')
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
    parts = _remove_comments(content_type).split(';')
    type_spec = parts.pop(0)
    try:
        content_type, content_subtype = type_spec.split('/')
    except ValueError as error:
        raise errors.MalformedContentType(content_type) from error

    parameters = _parse_parameter_list(
        parts, normalize_parameter_values=normalize_parameter_values
    )
    if '+' in content_subtype:
        content_subtype, content_suffix = content_subtype.split('+')
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
    result = []
    for entry in parse_list(header_value):
        param_tuples = _parse_parameter_list(
            entry.split(';'),
            normalize_parameter_names=True,
            normalize_parameter_values=False,
        )
        if only_standard_parameters:
            for name, _ in param_tuples:
                if name not in ('for', 'proto', 'by', 'host'):
                    raise errors.StrictHeaderParsingFailure(
                        'Forwarded', header_value
                    )
        result.append(dict(param_tuples))
    return result


def parse_link(
    header_value: str, *, strict: bool = True
) -> list[datastructures.LinkHeader]:
    """Parse a HTTP Link header.

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
    sanitized = _remove_comments(header_value)
    links = []

    def parse_links(
        buf: str,
    ) -> abc.Generator[tuple[str, list[str]], None, None]:
        r"""Parse links from `buf`.

        Find quoted parts, these are allowed to contain commas
        however, it is much easier to parse if they do not so
        replace them with \000.  Since the NUL byte is not allowed
        to be there, we can replace it with a comma later on.
        A similar trick is performed on semicolons with \001.
        """
        quoted = re.findall('"([^"]*)"', buf)
        for segment in quoted:
            left, match, right = buf.partition(segment)
            match = match.replace(',', '\000')
            match = match.replace(';', '\001')
            buf = f'{left}{match}{right}'

        while buf:
            matched = re.match(r'<(?P<link>[^>]*)>\s*(?P<params>.*)', buf)
            if matched:
                groups = matched.groupdict()
                params, _, buf = groups['params'].partition(',')
                params = params.replace('\000', ',')  # undo comma hackery
                if params and not params.startswith(';'):
                    raise errors.MalformedLinkValue(
                        'Param list missing opening semicolon'
                    )

                yield (
                    groups['link'].strip(),
                    [
                        p.replace('\001', ';').strip()
                        for p in params[1:].split(';')
                        if p
                    ],
                )
                buf = buf.strip()
            else:
                raise errors.MalformedLinkValue('Malformed link header', buf)

    for target, param_list in parse_links(sanitized):
        parser = _helpers.ParameterParser(strict=strict)
        for name, value in _parse_parameter_list(
            param_list, strip_interior_whitespace=True
        ):
            parser.add_value(name, value)

        links.append(
            datastructures.LinkHeader(target=target, parameters=parser.values)
        )

    return links


def parse_list(value: str) -> list[str]:
    """Parse a comma-separated list header.

    :param value: header value to split into elements
    :return: list of header elements as strings

    """
    segments = _QUOTED_SEGMENT_RE.findall(value)
    for segment in segments:
        left, match, right = value.partition(segment)
        value = ''.join([left, match.replace(',', '\000'), right])
    return [_dequote(x.strip()).replace('\000', ',') for x in value.split(',')]


def _parse_parameter_list(
    parameter_list: abc.Iterable[str],
    *,
    normalize_parameter_names: bool = False,
    normalize_parameter_values: bool = True,
    strip_interior_whitespace: bool = False,
) -> list[tuple[str, str]]:
    """Parse a named parameter list in the "common" format.

    :param parameter_list: sequence of string values to parse
    :keyword normalize_parameter_names: if specified and *truthy*
        then parameter names will be case-folded to lower case
    :keyword normalize_parameter_values: if omitted or specified
        as *truthy*, then parameter values are case-folded to lower case
    :keyword strip_interior_whitespace: remove whitespace between
        name and values surrounding the ``=``
    :return: a sequence containing the name to value pairs

    The parsed values are normalized according to the keyword parameters
    and returned as :class:`tuple` of name to value pairs preserving the
    ordering from `parameter_list`.  The values will have quotes removed
    if they were present.

    """
    parameters = []
    for param in parameter_list:
        param = param.strip()  # noqa: PLW2901 -- overridden for simplicity
        if param:
            name, value = param.split('=')
            if strip_interior_whitespace:
                name, value = name.strip(), value.strip()
            if normalize_parameter_names:
                name = name.lower()
            if normalize_parameter_values:
                value = value.lower()
            parameters.append((name, _dequote(value.strip())))
    return parameters


def _parse_qualified_list(value: str) -> list[str]:
    """Parse `value` as a comma-separated list of qualified names.

    Returns a sorted list of values based upon the quality rules specified
    in https://tools.ietf.org/html/rfc7231 for the Accept-* headers.

    :param value: The value to parse into a list

    """
    found_wildcard = False
    values, rejected_values = [], []
    parsed = parse_list(value)
    default = float(len(parsed) + 1)
    highest = default + 1.0
    for raw_str in parsed:
        charset, _, parameter_str = raw_str.replace(' ', '').partition(';')
        if charset == '*':
            found_wildcard = True
            continue
        params = dict(_parse_parameter_list(parameter_str.split(';')))
        actual_param = params.get('q')
        quality = float(params.pop('q', default))
        if quality < _SMALLEST_QUALITY:
            rejected_values.append(charset)
        elif actual_param == '1.0':
            values.append((highest + default, charset))
        else:
            values.append((quality, charset))
        default -= 1.0
    parsed = [value[1] for value in sorted(values, reverse=True)]
    if found_wildcard:
        parsed.append('*')
    parsed.extend(rejected_values)
    return parsed


def _remove_comments(value: str) -> str:
    return _COMMENT_RE.sub('', value)


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
    if value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value
