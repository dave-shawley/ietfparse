Changelog
---------

* Next Release

  - Added ``headers.parse_list_header`` which parses generic comma-
    separated list headers with support for quoted parts.
  - Added ``headers.parse_accept_charset`` which parses an HTTP
    ``Accept-Charset`` header into a sorted list.

* 1.2.1 (25-May-2015)

  - ``select_content_type`` claims to work with ``ContentType``
    values but it was requiring the augmented ones returned from
    ``parse_http_accept_header``.  IOW, the algorithm required
    that the quality attribute exist.  RFC7231 states that missing
    quality values are treated as 1.0.


* 1.2.0 (19-Apr-2015)

  - Added support for :rfc:`5988` ``Link`` headers.  This consists
    of ``headers.parse_link_header`` and ``datastructures.LinkHeader``

* 1.1.1 (10-Feb-2015)

  - Removed ``setupext`` module since it was causing problems with
    source distributions.

* 1.1.0 (26-Oct-2014)

  - Added ``algorithms.rewrite_url``

* 1.0.0 (21-Sep-2014)

  - Initial implementation containing the following functionality:
      - ``algorithms.select_content_type``
      - ``datastructures.ContentType``
      - ``errors.NoMatch``
      - ``errors.RootException``
      - ``headers.parse_content_type``
      - ``headers.parse_http_accept_header``
