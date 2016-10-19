Changelog
---------

.. py:currentmodule:: ietfparse

* `1.4.0`_ (18-Oct-2016)

  - Fixed parsing of lists like ``max-age=5, x-foo="prune"``.  The previous
    versions incorrectly produced ``['max-age=5', 'x-foo="prune']``.
  - Added :func:`headers.parse_accept_encoding` which parses HTTP `Accept-Encoding`_
    header values into a list.
  - Added :func:`headers.parse_accept_language` which parses HTTP `Accept-Language`_
    header values into a list.

* `1.3.0`_ (11-Aug-2016)

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


* `1.2.2`_ (27-May-2015)

  - Added :func:`headers.parse_list_header` which parses generic comma-
    separated list headers with support for quoted parts.
  - Added :func:`headers.parse_accept_charset` which parses an HTTP
    `Accept-Charset`_ header into a sorted list.

* `1.2.1`_ (25-May-2015)

  - :func:`algorithms.select_content_type` claims to work with
    :class:`datastructures.ContentType`` values but it was requiring
    the augmented ones returned from  :func:`algorithms.parse_http_accept_header`.
    IOW, the algorithm required that the quality attribute exist.
    :rfc:`7231#section-5.3.1` states that missing quality values are
    treated as 1.0.

* `1.2.0`_ (19-Apr-2015)

  - Added support for :rfc:`5988` ``Link`` headers.  This consists
    of :func:`headers.parse_link_header` and :class:`datastructures.LinkHeader`

* `1.1.1`_ (10-Feb-2015)

  - Removed ``setupext`` module since it was causing problems with
    source distributions.

* `1.1.0`_ (26-Oct-2014)

  - Added :func:`algorithms.rewrite_url`

* 1.0.0 (21-Sep-2014)

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

.. _1.1.0: https://github.com/dave-shawley/ietfparse/compare/1.0.0...1.1.0
.. _1.1.1: https://github.com/dave-shawley/ietfparse/compare/1.1.0...1.1.1
.. _1.2.0: https://github.com/dave-shawley/ietfparse/compare/1.1.1...1.2.0
.. _1.2.1: https://github.com/dave-shawley/ietfparse/compare/1.2.0...1.2.1
.. _1.2.2: https://github.com/dave-shawley/ietfparse/compare/1.2.1...1.2.2
.. _1.3.0: https://github.com/dave-shawley/ietfparse/compare/1.2.2...1.3.0
.. _1.4.0: https://github.com/dave-shawley/ietfparse/compare/1.3.0...1.4.0
