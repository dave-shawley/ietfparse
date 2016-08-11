ietfparse
=========

|Version| |ReadTheDocs| |Travis| |Coverage| |CodeClimate|

Wait... Why? What??
-------------------
This is a gut reaction to the wealth of ways to parse URLs, MIME headers,
HTTP messages and other things described by IETF RFCs.  They range from
the Python standard library (``urllib``) to be buried in the guts of other
*kitchen sink* libraries (``werkzeug``) and most of them are broken in one
way or the other.

So why create another one?  Good question... glad that you asked.  This is
a companion library to the great packages out there that are responsible for
communicating with other systems.  I'm going to concentrate on providing a
crisp and usable set of APIs that concentrate on parsing text.  Nothing more.
Hopefully by concentrating on the specific task of parsing things, the result
will be a beautiful and usable interface to the text strings that power the
Internet world.

Here's a sample of the code that this library lets you write::

    from ietfparse import algorithms, headers

    def negotiate_versioned_representation(request, handler, data_dict):
        requested = headers.parse_accept(request.headers['Accept'])
        selected = algorithms.select_content_type(requested, [
            headers.parse_content_type('application/example+json; v=1'),
            headers.parse_content_type('application/example+json; v=2'),
            headers.parse_content_type('application/json'),
        ])

        output_version = selected.parameters.get('v', '2')
        if output_version == '1':
            handler.set_header('Content-Type', 'application/example+json; v=1')
            handler.write(generate_legacy_json(data_dict))
        else:
            handler.set_header('Content-Type', 'application/example+json; v=2')
            handler.write(generate_modern_json(data_dict))

    def redirect_to_peer(host, port=80):
        flask.redirect(algorithms.rewrite_url(flask.request.url,
                                              host=host, port=port))

Ok... Where?
------------
+---------------+-------------------------------------------------+
| Source        | https://github.com/dave-shawley/ietfparse       |
+---------------+-------------------------------------------------+
| Status        | https://travis-ci.org/dave-shawley/ietfparse    |
+---------------+-------------------------------------------------+
| Download      | https://pypi.python.org/pypi/ietfparse          |
+---------------+-------------------------------------------------+
| Documentation | http://ietfparse.readthedocs.org/en/latest      |
+---------------+-------------------------------------------------+
| Issues        | https://github.com/dave-shawley/ietfparse       |
+---------------+-------------------------------------------------+

.. |CodeClimate| image:: https://codeclimate.com/github/dave-shawley/ietfparse/badges/gpa.svg
   :target: https://codeclimate.com/github/dave-shawley/ietfparse/
.. |Coverage| image:: https://coveralls.io/repos/dave-shawley/ietfparse/badge.svg
   :target: https://coveralls.io/r/dave-shawley/ietfparse
.. |ReadTheDocs| image:: https://readthedocs.org/projects/ietfparse/badge/
   :target: https://ietfparse.readthedocs.org/
.. |Travis| image:: https://travis-ci.org/dave-shawley/ietfparse.svg
   :target: https://travis-ci.org/dave-shawley/ietfparse
.. |Version| image:: https://badge.fury.io/py/ietfparse.svg
   :target: http://badge.fury.io/py/ietfparse
