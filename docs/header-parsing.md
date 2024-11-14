# Supported headers

Parsing IETF headers is a difficult science at best.  They come in a wide
variety of syntaxes each with their own peculiarities.  The functions in
this module expect that the incoming header data is formatted appropriately.
If it is not, then a data-related exception will be raised.  Any of the
following exceptions can be raised from **any** of the header parsing
functions: [AttributeError][], [IndexError][], [TypeError][], and
[ValueError][].

This approach is an intentional design decision on the part of the author.
Instead of inventing another list of *garbage-in -> garbage-out* exception
types, I chose to simply let the underlying exception propagate.  This means
that you should always guard against at least this set of exceptions.

| Header                              | Represented as...                                    | Parsed by...                                |
|-------------------------------------|------------------------------------------------------|---------------------------------------------|
| [Accept](#accept)                   | sequence of [ietfparse.datastructures.ContentType][] | [ietfparse.headers.parse_accept][]          |
| [Accept-Charset](#accept-charset)   | sequence of strings                                  | [ietfparse.headers.parse_accept_charset][]  |
| [Accept-Encoding](#accept-encoding) | sequence of strings                                  | [ietfparse.headers.parse_accept_encoding][] |
| [Accept-Language](#accept-language) | sequence of strings                                  | [ietfparse.headers.parse_accept_language][] |
| [Cache-Control](#cache-control)     | mapping of parameter to value                        | [ietfparse.headers.parse_cache_control][]   |
| [Content-Type](#content-type)       | [ietfparse.datastructures.ContentType][]             | [ietfparse.headers.parse_content_type][]    |
| [Forwarded](#forwarded)             | sequence of mappings                                 | [ietfparse.headers.parse_forwarded][]       |
| [Link](#link)                       | sequence of [ietfparse.datastructures.LinkHeader][]  | [ietfparse.headers.parse_link][]            |

## Accept

[ietfparse.headers.parse_accept][] parses the [HTTP-Accept] header into a
sorted list of [ietfparse.datastructures.ContentType][] instances. The list is
sorted according to the specified quality values. Elements with the same quality
value are ordered with the *most-specific* value first. The following is a good
example of this is from
[section 12.5.1 of RFC-9110](https://www.rfc-editor.org/rfc/rfc9110#section-12.5.1-11).

```pycon
>>> from ietfparse import headers
>>> requested = headers.parse_accept(
...     'text/*, text/plain, text/plain;format=flowed, */*')
>>> [str(h) for h in requested]
['text/plain; format=flowed', 'text/plain', 'text/*', '*/*']
```

The requested types all have the same quality value (implicitly 1.0), so they
are sorted purely by specificity. Though the result is sorted according to
quality and specificity, selecting a matching content type is not as easy as
traversing the list in order. The full algorithm for selecting the most
appropriate content type is described in [RFC-9110] and is fully implemented by
[ietfparse.algorithms.select_content_type][].

## Accept-Charset

[ietfparse.headers.parse_accept_charset][] parses the [HTTP-Accept-Charset]
header into a sorted sequence of character set identifiers. Character set
identifiers are simple tokens with an optional quality value that is the
strength of the preference from most preferred (1.0) to rejection (0.0).
After the header is parsed and sorted, the quality values are removed and
the token list is returned.

```pycon
>>> from ietfparse import headers
>>> charsets = headers.parse_accept_charset('latin1;q=0.5, utf-8;q=1.0, '
...                                         'us-ascii;q=0.1, ebcdic;q=0.0')
['utf-8', 'latin1', 'us-ascii', 'ebcdic']
```

The wildcard character set if present, will be sorted towards the end of the
list.  If both a wildcard and rejected values are present, then the wildcard
will occur *before* the rejected values.

```pycon
>>> from ietfparse import headers
>>> headers.parse_accept_charset('acceptable, rejected;q=0, *')
['acceptable', '*', 'rejected']
```

!!! note
    The only attribute that is allowed to be specified per the RFC is the
    quality value.  If additional parameters are included, they are not
    included in the response from this function.  More specifically, the
    returned list contains only the character set strings.

## Accept-Encoding

[ietfparse.headers.parse_accept_encoding][] parses the [HTTP-Accept-Encoding]
header into a sorted sequence of encodings. Encodings are simple tokens with
an optional quality value that is the strength of the preference from most
preferred (1.0) to rejection (0.0). After the header is parsed and sorted,
the quality values are removed and the token list is returned.

```pycon
>>> from ietfparse import headers
>>> headers.parse_accept_encoding('snappy, compress;q=0.7, gzip;q=0.8')
['snappy', 'gzip', 'compress']
```

The wildcard character set if present, will be sorted towards the end of the
list. If both a wildcard and rejected values are present, then the wildcard
will occur *before* the rejected values.

```pycon
>>> from ietfparse import headers
>>> headers.parse_accept_encoding('compress, snappy;q=0, *')
['compress', '*', 'snappy']
```

!!! note
    The only attribute that is allowed to be specified per the RFC is the
    quality value. If additional parameters are included, they are not
    included in the response from this function.  More specifically, the
    returned list contains only the character set strings.

## Accept-Language

[ietfparse.headers.parse_accept_language][] parses the [HTTP-Accept-Language]
header into a sorted sequence of languages. Languages are simple tokens with an
optional quality value that is the strength of the preference from most
preferred (1.0) to rejection (0.0). After the header is parsed and sorted,
the quality values are removed and the token list is returned.

```pycon
>>> from ietfparse import headers
>>> headers.parse_accept_language('de, en;q=0.7, en-gb;q=0.8')
['de', 'en-gb', 'en']
```

The wildcard character set if present, will be sorted towards the end of the
list. If both a wildcard and rejected values are present, then the wildcard
will occur *before* the rejected values.

```pycon
>>> from ietfparse import headers
>>> headers.parse_accept_language('es-es, en;q=0, *')
['es-es', '*', 'en']
```

!!! note
    The only attribute that is allowed to be specified per the RFC is the
    quality value.  If additional parameters are included, they are not
    included in the response from this function.  More specifically, the
    returned list contains only the character set strings.

## Cache-Control

[ietfparse.headers.parse_cache_control][] parses the [HTTP-Cache-Control]
header as described into a dictionary of directives.

Directives without a value such as `public` and `no-cache` will be returned
in the dictionary with a value of `True` if set.

```pycon
>>> from ietfparse import headers
>>> headers.parse_cache_control('public, max-age=2592000')
{'public': True, 'max-age': 2592000}
```

## Content-Type

[ietfparse.headers.parse_content_type][] parses a MIME or [HTTP-Content-Type]
header into a [ietfparse.datastructures.ContentType] instance that exposes the
structured data.

```pycon
>>> from ietfparse import headers
>>> header = headers.parse_content_type('text/html; charset=ISO-8859-4')
>>> header.content_type, header.content_subtype
('text', 'html')
>>> header.parameters['charset']
'ISO-8859-4'
```

It handles unquoting and normalizing the value. The content type and all
parameter names are translated to lower-case during the parsing process. The
relatively unknown option to include comments in the content type is honored
and comments are discarded.

```pycon
>>> header = headers.parse_content_type(
...     'message/http; version=2.0 (someday); MSGTYPE="request"')
>>> header.parameters['version']
'2.0'
>>> header.parameters['msgtype']
'request'
```

Notice that the `(someday)` comment embedded in the `version` parameter
was discarded and the `msgtype` parameter name was normalized as well.

## Forwarded

[ietfparse.headers.parse_forwarded][] parses the [HTTP-Forwarded] header into
a sequence of [dict][] instances.

```pycon
>>> from ietfparse import headers
>>> parsed = headers.parse_forwarded('For=93.184.216.34;proto=http;'
...                                  'By="[2606:2800:220:1:248:1893:25c8:1946]";'
...                                  'host=example.com')
>>> len(parsed)
1
>>> parsed[0]['for']
'93.184.216.34'
>>> parsed[0]['proto']
'http'
>>> parsed[0]['by']
'[2606:2800:220:1:248:1893:25c8:1946]'
>>> parsed[0]['host']
'example.com'
```

The names of the parameters are case-folded to lower case per the
recommendation in [RFC-7239-section-4].

## Link

[ietfparse.headers.parse_link][] parses an [HTTP-Link] header into a sequence
of [ietfparse.datastructures.LinkHeader][] instances.

```pycon
>>> from ietfparse import headers
>>> parsed = headers.parse_link(
...     '<http://example.com/TheBook/chapter2>; rel="previous"; '
...     'title="previous chapter"')
>>> parsed[0].target
'http://example.com/TheBook/chapter2'
>>> parsed[0].parameters
[('rel', 'previous'), ('title', 'previous chapter')]
>>> str(parsed[0])
'<http://example.com/TheBook/chapter2>; rel="previous"; title="previous chapter"'
```

Notice that the parameter values are returned as a list of name and value
tuples.  This is by design and required by the RFC to support the
`hreflang` parameter:

!!! quote "[RFC-8288-section-3.4.1]"
    The "hreflang" parameter, when present, is a hint indicating what the
    language of the result of dereferencing the link should be.  Note
    that this is only a hint; for example, it does not override the
    Content-Language header of a HTTP response obtained by actually
    following the link.  Multiple "hreflang" parameters on a single link-
    value indicate that multiple languages are available from the
    indicated resource.

Also note that you can cast a [ietfparse.datastructures.LinkHeader][]
instance to a string to get a correctly formatted representation of it.
