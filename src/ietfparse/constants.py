"""Useful constant values.

!!! warning

    Take care when comparing content type values since equality comparison
    includes comparing parameter values. The
    [ietfparse.algorithms.select_content_type][] algorithm should be used
    to select content type based on the [HTTP-Accept] header.

    ```pycon
    >>> from ietfparse import headers
    >>> a = headers.parse_content_type('application/json')
    >>> b = headers.parse_content_type('application/json; charset=utf-8')
    >>> c = headers.parse_content_type('application/json; charset="UTF-8"')
    >>> a == b
    False
    >>> a == c
    False
    >>> b == c
    True
    ```

    The last example shows that parameters are normalized when parsing.

"""

from ietfparse import datastructures as ds
from ietfparse import headers

APPLICATION_JSON: ds.ContentType = headers.parse_content_type(
    'application/json'
)
"""[RFC-8259]: The JavaScript Object Notation (JSON) Data Interchange Format"""

APPLICATION_OCTET_STREAM: ds.ContentType = headers.parse_content_type(
    'application/octet-stream'
)
"""Default content type for the Internet as described in [RFC=2045]"""

APPLICATION_PROBLEM_JSON: ds.ContentType = headers.parse_content_type(
    'application/problem+json'
)
"""HTTP API error document as described by [RFC-9457]"""

APPLICATION_XML: ds.ContentType = headers.parse_content_type('application/xml')
"""eXtensible Markup Language as described in [RFC-7303]"""

TEXT_HTML: ds.ContentType = headers.parse_content_type(
    'text/html; charset=UTF-8'
)
"""[HyperText Markup Language](https://html.spec.whatwg.org/multipage/)"""

TEXT_JAVASCRIPT: ds.ContentType = headers.parse_content_type(
    'text/javascript; charset=UTF-8'
)
"""ECMAScript Media Types ([RFC-9239])"""

TEXT_MARKDOWN: ds.ContentType = headers.parse_content_type(
    'text/markdown; charset=UTF-8'
)
"""Markdown documents ([RFC-7763])

RFC-7763 is the formal registration for Markdown formatted content.
[Daring Fireball: Markdown](http://daringfireball.net/projects/markdown/)
is the document specification.
"""

TEXT_PLAIN: ds.ContentType = headers.parse_content_type('text/plain')
"""Simple text content encoded in UTF-8 characters
([RFC-2046-section-4.1.3])"""
