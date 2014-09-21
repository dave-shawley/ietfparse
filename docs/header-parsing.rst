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
