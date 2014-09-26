.. py:currentmodule:: ietfparse.headers

URL Processing
==============
If your applications have reached the `Glory of REST`_ by using hypermedia
controls throughout, then you aren't manipulating URLs a lot unless you
are responsible for generating them.  However, if you are interacting with
less mature web applications, you need to manipulate URLs and you are probably
doing something like:

>>> url_pattern = 'http://example.com/api/movie/{movie_id}/actors'
>>> response = requests.get(url_pattern.format(movie_id=ident))

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
Templates which happens to handle our case quite well. :func:`rewrite_url`
is closer to the :func:`~urllib.parse.urlsplit` and
:func:`~urllib.parse.urlunsplit` case with a nicer interface.

.. _Glory of REST: http://martinfowler.com/articles/richardsonMaturityModel.html
