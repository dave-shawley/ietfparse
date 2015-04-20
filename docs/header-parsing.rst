.. py:currentmodule:: ietfparse.headers

Header Parsing
==============

HTTP Content-Type
-----------------
:func:`parse_content_type` parses a MIME or HTTP :mailheader:`Content-Type`
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

HTTP Accept
-----------
:func:`parse_http_accept_header` parses the HTTP :mailheader:`Accept` header
into a sorted list of :class:`ietfparse.datastructures.ContentType` instances.
The list is sorted according to the specified quality values. Elements with
the same quality value are ordered with the *most-specific* value first.  The
following is a good example of this from section 5.3.2 of
:rfc:`7231#section-5.3.2`.

>>> from ietfparse import headers
>>> requested = headers.parse_http_accept_header(
...     'text/*, text/plain, text/plain;format=flowed, */*')
>>> [str(h) for h in requested]
['text/plain; format=flowed', 'text/plain', 'text/*', '*/*']

All of the requested types have the same quality - implicitly 1.0 so they
are sorted purely by specificity.  Though the result is sorted according
to quality and specificity, selecting a matching content type is not as
easy as traversing the list in order.  The full algorithm for selecting the
most appropriate content type is described in :rfc:`7231` and is fully
implemented by :func:`~ietfparse.algorithms.select_content_type`.

Link
----
:func:`parse_link_header` parses an HTTP :mailheader:`Link` header as
described in :rfc:`5988` into a sequence of
:class:`ietfparse.datastructures.LinkHeader` instances.

>>> from ietfparse import headers
>>> parsed = headers.parse_link_header(
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
