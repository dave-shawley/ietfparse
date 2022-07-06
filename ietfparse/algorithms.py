"""
Implementations of algorithms from various specifications.

- :func:`.remove_url_auth`: removes and returns the auth portion
  of a URL.  This is particularly handy for processing URLs from
  configuration files or environment variables.
- :func:`.rewrite_url`: modify a portion of a URL.
- :func:`.select_content_type`: select the best match between a
  HTTP ``Accept`` header and a list of available ``Content-Type`` s

This module implements some of the more interesting algorithms
described in IETF RFCs.

.. data:: IDNA_SCHEMES

   A collection of schemes that use IDN encoding for its host.

"""
from __future__ import annotations

import typing
import warnings
from operator import attrgetter
from urllib import parse
from typing import Dict, List, Sequence, Tuple

from ietfparse import datastructures, errors

IDNA_SCHEMES = ['http', 'https', 'ftp', 'afp', 'sftp', 'smb']

# these are in addition to the "always safe" set
_rfc3986_unreserved = b'~'
_rfc3986_sub_delims = b"!$&'()*+,;="

# see RFC-3986, section 3.2.1
USERINFO_SAFE_CHARS = _rfc3986_sub_delims + _rfc3986_unreserved + b':'

# see RFC-3986, section 3.2.2
HOST_SAFE_CHARS = _rfc3986_sub_delims + _rfc3986_unreserved

# see RFC-3986, section 3.3
PATH_SAFE_CHARS = _rfc3986_sub_delims + _rfc3986_unreserved + b':/@'

# see RFC-3986, section 3.5
FRAGMENT_SAFE_CHARS = b'?/'


class RemoveUrlAuthResult:
    def __init__(self, auth: Tuple[str | None, str | None], url: str) -> None:
        self.auth = auth
        self.url = url

    @property
    def username(self) -> str | None:
        return self.auth[0]

    @property
    def password(self) -> str | None:
        return self.auth[1]

    # len(result) is a holdover from when this class was
    # a namedtuple, please do not depend on this
    def __len__(self) -> int:  # pragma: no cover
        warnings.warn('deprecated without replacement', DeprecationWarning)
        return 2

    def __getitem__(self, index: int) -> str | Tuple[str | None, str | None]:
        # included to make return value destructuring work
        if index == 0:
            return self.auth
        elif index == 1:
            return self.url
        raise IndexError()


def _content_type_matches(candidate: datastructures.ContentType,
                          pattern: datastructures.ContentType) -> bool:
    """Is ``candidate`` an exact match or sub-type of ``pattern``?"""
    def _wildcard_compare(type_spec: str, type_pattern: str) -> bool:
        return type_pattern == '*' or type_spec == type_pattern

    return (_wildcard_compare(candidate.content_type, pattern.content_type)
            and _wildcard_compare(candidate.content_subtype,
                                  pattern.content_subtype))


def select_content_type(
    requested: Sequence[datastructures.ContentType],
    available: Sequence[datastructures.ContentType]
) -> Tuple[datastructures.ContentType, datastructures.ContentType]:
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


unspecified_str = '...'


def rewrite_url(input_url: str,
                *,
                scheme: str | None = unspecified_str,
                user: str | None = unspecified_str,
                password: str | None = unspecified_str,
                host: str | None = unspecified_str,
                port: int | str | None = unspecified_str,
                path: str | None = unspecified_str,
                query: str | dict[str, str] = unspecified_str,
                fragment: str | None = unspecified_str,
                enable_long_host: bool = False,
                encode_with_idna: bool | None = None) -> str:
    """
    Create a new URL from `input_url` with modifications applied.

    :param input_url: the URL to modify

    :param fragment: if specified, this keyword sets the
        fragment portion of the URL.  A value of :data:`None`
        will remove the fragment portion of the URL.
    :param host: if specified, this keyword sets the host
        portion of the network location.  A value of :data:`None`
        will remove the network location portion of the URL.
    :param password: if specified, this keyword sets the
        password portion of the URL.  A value of :data:`None` will
        remove the password from the URL.
    :param path: if specified, this keyword sets the path
        portion of the URL.  A value of :data:`None` will remove
        the path from the URL.
    :param port: if specified, this keyword sets the port
        portion of the network location.  A value of :data:`None`
        will remove the port from the URL.
    :param query: if specified, this keyword sets the query portion
        of the URL.  See the comments for a description of this
        parameter.
    :param scheme: if specified, this keyword sets the scheme
        portion of the URL.  A value of :data:`None` will remove
        the scheme.  Note that this will make the URL relative and
        may have unintended consequences.
    :param user: if specified, this keyword sets the user
        portion of the URL.  A value of :data:`None` will remove
        the user and password portions.

    :param enable_long_host: if this keyword is specified
        and it is :data:`True`, then the host name length restriction
        from :rfc:`3986#section-3.2.2` is relaxed.
    :param encode_with_idna: if this keyword is specified
        and it is :data:`True`, then the ``host`` parameter will be
        encoded using IDN.  If this value is provided as :data:`False`,
        then the percent-encoding scheme is used instead.  If this
        parameter is omitted or included with a different value, then
        the ``host`` parameter is processed using :data:`IDNA_SCHEMES`.

    :return: the modified URL
    :raises ValueError: when a keyword parameter is given an invalid value

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
    result = parse.urlparse(input_url)

    if scheme is unspecified_str:
        scheme = result.scheme

    if user is unspecified_str:
        user = result.username
        if user is not None:
            user = parse.unquote_to_bytes(user).decode('utf-8')

    if password is unspecified_str:
        password = result.password
        if password is not None:
            password = parse.unquote_to_bytes(password).decode('utf-8')

    ident = _create_url_identifier(user, password)

    if host is unspecified_str:
        host = result.hostname
    elif host is not None:
        host = _normalize_host(
            host,
            enable_long_host=enable_long_host,
            encode_with_idna=encode_with_idna,
            scheme=scheme,
        )

    if port is unspecified_str:
        port = result.port
    elif port is not None:
        port = int(port)
        if port < 0:
            raise ValueError('port is requried to be non-negative')

    if host is None or host == '':
        host_n_port = None
    elif port is None:
        host_n_port = host
    else:
        host_n_port = f'{host}:{port}'

    if path is unspecified_str:
        path = result.path
    elif path is None:
        path = '/'
    else:
        path = parse.quote(path.encode('utf-8'), safe=PATH_SAFE_CHARS)

    netloc = f'{ident}@{host_n_port}' if ident else host_n_port

    if query is unspecified_str:
        query = result.query
    elif query is not None:
        PairList = List[Tuple[str, str]]
        params: PairList = []
        try:
            query = typing.cast(Dict[str, str], query)
            for param in sorted(query.keys()):
                params.append((param, query[param]))
        except AttributeError:  # arg is not a dict
            try:  # does it look like a list of tuples?
                params = [(param, value)
                          for param, value in typing.cast(PairList, query)]
            except ValueError:  # guess not...
                pass

        if params:
            query = parse.urlencode(params)

    if fragment is unspecified_str:
        fragment = result.fragment
    elif fragment is not None:
        fragment = parse.quote(fragment.encode('utf-8'),
                               safe=FRAGMENT_SAFE_CHARS)

    # The following is necessary to get around some interesting special
    # case code in urllib.parse._coerce_args in Python 3.4.  Setting
    # scheme to None causes urlunsplit to assume that all non-``None``
    # parameters with be byte strings....
    if scheme is None:
        scheme = ''

    # for some reason mypy is convinced that parse.urlunparse() returns
    # a collection of strings...
    return parse.urlunparse(
        (scheme, netloc, path, result.params, query, fragment))  # type: ignore


def remove_url_auth(url: str) -> RemoveUrlAuthResult:
    """
    Removes the user & password and returns them along with a new url.

    :param str url: the URL to sanitize
    :return: a :class:`tuple` containing the authorization portion and
        the sanitized URL.  The authorization is a simple user & password
        :class:`tuple`.

    >>> auth, sanitized = remove_url_auth('http://foo:bar@example.com')
    >>> auth
    ('foo', 'bar')
    >>> sanitized
    'http://example.com'

    The return value from this function is simple named tuple with the
    following fields:

    - *auth* the username and password as a tuple
    - *username* the username portion of the URL or :data:`None`
    - *password* the password portion of the URL or :data:`None`
    - *url* the sanitized URL

    >>> result = remove_url_auth('http://me:secret@example.com')
    >>> result.username
    'me'
    >>> result.password
    'secret'
    >>> result.url
    'http://example.com'

    """
    parts = parse.urlparse(url)
    return RemoveUrlAuthResult(auth=(parts.username or None, parts.password),
                               url=rewrite_url(url, user=None, password=None))


def _create_url_identifier(user: str | None,
                           password: str | None) -> str | None:
    """
    Generate the user+password portion of a URL.

    :param user: the user name or :data:`None`
    :param password: the password or :data:`None`

    """
    if user is not None:
        user = parse.quote(user.encode('utf-8'), safe=USERINFO_SAFE_CHARS)
        if password:
            password = parse.quote(password.encode('utf-8'),
                                   safe=USERINFO_SAFE_CHARS)
            return f'{user}:{password}'
        return user
    return None


def _normalize_host(host: str,
                    enable_long_host: bool = False,
                    encode_with_idna: bool | None = None,
                    scheme: str | None = None) -> str:
    """
    Normalize a host for a URL.

    :param str host: the host name to normalize

    :keyword bool enable_long_host: if this keyword is specified
        and it is :data:`True`, then the host name length restriction
        from :rfc:`3986#section-3.2.2` is relaxed.
    :keyword bool encode_with_idna: if this keyword is specified
        and it is :data:`True`, then the ``host`` parameter will be
        encoded using IDN.  If this value is provided as :data:`False`,
        then the percent-encoding scheme is used instead.  If this
        parameter is omitted or included with a different value, then
        the ``host`` parameter is processed using :data:`IDNA_SCHEMES`.
    :keyword str scheme: if this keyword is specified, then it is
        used to determine whether to apply IDN rules or not.  This
        parameter is ignored if `encode_with_idna` is not :data:`None`.

    :return: the normalized and encoded string ready for inclusion
        into a URL

    """
    if encode_with_idna is not None:
        enable_idna = encode_with_idna
    else:
        enable_idna = scheme.lower() in IDNA_SCHEMES if scheme else False
    if enable_idna:
        try:
            host = '.'.join(
                segment.encode('idna').decode() for segment in host.split('.'))
        except UnicodeError as exc:
            raise ValueError('host is invalid - {0}'.format(exc))
    else:
        host = parse.quote(host.encode('utf-8'), safe=HOST_SAFE_CHARS)

    if len(host) > 255 and not enable_long_host:
        raise ValueError('host too long')

    return host
