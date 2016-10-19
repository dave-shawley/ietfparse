.. py:currentmodule:: ietfparse.headers

Header Parsing
==============

Accept
------
:func:`parse_accept` parses the HTTP :http:header:`Accept` header
into a sorted list of :class:`ietfparse.datastructures.ContentType` instances.
The list is sorted according to the specified quality values. Elements with
the same quality value are ordered with the *most-specific* value first.  The
following is a good example of this from section 5.3.2 of
:rfc:`7231#section-5.3.2`.

>>> from ietfparse import headers
>>> requested = headers.parse_accept(
...     'text/*, text/plain, text/plain;format=flowed, */*')
>>> [str(h) for h in requested]
['text/plain; format=flowed', 'text/plain', 'text/*', '*/*']

All of the requested types have the same quality - implicitly 1.0 so they
are sorted purely by specificity.  Though the result is sorted according
to quality and specificity, selecting a matching content type is not as
easy as traversing the list in order.  The full algorithm for selecting the
most appropriate content type is described in :rfc:`7231` and is fully
implemented by :func:`~ietfparse.algorithms.select_content_type`.

Accept-Charset
--------------
:func:`parse_accept_charset` parses the HTTP :http:header:`Accept-Charset`
header into a sorted sequence of character set identifiers.  Character set
identifiers are simple tokens with an optional quality value that is the
strength of the preference from most preferred (1.0) to rejection (0.0).
After the header is parsed and sorted, the quality values are removed and
the token list is returned.

>>> from ietfparse import headers
>>> charsets = headers.parse_accept_charset('latin1;q=0.5, utf-8;q=1.0, '
...                                         'us-ascii;q=0.1, ebcdic;q=0.0')
['utf-8', 'latin1', 'us-ascii', 'ebcdic']

The wildcard character set if present, will be sorted towards the end of the
list.  If both a wildcard and rejected values are present, then the wildcard
will occur *before* the rejected values.

>>> from ietfparse import headers
>>> headers.parse_accept_charset('acceptable, rejected;q=0, *')
['acceptable', '*', 'rejected']

.. note::

   The only attribute that is allowed to be specified per the RFC is the
   quality value.  If additional parameters are included, they are not
   included in the response from this function.  More specifically, the
   returned list contains only the character set strings.

Accept-Encoding
---------------
:func:`parse_accept_encoding` parses the HTTP :http:header:`Accept-Encoding`
header into a sorted sequence of encodings.  Encodings are simple tokens
with an optional quality value that is the strength of the preference from
most preferred (1.0) to rejection (0.0). After the header is parsed and sorted,
the quality values are removed and the token list is returned.

>>> from ietfparse import headers
>>> headers.parse_accept_encoding('snappy, compress;q=0.7, gzip;q=0.8')
['snappy', 'gzip', 'compress']

The wildcard character set if present, will be sorted towards the end of the
list.  If both a wildcard and rejected values are present, then the wildcard
will occur *before* the rejected values.

>>> from ietfparse import headers
>>> headers.parse_accept_encoding('compress, snappy;q=0, *')
['compress', '*', 'snappy']

.. note::

   The only attribute that is allowed to be specified per the RFC is the
   quality value.  If additional parameters are included, they are not
   included in the response from this function.  More specifically, the
   returned list contains only the character set strings.

Accept-Language
---------------
:func:`parse_accept_language` parses the HTTP :http:header:`Accept-Language`
header into a sorted sequence of languages.  Languages are simple tokens
with an optional quality value that is the strength of the preference from
most preferred (1.0) to rejection (0.0). After the header is parsed and sorted,
the quality values are removed and the token list is returned.

>>> from ietfparse import headers
>>> headers.parse_accept_language('de, en;q=0.7, en-gb;q=0.8')
['de', 'en-gb', 'en']

The wildcard character set if present, will be sorted towards the end of the
list.  If both a wildcard and rejected values are present, then the wildcard
will occur *before* the rejected values.

>>> from ietfparse import headers
>>> headers.parse_accept_language('es-es, en;q=0, *')
['es-es', '*', 'en']

.. note::

   The only attribute that is allowed to be specified per the RFC is the
   quality value.  If additional parameters are included, they are not
   included in the response from this function.  More specifically, the
   returned list contains only the character set strings.

Cache-Control
-------------
:func:`parse_cache_control` parses the HTTP Cache-Control header
as described in :rfc:`7234` into a dictionary of directives.

Directives without a value such as ``public`` or ``no-cache`` will be returned
in the dictionary with a value of ``True`` if set.

>>> from ietfparse import headers
>>> headers.parse_cache_control('public, max-age=2592000')
{'public': True, 'max-age': 2592000}

Content-Type
------------
:func:`parse_content_type` parses a MIME or HTTP :http:header:`Content-Type`
header into an object that exposes the structured data.

>>> from ietfparse import headers
>>> header = headers.parse_content_type('text/html; charset=ISO-8859-4')
>>> header.content_type, header.content_subtype
('text', 'html')
>>> header.parameters['charset']
'ISO-8859-4'

It handles dequoting and normalizing the value.  The content type
and all parameter names are translated to lower-case during the
parsing process.  The relatively unknown option to include comments
in the content type is honored and comments are discarded.

>>> header = headers.parse_content_type(
...     'message/http; version=2.0 (someday); MSGTYPE="request"')
>>> header.parameters['version']
'2.0'
>>> header.parameters['msgtype']
'request'

Notice that the ``(someday)`` comment embedded in the ``version``
parameter was discarded and the ``msgtype`` parameter name was
normalized as well.

Link
----
:func:`parse_link` parses an HTTP :http:header:`Link` header as
described in :rfc:`5988` into a sequence of
:class:`ietfparse.datastructures.LinkHeader` instances.

>>> from ietfparse import headers
>>> parsed = headers.parse_link(
...     '<http://example.com/TheBook/chapter2>; rel="previous"; '
...     'title="previous chapter"')
>>> parsed[0].target
'http://example.com/TheBook/chapter2'
>>> parsed[0].parameters
[('rel', 'previous'), ('title', 'previous chapter')]

Notice that the parameter values are returned as a list of name and value
tuples.  This is by design and required by the RFC to support the
``hreflang`` parameter as specified:

   The "hreflang" parameter, when present, is a hint indicating what the
   language of the result of dereferencing the link should be.  Note
   that this is only a hint; for example, it does not override the
   Content-Language header of a HTTP response obtained by actually
   following the link.  Multiple "hreflang" parameters on a single link-
   value indicate that multiple languages are available from the
   indicated resource.
