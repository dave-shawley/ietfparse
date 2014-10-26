.. py:currentmodule:: ietfparse.algorithms

URL Processing
==============
If your applications have reached the `Glory of REST`_ by using hypermedia
controls throughout, then you aren't manipulating URLs a lot unless you
are responsible for generating them.  However, if you are interacting with
less mature web applications, you need to manipulate URLs and you are probably
doing something like:

>>> url_pattern = 'http://example.com/api/movie/{movie_id}/actors'
>>> response = requests.get(url_pattern.format(movie_id=ident))

or even *(the horror)*:

>>> url = 'http://{0}/{1}?{2}'.format(host, path, query)
>>> response = requests.get(url)

If you are a little more careful, you could be URL encoding the argument
to prevent *URL injection attacks*.  This isn't a horrible pattern for
generating URLs from a known pattern and data.  But what about other
types of manipulation?  How do you take a URL and point it at a different
host?

>>> # really brute force?
>>> url = url_pattern.format(movie_id=1234)
>>> url = url[:7] + 'host.example.com' + url[18:]

>>> # with str.split + str.join??
>>> parts = url.split('/')
>>> parts[2] = 'host.example.com'
>>> url = '/'.join(parts)

>>> # leverage the standard library???
>>> import urllib.parse
>>> parts = urllib.parse.urlsplit(url)
>>> url = urllib.parse.urlunsplit((parts.scheme, 'host.example.com',
...     parts.path, parts.query, parts.fragment))
...
>>>

Let's face it, manipulating URLs in Python is less than ideal.  What about
something like the following instead?

>>> from ietfparse import algorithms
>>> url = algorithms.encode_url_template(url_pattern, movie_id=1234)
>>> url = algorithms.rewrite_url(url, host='host.example.com')

And, **yes**, the :func:`encode_url_template` is doing a bit more than
calling :meth:`str.format`.  It implements the full gamut of :rfc:`6570` URL
Templates which happens to handle our case quite well.

:func:`rewrite_url` is closer to the :func:`~urllib.parse.urlsplit` and
:func:`~urllib.parse.urlunsplit` case with a nicer interface and a bit of
additional functionality as well.  For example, if you are a little more
forward looking, then you probably have heard of *International Domain Names*
(:rfc:`5980`).  The :func:`rewrite_url` function will correctly encode names
using the :mod:`codecs.idna`.  It also implements the same query encoding
tricks that :func:`~urllib.parse.urlencode` does.

>>> from ietfparse import algorithms
>>> algorithms.rewrite_url('http://example.com', query={'b': 12, 'a': 'c'})
'http://example.com?a=c&b=12'
>>> algorithms.rewrite_url('http://example.com', query=[('b', 12), ('a', 'c')])
'http://example.com?b=12&a=c'

There is a lot going on in those two examples.  See the documentation for
:func:`rewrite_url` for all of the details.

Relevant Specifications
-----------------------

- `[RFC1034]`_ *"Domain Names - concepts and facilities"*, esp. Section 3.5
- `[RFC3986]`_ *"Uniform Resource Identifiers: Generic Syntax"*
- `[RFC5890]`_ *"Internationalized Domain Names for Applications (IDNA)"*
- `[RFC7230]`_ *"Hypertext Transfer Protocol (HTTP/1.1): Message
  Syntax and Routing"*

Known and Accepted Variances
----------------------------
Some of the IETF specifications require deep understanding of the underlying
URL scheme.  These portions are not implemented since they would unnecessarily
couple this library to an open-ended set of protocol specifications.  This
section attempts to cover all such variances.

The ``host`` portion of a URL is not strictly required to be a valid DNS
name for schemes that are restricted to using DNS names.  For example,
``http://-/`` is a questionably valid URL.  :rfc:`1035#section-3.5` prohibits
domain names from beginning with a hyphen and :rfc:`7230#section-2.7.1`
strongly implies (requires?) that the host be an IP literal or valid DNS
name.  However, ``file:///-`` is perfectly acceptable, so the requirement
specific to HTTP is left unenforced.

Similarly, the ``port`` portion of a network location is usually a network
port which is limited to 16-bits by both :rfc:`793` and :rfc:`768`.  This
is strictly required to be a TCP port in the case of HTTP (:rfc:`7230`).
This library only limits the ``port`` to a non-negative integer.  The other
*SHOULD* that is not implemented is the suggestion that default port numbers
are omitted - see section 3.2.3 of :rfc:`3986#section-3.2.3`.

Influencing URL Processing
--------------------------
URLs are finicky things with a wealth of specifications that sometimes seem
to contradict each other.  Whenever a grey area was encountered, this library
tried to make the result controllable from the outside.  For example,
section 3.2.2 of :rfc:`3986#section-3.2.2` contains the following paragraph
when describing the host portion of the URL.

    The reg-name syntax allows percent-encoded octets in order to
    represent non-ASCII registered names in a uniform way that is
    independent of the underlying name resolution technology.  Non-ASCII
    characters must first be encoded according to UTF-8 [STD63], and then
    each octet of the corresponding UTF-8 sequence must be percent-
    encoded to be represented as URI characters.  URI producing
    applications must not use percent-encoding in host unless it is used
    to represent a UTF-8 character sequence.  When a non-ASCII registered
    name represents an internationalized domain name intended for
    resolution via the DNS, the name must be transformed to the IDNA
    encoding [RFC3490] prior to name lookup.  URI producers should
    provide these registered names in the IDNA encoding, rather than a
    percent-encoding, if they wish to maximize interoperability with
    legacy URI resolvers.

When :func:`rewrite_url` is called with a ``host`` parameter, it needs to
decide how to encode the string that it is given for inclusion into the URL.
In other words, it needs to decide whether the *name represents an
internationalized domain name intended for resolution via the DNS* or not.
There are two ways to control decisions like this.  The recommended way is
to pass a parameter that explicitly states what you want - the
``encode_with_dna`` keyword to :func:`rewrite_url` is one such case.  A
configuration-based alternative is usually offered as well.  The latter
should be used if you have a special case that is application specific.
For example, the :data:`ietfparse.algorithms.IDNA_SCHEMES` variable is a
collection that the library uses to know which schemes *ALWAYS* apply
IDNA rules to host names.  You can modify this collection as needed to
meet your application requirements.

.. _Glory of REST: http://martinfowler.com/articles/richardsonMaturityModel.html
.. _[RFC1034]: http://tools.ietf.org/html/rfc1034
.. _[RFC3986]: http://tools.ietf.org/html/rfc3986
.. _[RFC5890]: https://tools.ietf.org/html/rfc5890
.. _[RFC7230]: http://tools.ietf.org/html/rfc7230
