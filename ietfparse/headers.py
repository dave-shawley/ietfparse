"""
Functions for parsing headers.

- :func:`.parse_content_type`: parse a ``Content-Type`` value
- :func:`.parse_http_accept_header`: parse an ``Accept`` style header

This module also defines classes that might be of some use outside
of the module.  They are not designed for direct usage unless otherwise
mentioned.

"""
import functools
import re

from . import datastructures, errors


_COMMENT_RE = re.compile(r'\(.*\)')


def _remove_comments(value):
    """:rtype: str"""  # makes PyCharm happy
    return _COMMENT_RE.sub('', value)


def parse_parameter_list(parameter_list, normalized_parameter_values=True):
    """
    Parse a named parameter list in the "common" format.

    :param parameter_list:
    :param bool normalized_parameter_values:
    :return: a sequence containing the name to value pairs

    """
    parameters = []
    for param in parameter_list:
        name, value = param.strip().split('=')
        if normalized_parameter_values:
            value = value.lower()
        parameters.append((name, value.strip('"').strip()))
    return parameters


def parse_content_type(content_type, normalize_parameter_values=True):
    """Parse a content type like header.

    :param str content_type: the string to parse as a content type
    :param bool normalize_parameter_values:
        setting this to ``False`` will enable strict RFC2045 compliance
        in which content parameter values are case preserving.
    :return: a :class:`~ietfparse.datastructures.ContentType` instance

    """
    parts = _remove_comments(content_type).split(';')
    content_type, content_subtype = parts.pop(0).split('/')
    parameters = parse_parameter_list(parts, normalize_parameter_values)

    return datastructures.ContentType(content_type, content_subtype,
                                      dict(parameters))


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

    .. _Accept: http://tools.ietf.org/html/rfc7231#section-5.3.2

    """
    headers = [parse_content_type(header)
               for header in header_value.split(',')]
    for header in headers:
        header.quality = float(header.parameters.pop('q', 1.0))

    def ordering(left, right):
        if left.quality != right.quality:
            return right.quality - left.quality
        if left == right:
            return 0
        if left > right:
            return -1
        return 1

    return sorted(headers, key=functools.cmp_to_key(ordering))


def parse_link_header(header_value):
    """
    Parse a HTTP Link header.

    :param str header_value: the header value to parse
    :return: a sequence of :class:`~ietfparse.datastructures.LinkHeader`
        instances
    :raises ietfparse.errors.MalformedLinkValue:
        if the specified `header_value` cannot be parsed

    """
    sanitized = _remove_comments(header_value)
    links = []

    def parse_links(buf):
        # Find quoted parts, these are allowed to contain commas
        # however, it is much easier to parse if they do not so
        # replace them with \000.  Since the NUL byte is not allowed
        # to be there, we can replace it with a comma later on.
        quoted = re.findall('"([^"]*)"', buf)
        for segment in quoted:
            left, match, right = buf.partition(segment)
            buf = ''.join([left, match.replace(',', '\000'), right])

        while buf:
            matched = re.match('<(?P<link>[^>]*)>\s*(?P<params>.*)', buf)
            if matched:
                groups = matched.groupdict()
                params, _, buf = groups['params'].partition(',')
                params = params.replace('\000', ',')  # undo comma hackery
                if params and not params.startswith(';'):
                    raise errors.MalformedLinkValue(
                        'Param list missing opening semicolon ')
                yield (groups['link'].strip(),
                       [p.strip() for p in params[1:].split(';') if p])
                buf = buf.strip()
            else:
                raise errors.MalformedLinkValue('Malformed link header', buf)

    for target, param_list in parse_links(sanitized):
        # a few validations from RFC5988
        # - sec. 5.3:
        #   - the first "rel" is used when multiple are present
        # - sec. 5.4:
        #   - there MUST NOT be more than one media parameter
        #   - the first "title" is used when multiple are present
        #   - if both title and title* are present, then processors
        #     SHOULD use the title* parameter
        #   - there MUST NOT be more than one type parameter
        parsed_params = []
        title_value, title_star_value = None, None
        found_rel, found_media, found_type = False, False, False
        for name, value in parse_parameter_list(param_list):
            if name == 'rel':
                if found_rel:
                    continue
                found_rel = True
            if name == 'media':
                if found_media:
                    raise errors.MalformedLinkValue(
                        'More than one media parameter present')
                found_media = True
            if name == 'type':
                if found_type:
                    raise errors.MalformedLinkValue(
                        'More than one type parameter present')
                found_type = True
            if name == 'title':
                if title_value is None:
                    title_value = value
                continue
            if name == 'title*':
                if title_star_value is None:
                    title_star_value = value
                continue
            parsed_params.append((name, value))

        if title_star_value is not None:
            parsed_params.append(('title*', title_star_value))
            if title_value is not None:
                parsed_params.append(('title', title_star_value))
        elif title_value is not None:
            parsed_params.append(('title', title_value))

        links.append(datastructures.LinkHeader(target=target,
                                               parameters=parsed_params))
    return links
