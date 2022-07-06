Relevant RFCs
=============

`RFC-2045`_
-----------
- :class:`ietfparse.datastructures.ContentType` is an abstraction of
  the :mailheader:`Content-Type` header described in :rfc:`2045` and
  fully specified in section `5.1`_.

`RFC-5988`_
-----------
- :func:`ietfparse.headers.parse_link_header` parses a :mailheader:`Link`
  HTTP header.
- :func:`ietfparse.datastructures.LinkHeader` represents a :mailheader:`Link`
  HTTP header.

`RFC-6839`_
-----------
- :func:`ietf.headers.parse_content_type` and
  :class:`ietfparse.datastructures.ContentType` both support content suffixes.

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

`RFC-7239`_
-----------
- :func:`ietfparse.headers.parse_forwarded` parses a :http:header:`Forwarded`
  HTTP header.


.. _RFC-2045: https://tools.ietf.org/html/rfc2045
.. _5.1: https://tools.ietf.org/html/rfc2045#section-5.1

.. _RFC-5988: https://tools.ietf.org/html/rfc5988

.. _RFC-7231: https://tools.ietf.org/html/rfc7231
.. _3.4.1: https://tools.ietf.org/html/rfc7231#section-3.4.1
.. _5.3: https://tools.ietf.org/html/rfc7231#section-5.3
.. _5.3.2: https://tools.ietf.org/html/rfc7231#section-5.3.2
.. _5.3.3: https://tools.ietf.org/html/rfc7231#section-5.3.3

.. _RFC-2739: https://tools.ietf.org/html/rfc7239
