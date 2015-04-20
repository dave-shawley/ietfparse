Changelog
---------

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
