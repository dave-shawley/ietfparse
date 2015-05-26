Relevant RFCs
=============

`RFC-2045`_
-----------
- :class:`ietfparse.datastructures.ContentType` is an abstraction of
  the :mailheader:`Content-Type` header described in :rfc:`2045` and
  fully specified in section `5.1`_.

`RFC-3986`_
-----------
- :func:`ietfparse.algorithms.rewrite_url` implements encoding and
  parsing per :rfc:`3986`.

`RFC-5980`_
-----------
- :func:`ietfparse.algorithms.rewrite_url` encodes hostnames according
  to :rfc:`5980` for the schemes identified by
  :data:`~ietfparse.algorithms.IDNA_SCHEMES`.  Encoding can also be
  forced using the ``encode_with_idna`` keyword parameter.

`RFC-5988`_
-----------
- :func:`ietfparse.headers.parse_link_header` parses a :mailheader:`Link`
  HTTP header.
- :func:`ietfparse.datastructures.LinkHeader` represents a :mailheader:`Link`
  HTTP header.

`RFC-7231`_
-----------
- :func:`ietfparse.algorithms.select_content_type` implements proactive
  content negotiation as described in sections `3.4.1`_ and `5.3`_ of
  :rfc:`7231`
- :func:`ietfparse.headers.parse_accept_charset` parses a
  :mailheader:`Accept-Charset` value as described in section `5.3.3`_.
- :func:`ietfparse.headers.parse_http_accept_header` parses a
  :mailheader:`Accept` value as described in section `5.3.2`_.
- :func:`ietfparse.headers.parse_list_header` parses just about any of
  the comma-separated lists from :rfc:`7231`.  It doesn't provide any
  logic other than parsing the header though.
- :func:`ietfparse.headers.parse_parameter_list` parses the ``key=value``
  portions common to many header values.


.. _RFC-2045: https://tools.ietf.org/html/rfc2045
.. _5.1: https://tools.ietf.org/html/rfc2045#section-5.1

.. _RFC-3986: https://tools.ietf.org/html/rfc3986

.. _RFC-5980: https://tools.ietf.org/html/rfc5980

.. _RFC-5988: https://tools.ietf.org/html/rfc5988

.. _RFC-7231: https://tools.ietf.org/html/rfc7231
.. _3.4.1: https://tools.ietf.org/html/rfc7231#section-3.4.1
.. _5.3: https://tools.ietf.org/html/rfc7231#section-5.3
.. _5.3.2: https://tools.ietf.org/html/rfc7231#section-5.3.2
.. _5.3.3: https://tools.ietf.org/html/rfc7231#section-5.3.3
