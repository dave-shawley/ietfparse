Changelog
=========

.. py:currentmodule:: ietfparse

`1.6.1`_ (26-Jan-2020)
----------------------
- Fixed project URL metadata.
- Updated links to refer to canonical URLs.

`1.6.0`_ (25-Jan-2020)
----------------------
- Switched from travis-ci to circle-ci.
- Add type stubs.
- Allow "bad whitespace" around ``=`` in link header parameter lists as
  indicated in :rfc:`8288#section-3`.
- Replaced *nosetests* usage with the :mod:`unittest` module.

`1.5.1`_ (04-Mar-2018)
----------------------
- Add :rfc:`6839` content suffix support to :class:`datastructures.ContentType`
  and :func:`headers.parse_content_type`

`1.5.0`_ (24-Dec-2017)
----------------------
- Officially drop support for Python 2.6 and 3.3.
- Change :func:`headers.parse_accept` to also prefer explicit highest
  quality preferences over inferred highest quality preferences.
- Rename the ``normalized_parameter_values`` keyword of
  :func:`headers._parse_parameter_list`.  The current spelling is retained
  with a deprecation warning.  This will be removed in 2.0.
- Add ``normalize_parameter_names`` keyword to the
  :func:`headers._parse_parameter_list` internal function.
- Add support for parsing :rfc:`7239` ``Forwarded`` headers with
  :func:`headers.parse_forwarded`.
- Add :func:`algorithms.remove_url_auth`

`1.4.3`_ (30-Oct-2017)
----------------------
- Change parsing of qualified lists to retain the initial ordering whenever
  possible.  The algorithm prefers explicit highest quality (1.0) preferences
  over inferred highest quality preferences.  It also retains the initial
  ordering in the presence of multiple highest quality matches.  This affects
  :func:`headers.parse_accept_charset`, :func:`headers.parse_accept_encoding`,
  and :func:`headers.parse_accept_language`.

`1.4.2`_ (04-Jul-2017)
----------------------
- Add formatting of HTTP `Link`_ header using ``str(header)``.

`1.4.1`_ (03-Apr-2017)
----------------------
- Add some documentation about exceptions raised during header parsing.

`1.4.0`_ (18-Oct-2016)
----------------------
- Fixed parsing of lists like ``max-age=5, x-foo="prune"``.  The previous
  versions incorrectly produced ``['max-age=5', 'x-foo="prune']``.
- Added :func:`headers.parse_accept_encoding` which parses HTTP `Accept-Encoding`_
  header values into a list.
- Added :func:`headers.parse_accept_language` which parses HTTP `Accept-Language`_
  header values into a list.

`1.3.0`_ (11-Aug-2016)
----------------------
- Added :func:`headers.parse_cache_control` which parses HTTP `Cache-Control`_
  header values into a dictionary.
- Renamed :func:`headers.parse_http_accept_header` to :func:`headers.parse_accept`,
  adding a wrapper function that raises a deprecation function when invoking
  :func:`headers.parse_http_accept_header`.
- Renamed :func:`headers.parse_link_header` to :func:`headers.parse_link`,
  adding a wrapper function that raises a deprecation function when invoking
  :func:`headers.parse_link_header`.
- Renamed :func:`headers.parse_list_header` to :func:`headers.parse_list`,
  adding a wrapper function that raises a deprecation function when invoking
  :func:`headers.parse_list_header`.


`1.2.2`_ (27-May-2015)
----------------------
- Added :func:`headers.parse_list_header` which parses generic comma-
  separated list headers with support for quoted parts.
- Added :func:`headers.parse_accept_charset` which parses an HTTP
  `Accept-Charset`_ header into a sorted list.

`1.2.1`_ (25-May-2015)
----------------------
- :func:`algorithms.select_content_type` claims to work with
  :class:`datastructures.ContentType`` values but it was requiring
  the augmented ones returned from  :func:`algorithms.parse_http_accept_header`.
  IOW, the algorithm required that the quality attribute exist.
  :rfc:`7231#section-5.3.1` states that missing quality values are
  treated as 1.0.

`1.2.0`_ (19-Apr-2015)
----------------------
- Added support for :rfc:`5988` ``Link`` headers.  This consists
  of :func:`headers.parse_link_header` and :class:`datastructures.LinkHeader`

`1.1.1`_ (10-Feb-2015)
----------------------
- Removed ``setupext`` module since it was causing problems with
  source distributions.

`1.1.0`_ (26-Oct-2014)
----------------------
- Added :func:`algorithms.rewrite_url`

1.0.0 (21-Sep-2014)
-------------------
- Initial implementation containing the following functionality:
  - :func:`algorithms.select_content_type`
  - :class:`datastructures.ContentType`
  - :class:`errors.NoMatch`
  - :class:`errors.RootException`
  - :func:`headers.parse_content_type`
  - :func:`headers.parse_http_accept_header`

.. _Accept-Charset: https://tools.ietf.org/html/rfc7231#section-5.3.3
.. _Accept-Encoding: https://tools.ietf.org/html/rfc7231#section-5.3.4
.. _Accept-Language: https://tools.ietf.org/html/rfc7231#section-5.3.5
.. _Cache-Control: https://tools.ietf.org/html/rfc7231#section-5.2
.. _Link: https://tools.ietf.org/html/rfc5988

.. _1.1.0: https://github.com/dave-shawley/ietfparse/compare/1.0.0...1.1.0
.. _1.1.1: https://github.com/dave-shawley/ietfparse/compare/1.1.0...1.1.1
.. _1.2.0: https://github.com/dave-shawley/ietfparse/compare/1.1.1...1.2.0
.. _1.2.1: https://github.com/dave-shawley/ietfparse/compare/1.2.0...1.2.1
.. _1.2.2: https://github.com/dave-shawley/ietfparse/compare/1.2.1...1.2.2
.. _1.3.0: https://github.com/dave-shawley/ietfparse/compare/1.2.2...1.3.0
.. _1.4.0: https://github.com/dave-shawley/ietfparse/compare/1.3.0...1.4.0
.. _1.4.1: https://github.com/dave-shawley/ietfparse/compare/1.4.0...1.4.1
.. _1.4.2: https://github.com/dave-shawley/ietfparse/compare/1.4.1...1.4.2
.. _1.4.3: https://github.com/dave-shawley/ietfparse/compare/1.4.2...1.4.3
.. _1.5.0: https://github.com/dave-shawley/ietfparse/compare/1.4.3...1.5.0
.. _1.5.1: https://github.com/dave-shawley/ietfparse/compare/1.5.0...1.5.1
.. _1.6.0: https://github.com/dave-shawley/ietfparse/compare/1.5.1...1.6.0
.. _1.6.1: https://github.com/dave-shawley/ietfparse/compare/1.6.0...1.6.1
.. _Next Release: https://github.com/dave-shawley/ietfparse/compare/1.6.1...head
