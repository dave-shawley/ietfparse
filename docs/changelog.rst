Changelog
---------

.. py:currentmodule:: ietfparse

* Next Release

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

.. _1.1.0: https://github.com/dave-shawley/ietfparse/compare/1.0.0...1.1.0
.. _1.1.1: https://github.com/dave-shawley/ietfparse/compare/1.1.0...1.1.1
.. _1.2.0: https://github.com/dave-shawley/ietfparse/compare/1.1.1...1.2.0
.. _1.2.1: https://github.com/dave-shawley/ietfparse/compare/1.2.0...1.2.1
