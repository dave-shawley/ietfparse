# Algorithms

Header parsing is only part of what you need to write modern web
applications.  You need to implement responsive behaviors that factor
in the state of the server, the resource in question, and information
from the requesting client.

## Content negotiation

[RFC-9110-name-content-negotiation] describes how *Content Negotiation* can
be implemented along various content dimensions (e.g., content type, language,
character encoding, etc.). [ietfparse.algorithms.select_content_type][]
implements *Proactive Negotiation* of the content type dimension. It takes a
list of requested content types (e.g., from [ietfparse.headers.parse_accept][])
along with a list of content types that the server is capable of producing
and returns the content type that is the *best match*. The algorithm is
loosely described in Section 12.5.1 of [RFC-7231-name-accept].

```pycon
>>> from ietfparse import headers
>>> available = [headers.parse_content_type(t)
...              for t in ('text/html', 'text/plain')]
>>> requested = headers.parse_accept(
...   'text/*;q=0.3, text/html;q=0.7, text/plain;format=flowed, '
...   'text/plain;format=fixed;q=0.4, */*;q=0.5')
>>> req_match, avail_match = headers.select_content_type(requested, available)
>>> str(req_match)
'text/html'
```

The function returns the selected value _from each set_ as a pair. The first
value in the pair is the content type that the user requested. This is usually
what you want to return in the [HTTP-Content-Type] header. The second value is
from the list of supported content types. This is what tells the server which
content type from the list of available types should be returned. In other
words, the first value is from the list that the client specified and _knows_.
The response content type should be in terms of what the client asked for.
The second value is from the set of server-supported content types. It is used
to select the renderer for the representation from the set of server _known
values_.

Let's look at an example from a server that supports different versions of
a representation. This is represented by a vendor content type with a version
parameter.

```pycon
>>> from ietfparse import algorithms, headers
>>> requested = headers.parse_accept(
...   'application/vnd.example.com+json;version=2, '
...   'application/vnd.example.com+json;q=0.75, '
...   'application/json;q=0.5, text/javascript;q=0.25'
... )
>>> selected, _ = algorithms.select_content_type(requested, [
...   headers.parse_content_type('application/vnd.example.com+json;version=3'),
...   headers.parse_content_type('application/vnd.example.com+json;version=2'),
... ])
>>> str(selected)
'application/vnd.example.com+json; version=2'
```
