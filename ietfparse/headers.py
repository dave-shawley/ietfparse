"""
Functions for parsing headers.

- :func:`.parse_accept`: parse an ``Accept`` value
- :func:`.parse_accept_charset`: parse a ``Accept-Charset`` value
- :func:`.parse_cache_control`: parse a ``Cache-Control`` value
- :func:`.parse_content_type`: parse a ``Content-Type`` value
- :func:`.parse_forwarded`: parse a :rfc:`7239` ``Forwarded`` value
- :func:`.parse_link`: parse a :rfc:`5988` ``Link`` value
- :func:`.parse_list`: parse a comma-separated list that is
  present in so many headers

This module also defines classes that might be of some use outside
of the module.  They are not designed for direct usage unless otherwise
mentioned.

"""
import functools
import decimal
import re
import warnings

from . import datastructures, errors, _helpers


_CACHE_CONTROL_BOOL_DIRECTIVES = \
    ('must-revalidate', 'no-cache', 'no-store', 'no-transform',
     'only-if-cached', 'public', 'private', 'proxy-revalidate')
_COMMENT_RE = re.compile(r'\(.*\)')
_QUOTED_SEGMENT_RE = re.compile(r'"([^"]*)"')
_DEF_PARAM_VALUE = object()


def parse_accept(header_value, strict=False):
    """Parse an HTTP accept-like header.

    :param str header_value: the header value to parse
    :param bool strict: if :data:`True`, then invalid content type
        values within `header_value` will raise :exc:`ValueError`;
        otherwise, they are ignored
    :return: a :class:`list` of :class:`.ContentType` instances
        in decreasing quality order.  Each instance is augmented
        with the associated quality as a ``float`` property
        named ``quality``.
    :raise: :exc:`ValueError` if `strict` is *truthy* and at least
        one value in `header_value` could not be parsed by
        :func:`.parse_content_type`

    ``Accept`` is a class of headers that contain a list of values
    and an associated preference value.  The ever present `Accept`_
    header is a perfect example.  It is a list of content types and
    an optional parameter named ``q`` that indicates the relative
    weight of a particular type.  The most basic example is::

        Accept: audio/*;q=0.2, audio/basic

    Which states that I prefer the ``audio/basic`` content type
    but will accept other ``audio`` sub-types with an 80% mark down.

    .. _Accept: https://tools.ietf.org/html/rfc7231#section-5.3.2

    """
    next_explicit_q = decimal.ExtendedContext.next_plus(decimal.Decimal('5.0'))
    headers = []
    for header in parse_list(header_value):
        try:
            headers.append(parse_content_type(header))
        except ValueError:
            if strict:
                raise

    for header in headers:
        q = header.parameters.pop('q', None)
        if q is None:
            q = '1.0'
        elif float(q) == 1.0:
            q = float(next_explicit_q)
            next_explicit_q = next_explicit_q.next_minus()
        header.quality = float(q)

    def ordering(left, right):
        """
        Method for sorting the header values

        :param mixed left:
        :param mixed right:
        :rtype: mixed

        """
        if left.quality != right.quality:
            return right.quality - left.quality
        if left == right:
            return 0
        if left > right:
            return -1
        return 1

    return sorted(headers, key=functools.cmp_to_key(ordering))


def parse_accept_charset(header_value):
    """
    Parse the ``Accept-Charset`` header into a sorted list.

    :param str header_value: header value to parse

    :return: list of character sets sorted from highest to lowest
        priority

    The `Accept-Charset`_ header is a list of character set names with
    optional *quality* values.  The quality value indicates the strength
    of the preference where 1.0 is a strong preference and less than 0.001
    is outright rejection by the client.

    .. note::

       Character sets that are rejected by setting the quality value
       to less than 0.001.  If a wildcard is included in the header,
       then it will appear **BEFORE** values that are rejected.

    .. _Accept-Charset: https://tools.ietf.org/html/rfc7231#section-5.3.3

    """
    return _parse_qualified_list(header_value)


def parse_accept_encoding(header_value):
    """
    Parse the ``Accept-Encoding`` header into a sorted list.

    :param str header_value: header value to parse

    :return: list of encodings sorted from highest to lowest priority

    The `Accept-Encoding`_ header is a list of encodings with
    optional *quality* values.  The quality value indicates the strength
    of the preference where 1.0 is a strong preference and less than 0.001
    is outright rejection by the client.

    .. note::

       Encodings that are rejected by setting the quality value
       to less than 0.001.  If a wildcard is included in the header,
       then it will appear **BEFORE** values that are rejected.

    .. _Accept-Encoding: https://tools.ietf.org/html/rfc7231#section-5.3.4

    """
    return _parse_qualified_list(header_value)


def parse_accept_language(header_value):
    """
    Parse the ``Accept-Language`` header into a sorted list.

    :param str header_value: header value to parse

    :return: list of languages sorted from highest to lowest priority

    The `Accept-Language`_ header is a list of languages with
    optional *quality* values.  The quality value indicates the strength
    of the preference where 1.0 is a strong preference and less than 0.001
    is outright rejection by the client.

    .. note::

       Languages that are rejected by setting the quality value
       to less than 0.001.  If a wildcard is included in the header,
       then it will appear **BEFORE** values that are rejected.

    .. _Accept-Language: https://tools.ietf.org/html/rfc7231#section-5.3.5

    """
    return _parse_qualified_list(header_value)


def parse_cache_control(header_value):
    """
    Parse a `Cache-Control`_ header, returning a dictionary of key-value pairs.

    Any of the ``Cache-Control`` parameters that do not have directives, such
    as ``public`` or ``no-cache`` will be returned with a value of ``True``
    if they are set in the header.

    :param str header_value: ``Cache-Control`` header value to parse
    :return: the parsed ``Cache-Control`` header values
    :rtype: dict

    .. _Cache-Control: https://tools.ietf.org/html/rfc7234#section-5.2

    """
    directives = {}

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


def parse_content_type(content_type, normalize_parameter_values=True):
    """Parse a content type like header.

    :param str content_type: the string to parse as a content type
    :param bool normalize_parameter_values:
        setting this to ``False`` will enable strict RFC2045 compliance
        in which content parameter values are case preserving.
    :return: a :class:`~ietfparse.datastructures.ContentType` instance
    :raises: :exc:`ValueError` if the content type cannot be reasonably
        parsed (e.g., ``Content-Type: *``)

    """
    parts = _remove_comments(content_type).split(';')
    type_spec = parts.pop(0)
    try:
        content_type, content_subtype = type_spec.split('/')
    except ValueError:
        raise ValueError('Failed to parse ' + type_spec)

    if '+' in content_subtype:
        content_subtype, content_suffix = content_subtype.split('+')
    else:
        content_suffix = None
    parameters = _parse_parameter_list(
        parts, normalize_parameter_values=normalize_parameter_values)

    return datastructures.ContentType(content_type, content_subtype,
                                      dict(parameters), content_suffix)


def parse_forwarded(header_value, only_standard_parameters=False):
    """
    Parse RFC7239 Forwarded header.

    :param str header_value: value to parse
    :keyword bool only_standard_parameters: if this keyword is specified
        and given a *truthy* value, then a non-standard parameter name
        will result in :exc:`~ietfparse.errors.StrictHeaderParsingFailure`
    :return: an ordered :class:`list` of :class:`dict` instances
    :raises: :exc:`ietfparse.errors.StrictHeaderParsingFailure` is
        raised if `only_standard_parameters` is enabled and a non-standard
        parameter name is encountered

    This function parses a :rfc:`7239` HTTP header into a :class:`list`
    of :class:`dict` instances with each instance containing the param
    values.  The list is ordered as received from left to right and the
    parameter names are folded to lower case strings.

    """
    result = []
    for entry in parse_list(header_value):
        param_tuples = _parse_parameter_list(entry.split(';'),
                                             normalize_parameter_names=True,
                                             normalize_parameter_values=False)
        if only_standard_parameters:
            for name, _ in param_tuples:
                if name not in ('for', 'proto', 'by', 'host'):
                    raise errors.StrictHeaderParsingFailure(
                        'Forwarded', header_value)
        result.append(dict(param_tuples))
    return result


def parse_link(header_value, strict=True):
    """
    Parse a HTTP Link header.

    :param str header_value: the header value to parse
    :param bool strict: set this to ``False`` to disable semantic
        checking.  Syntactical errors will still raise an exception.
        Use this if you want to receive all parameters.
    :return: a sequence of :class:`~ietfparse.datastructures.LinkHeader`
        instances
    :raises ietfparse.errors.MalformedLinkValue:
        if the specified `header_value` cannot be parsed

    """
    sanitized = _remove_comments(header_value)
    links = []

    def parse_links(buf):
        """
        Find quoted parts, these are allowed to contain commas
        however, it is much easier to parse if they do not so
        replace them with \000.  Since the NUL byte is not allowed
        to be there, we can replace it with a comma later on.
        A similar trick is performed on semicolons with \001.

        :param str buf: The link buffer
        :return:
        """
        quoted = re.findall('"([^"]*)"', buf)
        for segment in quoted:
            left, match, right = buf.partition(segment)
            match = match.replace(',', '\000')
            match = match.replace(';', '\001')
            buf = ''.join([left, match, right])

        while buf:
            matched = re.match(r'<(?P<link>[^>]*)>\s*(?P<params>.*)', buf)
            if matched:
                groups = matched.groupdict()
                params, _, buf = groups['params'].partition(',')
                params = params.replace('\000', ',')  # undo comma hackery
                if params and not params.startswith(';'):
                    raise errors.MalformedLinkValue(
                        'Param list missing opening semicolon ')

                yield (groups['link'].strip(), [
                    p.replace('\001', ';').strip()
                    for p in params[1:].split(';') if p
                ])
                buf = buf.strip()
            else:
                raise errors.MalformedLinkValue('Malformed link header', buf)

    for target, param_list in parse_links(sanitized):
        parser = _helpers.ParameterParser(strict=strict)
        for name, value in _parse_parameter_list(
                param_list, strip_interior_whitespace=True):
            parser.add_value(name, value)

        links.append(
            datastructures.LinkHeader(target=target, parameters=parser.values))
    return links


def parse_list(value):
    """
    Parse a comma-separated list header.

    :param str value: header value to split into elements
    :return: list of header elements as strings

    """
    segments = _QUOTED_SEGMENT_RE.findall(value)
    for segment in segments:
        left, match, right = value.partition(segment)
        value = ''.join([left, match.replace(',', '\000'), right])
    return [_dequote(x.strip()).replace('\000', ',') for x in value.split(',')]


def _parse_parameter_list(parameter_list,
                          normalized_parameter_values=_DEF_PARAM_VALUE,
                          normalize_parameter_names=False,
                          normalize_parameter_values=True,
                          strip_interior_whitespace=False):
    """
    Parse a named parameter list in the "common" format.

    :param parameter_list: sequence of string values to parse
    :keyword bool normalize_parameter_names: if specified and *truthy*
        then parameter names will be case-folded to lower case
    :keyword bool normalize_parameter_values: if omitted or specified
        as *truthy*, then parameter values are case-folded to lower case
    :keyword bool normalized_parameter_values: alternate way to spell
        ``normalize_parameter_values`` -- this one is deprecated
    :keyword bool strip_interior_whitespace: remove whitespace between
        name and values surrounding the ``=``
    :return: a sequence containing the name to value pairs

    The parsed values are normalized according to the keyword parameters
    and returned as :class:`tuple` of name to value pairs preserving the
    ordering from `parameter_list`.  The values will have quotes removed
    if they were present.

    """
    if normalized_parameter_values is not _DEF_PARAM_VALUE:  # pragma: no cover
        warnings.warn(
            'normalized_parameter_values keyword to _parse_parameter_list is'
            ' deprecated, use normalize_parameter_values instead',
            DeprecationWarning)
        normalize_parameter_values = normalized_parameter_values
    parameters = []
    for param in parameter_list:
        param = param.strip()
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


def _parse_qualified_list(value):
    """
    Parse a header value, returning a sorted list of values based upon
    the quality rules specified in https://tools.ietf.org/html/rfc7231 for
    the Accept-* headers.

    :param str value: The value to parse into a list
    :rtype: list

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
        quality = float(params.pop('q', default))
        if quality < 0.001:
            rejected_values.append(charset)
        elif quality == 1.0:
            values.append((highest + default, charset))
        else:
            values.append((quality, charset))
        default -= 1.0
    parsed = [value[1] for value in sorted(values, reverse=True)]
    if found_wildcard:
        parsed.append('*')
    parsed.extend(rejected_values)
    return parsed


def _remove_comments(value):
    """:rtype: str"""  # makes PyCharm happy
    return _COMMENT_RE.sub('', value)


def _dequote(value):
    """
    Remove from value if the entire string is quoted.

    :param str value: value to dequote

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


# Backwards Compatibility Functions


def parse_http_accept_header(header_value):
    """Parse an HTTP accept-like header.

    :param str header_value: the header value to parse
    :return: a :class:`list` of :class:`.ContentType` instances
        in decreasing quality order.  Each instance is augmented
        with the associated quality as a ``float`` property
        named ``quality``.

    ``Accept`` is a class of headers that contain a list of values
    and an associated preference value.  The ever present `Accept`_
    header is a perfect example.  It is a list of content types and
    an optional parameter named ``q`` that indicates the relative
    weight of a particular type.  The most basic example is::

        Accept: audio/*;q=0.2, audio/basic

    Which states that I prefer the ``audio/basic`` content type
    but will accept other ``audio`` sub-types with an 80% mark down.

    .. _Accept: https://tools.ietf.org/html/rfc7231#section-5.3.2

    .. deprecated:: 1.3.0
       Use :func:`~ietfparse.headers.parse_accept` instead.

    """
    warnings.warn("deprecated", DeprecationWarning)
    return parse_accept(header_value)


def parse_link_header(header_value, strict=True):
    """
    Parse a HTTP Link header.

    :param str header_value: the header value to parse
    :param bool strict: set this to ``False`` to disable semantic
        checking.  Syntactical errors will still raise an exception.
        Use this if you want to receive all parameters.
    :return: a sequence of :class:`~ietfparse.datastructures.LinkHeader`
        instances
    :raises ietfparse.errors.MalformedLinkValue:
        if the specified `header_value` cannot be parsed

    .. deprecated:: 1.3.0
       Use :func:`~ietfparse.headers.parse_link` instead.

    """
    warnings.warn("deprecated", DeprecationWarning)
    return parse_link(header_value, strict)


def parse_list_header(value):
    """
    Parse a comma-separated list header.

    :param str value: header value to split into elements
    :return: list of header elements as strings

    .. deprecated:: 1.3.0
       Use :func:`~ietfparse.headers.parse_list` instead.

    """
    warnings.warn("deprecated", DeprecationWarning)
    return parse_list(value)
