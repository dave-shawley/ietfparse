.. py:currentmodule:: ietfparse.algorithms

Request Processing
==================
Header parsing is only part of what you need to write modern web
applications.  You need to implement responsive behaviors that factor
in the state of the server, the resource in question, and information
from the requesting client.

Content Negotiation
-------------------
:rfc:`7231#section-3.4` describes how *Content Negotiation* can
be implemented.  :func:`select_content_type` implements the type selection
portion of *Proactive Negotiation*.  It takes a list of requested content
types (e.g., from :func:`~ietfparse.headers.parse_accept`)
along with a list of content types that the server is capable of producing
and returns the content type that is the *best match*.  The algorithm is
loosely described in Section 5.3 of :rfc:`7231#section-5.3`.

>>> from ietfparse import headers
>>> requested = headers.parse_accept(
...   'text/*;q=0.3, text/html;q=0.7, text/html;level=1, '
...   'text/html;level=2;q=0.4, */*;q=0.5')
>>> headers.select_content_type(
...   requested,
...   ['text/html', 'text/html;level=4', 'text/html;level=3'])
'text/html

A more interesting case is to select the representation to produce based
on what a server knows how to produce and what a client has requested.

>>> from ietfparse import algorithms, headers
>>> requested = headers.parse_accept(
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
