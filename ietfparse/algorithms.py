"""
Implementations of algorithms from various specifications.

- :func:`.rewrite_url`: modify a portion of a URL.
- :func:`.select_content_type`: select the best match between a
  HTTP ``Accept`` header and a list of available ``Content-Type`` s

This module implements some of the more interesting algorithms
described in IETF RFCs.

.. data:: IDNA_SCHEMES

   A collection of schemes that use IDN encoding for its host.

"""
from __future__ import unicode_literals
from operator import attrgetter

from . compat import parse
from . import errors


IDNA_SCHEMES = [
    'http', 'https', 'ftp', 'afp', 'sftp', 'smb']


def _content_type_matches(candidate, pattern):
    """Is ``candidate`` an exact match or sub-type of ``pattern``?"""
    def _wildcard_compare(type_spec, type_pattern):
        return type_pattern == '*' or type_spec == type_pattern

    return (
        _wildcard_compare(candidate.content_type, pattern.content_type) and
        _wildcard_compare(candidate.content_subtype, pattern.content_subtype)
    )


def select_content_type(requested, available):
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

    .. _Accept: http://tools.ietf.org/html/rfc7231#section-5.3.2
    .. _Content-Type: http://tools.ietf.org/html/rfc7231#section-3.1.1.5

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

        def __init__(self, candidate, pattern):
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

    matches = []
    for pattern in sorted(requested, key=attrgetter('quality'), reverse=True):
        for candidate in sorted(available):
            if _content_type_matches(candidate, pattern):
                if candidate == pattern:  # exact match!!!
                    if pattern.quality == 0.0:
                        raise errors.NoMatch  # quality of 0 means NO
                    return candidate, pattern
                matches.append(Match(candidate, pattern))

    if not matches:
        raise errors.NoMatch

    matches = sorted(matches,
                     key=attrgetter('match_type', 'parameter_distance'))
    return matches[0].candidate, matches[0].pattern


def rewrite_url(input_url, **kwargs):
    """
    Create a new URL from `input_url` with modifications applied.

    :param str input_url: the URL to modify
    :keyword str host: if specified, this keyword sets the host
        portion of the network location.  A value of :data:`None`
        will remove the network location portion of the URL.
    :keyword str path: if specified, this keyword sets the path
        portion of the URL.  A value of :data:`None` will remove
        the path from the URL.
    :keyword int port: if specified, this keyword sets the port
        portion of the network location.  A value of :data:`None`
        will remove the port from the URL.
    :keyword query: if specified, this keyword sets the query portion
        of the URL.  See the comments for a description of this
        parameter.
    :keyword str user: if specified, this keyword sets the user
        portion of the URL.  A value of :data:`None` will remove
        the user and password portions.
    :keyword str password: if specified, this keyword sets the
        password portion of the URL.  A value of :data:`None` will
        remove the password from the URL.

    :keyword bool enable_long_host: if this keyword is specified
        and it is :data:`True`, then the host name length restriction
        from :rfc:`3986#section-3.2.2` is relaxed.

    :return: the modified URL
    :raises ValueError: when a keyword parameter is given an invalid
        value

    If the `host` parameter is specified and not :data:`None`, then
    it will be processed as an Internationalized Domain Name (IDN)
    if the scheme appears in :data:`IDNA_SCHEMES`.  Otherwise, it
    will be encoded as UTF-8 and percent encoded.

    The handling of the `query` parameter requires some additional
    explanation.  You can specify a query value in three different
    ways - as a *mapping*, as a *sequence* of pairs, or as a *string*.
    This flexibility makes it possible to meet the wide range of
    finicky use cases.

    *If the query parameter is a mapping*, then the key + value pairs
    are *sorted by the key* before they are encoded.  Use this method
    whenever possible.

    *If the query parameter is a sequence of pairs*, then each pair
    is encoded *in the given order*.  Use this method if you require
    that parameter order is controlled.

    *If the query parameter is a string*, then it is *used as-is*.
    This form SHOULD BE AVOIDED since it can easily result in broken
    URLs since *no URL escaping is performed*.  This is the obvious
    pass through case that is almost always present.

    """
    scheme, netloc, path, query, fragment = parse.urlsplit(input_url)
    ident, host_n_port = parse.splituser(netloc)

    user, password = parse.splitpasswd(ident) if ident else (None, None)
    if 'user' in kwargs:
        user = kwargs['user']
    elif user is not None:
        user = parse.unquote_to_bytes(user).decode('utf-8')
    if 'password' in kwargs:
        password = kwargs['password']
    elif password is not None:
        password = parse.unquote_to_bytes(password).decode('utf-8')

    ident = None
    if user is not None:
        user = parse.quote(user.encode('utf-8'))
        if password:
            password = parse.quote(password.encode('utf-8'))
        ident = '{0}:{1}'.format(user, password) if password else user

    host, port = parse.splitnport(host_n_port, defport=None)
    if 'host' in kwargs:
        host = kwargs['host']
        if host is not None:
            enable_long_host = kwargs.get('enable_long_host', False)
            if scheme.lower() in IDNA_SCHEMES:
                try:
                    host = '.'.join(segment.encode('idna').decode()
                                    for segment in host.split('.'))
                except UnicodeError as exc:
                    raise ValueError('host is invalid - {0}'.format(exc))
            else:
                host = parse.quote(host.encode('utf-8'))
            if len(host) > 255 and not enable_long_host:
                raise ValueError('host too long')

    if 'port' in kwargs:
        port = kwargs['port']
        if port is not None:
            port = int(kwargs['port'])
            if port < 0:
                raise ValueError('port is required to be non-negative')

    if host is None or host == '':
        host_n_port = None
    elif port is None:
        host_n_port = host
    else:
        host_n_port = '{0}:{1}'.format(host, port)

    if 'path' in kwargs:
        path = kwargs['path']
        if path is None:
            path = '/'
        else:
            path = parse.quote(path.encode('utf-8'))

    netloc = '{0}@{1}'.format(ident, host_n_port) if ident else host_n_port

    if 'query' in kwargs:
        new_query = kwargs['query']
        if new_query is None:
            query = None
        else:
            params = []
            try:
                for param in sorted(new_query.keys()):
                    params.append((param, new_query[param]))
            except AttributeError:  # arg is None or not a dict
                pass

            if not params:  # maybe a sequence of tuples?
                try:
                    params = [(param, value) for param, value in new_query]
                except ValueError:  # guess not...
                    pass

            if params:
                query = parse.urlencode(params)
            else:
                query = new_query

    return parse.urlunsplit((scheme, netloc, path, query, fragment))
