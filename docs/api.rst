Header Parsing
==============

.. py:currentmodule:: ietfparse.headers

The ``ietfparse.headers`` module contains functions for parsing
IETF header values into objects.

HTTP Content-Type
-----------------
The :func:`parse_content_type` function parses a MIME or HTTP
:mailheader:`Content-Type` header into an object that exposes the
structured data.

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
The :func:`parse_http_accept_header` function parses the HTTP
:mailheader:`Accept` header into a sorted list of :class:`.ContentType`
instances.  The list is sorted according to the specified quality values.
Elements with the same quality value are ordered with the *most-specific*
value first.  The following is a good example of this from section 5.3.2
of :rfc:`7231#section-5.3.2`.

>>> from ietfparse import headers
>>> requested = headers.parse_http_accept_header(
...     'text/*, text/plain, text/plain;format=flowed, */*')
>>> [str(h) for h in requested]
['text/plain; format=flowed', 'text/plain', 'text/*', '*/*']

All of the requested types have the same quality - implicitly 1.0 so they
are sorted purely by specificity.


Header Processing
=================

Header parsing is only part of what you need to write modern web
applications.  You need to implement behaviors based on the headers as
well.  :rfc:`7231#section-3.4` describes how *Content Negotiation* can
be implemented.  This :func:`select_content_type` function implements
the type selection portion of *Proactive Negotiation*.  It takes a list
of requested content types (e.g., from :func:`parse_http_accept_header`)
along with a list of content types that the server is capable of producing
and returns the content type that is the *best match*.  The algorithm is
loosely described in Section 5.3 of :rfc:`7231#section-5.3`.

>>> from ietfparse import headers
>>> requested = headers.parse_http_accept_header(
...   'text/*;q=0.3, text/html;q=0.7, text/html;level=1, '
...   'text/html;level=2;q=0.4, */*;q=0.5')
>>> headers.select_content_type(
...   requested,
...   ['text/html', 'text/html;level=4', 'text/html;level=3'])
'text/html

.. py:currentmodule:: ietfparse.algorithms

A more interesting case is to select the representation to produce based
on what a server knows how to produce and what a client has requested.

>>> from ietfparse import algorithms, headers
>>> requested = headers.parse_http_accept_header(
...   'application/vnd.example.com+json;version=2, '
...   'application/vnd.example.com+json;q=0.75, '
...   'application/json;q=0.5, text/javascript;q=0.25'
... )
>>> selected = algorithms.select_content_type(requested, [
...   headers.parse_content_type('application/vnd.example.com+json;version=3'),
...   headers.parse_content_type('application/vnd.example.com+json;version=2'),
... ])
>>> str(selected)
'application/vnd.example.com+json; version=2'

The :func:`select_content_type` function is an implementation of *Proactive
Content Negotiation* as described in :rfc:`7231#section-3.4.1`.
