---
title: Home
hide:
  - navigation
  - toc
---
# ietfparse

[![PyPI - Version](https://img.shields.io/pypi/v/ietfparse)](https://pypi.org/project/ietfparse/)
[![Documentation Status](https://readthedocs.org/projects/ietfparse/badge/?version=latest)](https://ietfparse.readthedocs.io/en/latest/?badge=latest)
[![Circle-CI](https://circleci.com/gh/dave-shawley/ietfparse.svg?style=shield)](https://circleci.com/gh/dave-shawley/ietfparse)
![Code Climate coverage](https://img.shields.io/codeclimate/coverage/dave-shawley/ietfparse)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dave-shawley_ietfparse&metric=alert_status)](https://sonarcloud.io/summary/overall?id=dave-shawley_ietfparse)

This project is a gut reaction to the wealth of ways to parse URLs, MIME
headers, HTTP messages and other things described by IETF RFCs. They range
from the Python standard library (`urllib`) to be buried in the guts of other
*kitchen sink* libraries (`werkzeug`) and most of them are broken in one
way or the other.

So why create another one?  *Good question...* glad that you asked. This is
a companion library to the great packages out there that are responsible for
communicating with other systems. I'm going to concentrate on providing a
crisp and usable set of APIs that concentrate on parsing text. Nothing more.
Hopefully by concentrating on the specific task of parsing things, the result
will be a beautiful and usable interface to the text strings that power the
Internet world.

Here's a sample of the code that this library lets you write:

```python
import json
import typing

from ietfparse import algorithms, constants

default_content_type = constants.APPLICATION_JSON
supported = [constants.APPLICATION_JSON, constants.TEXT_HTML]

def render_widget(request, widget):
    """Render `widget` based on the accept header"""
    selected, requested = algorithms.select_content_type(
        request.headers.get('accept'), supported,
        default=default_content_type)
    match selected:
        case constants.APPLICATION_JSON:
            body = json.dumps(widget)
        case constants.TEXT_HTML:
            body = translate_to_html(widget)
        case _ as unreachable:
            typing.assert_never(unreachable)

    return Response(body=body, content_type=str(requested))
```

The `render_widget` function is an implementation of _Proactive Content Negotiation_
as described in [RFC-9110]. It calls [ietfparse.algorithms.select_content_type][]
function to determine the most appropriate content type based on the [HTTP-Accept]
header from the request and the list of content types that the application supports.
Then it renders `widget` in the selected format.

As usual, the devil is in the details. This library understands how to parse HTTP
headers into _datastructures_ and contains _algorithms_ that do useful things with
the parsed values. The datastructures themselves hide a lot of useful functionality.
Consider the [HTTP-Link] header that is synonymous with REST APIs. Links between
resources are represented as a target URL and a _relationship type_. Consider an
implementation of paging through a search result set. A naive implementation places
the onus on the client to select each page by iteratively sending requests with the
page number in the request.

    GET /search?q=...&page-size=100
    GET /search?q=...&page=1&page-size=100
    GET /search?q=...&page=2&page-size=100

The client knows that it is "done" when it gets an empty response. Despite its
simplicity, this approach has a few drawbacks. The largest is that every client has
intimate knowledge of the query parameters and how to go from one response to the
next request. This is a common web antipattern that you probably recognize. If you
have been on the implementation side of search endpoint for a large dataset using
an SQL backend, then you may have run into the performance problems associated with
using `SELECT ... WHERE ... OFFSET {page} LIMIT {size}` style query.

> What happens when we change the pattern from offset and page size to use a
> server-side cursor?

The short answer is that we have to change _every client implementation_. The next
iteration is usually to add pagination information into the response structure.
Something like:

```json
{
  "data": [],
  "paging": {
    "total": 1234,
    "next": "/search?q=...&page=4&page-size=100",
    "previous": "/search?q=...&page=3&page-size=100",
    "first": "/search?q=..."
  }
}
```

Now our clients can follow links embedded in the response structure and the server
is completely in control of the pagination API. If the traversal algorithm changes
to pass a cursor in the URL, then it simply changes the links between pages in the
response. This is at the core of what Roy Fielding termed the Representational State
Transfer interaction pattern. There is still a problem in here ... clients need to
parse metadata from the responses. In essence, they have to separate the data and
the pagination data in the response. The [HTTP-Link] header is used to move the
links between representations out of the body and into HTTP headers.

```
GET /search?q=...&page=3&page-size=100 HTTP/1.1
Accept: application/json, application/msgpack;q=0.7

HTTP/1.1 200 OK
Content-Type: application/json
Link: </search?q=...&page=4&page-size=100>; rel="next"
Link: </search?q=...&page=4&page-size=100>; rel="next"
Link: </search?q=...&page=4&page-size=100>; rel="previous"
Link: </search?q=...>; rel="first"

[]
```

Now the response is simply a list of items found. Much easier to handle on the
client side of things. However, `Link` headers have a complex syntax so parsing
them requires some work. In addition to the individual header values, they can
be combined into a single `Link` header contain a comma-separated list of values.
The [ietfparse.headers.parse_link][] function transforms a `Link` header into a
list of datastructures that make accessing the individual properties simple.

```pycon
>>> from ietfparse import headers
>>> links = headers.parse_link('</search?q=...&page=4&page-size=100>; rel="next"')
>>> len(links)
1
>>> links[0].rel
'next'
>>> links[0].target
'/search?q=...&page=4&page-size=100'
>>> str(links[0])
'</search?q=...&page=4&page-size=100>; rel="next"'
>>> links[0]
<ietfparse.datastructures.LinkHeader object at 0x100ad0620>
```

The [ietfparse.datastructures.LinkHeader][] class is also useful for generating link
headers.

```pycon
>>> from iefparse import datastructures
>>> next_page = datastructures.LinkHeader(
...    '/search?q=...&page=4&page-size=100',
...    [('rel', 'next')])
>>> str(next_page)
'</search?q=...&page=4&page-size=100>; rel="next"'
```

Single link values are _pretty simple_. They get more complicated with the
addition of properties. The `LinkHeader` instance knows how to correctly
format property values contain various problematic characters so that you
do not need to be an expert.

The `Link` header is one of the many headers supported by this library. See
the [Header Parsing](header-parsing.md) section for a complete (and up tp date) list.


[API Documentation]: https://ietfparse.readthedocs.io/en/latest/?badge=latest
[Accept]: https://www.rfc-editor.org/rfc/rfc9110#field.accept
[HTTP Link header]: https://www.rfc-editor.org/rfc/rfc8288
[RFC-9110]: https://www.rfc-editor.org/rfc/rfc9110#name-proactive-negotiation
