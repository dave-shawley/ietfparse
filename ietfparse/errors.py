"""
Exceptions raised from within ietfparse.

All exceptions are rooted at :class:`~ietfparse.errors.RootException` so
so you can catch it to implement error handling behavior associated with
this library's functionality.

"""


class RootException(Exception):
    """Root of the ``ietfparse`` exception hierarchy."""
    pass


class NoMatch(RootException):
    """No match was found when selecting a content type."""
    pass


class MalformedLinkValue(RootException):
    """Value specified is not a valid link header."""
    pass


class StrictHeaderParsingFailure(RootException, ValueError):
    """
    Non-standard header value detected.

    This is raised when "strict" conformance is enabled for a
    header parsing function and a header value fails due to one
    of the "strict" rules.

    See :func:`ietfparse.headers.parse_forwarded` for an example.

    """
    def __init__(self, header_name, header_value):
        super(StrictHeaderParsingFailure,
              self).__init__(header_name, header_value)
        self.header_name = header_name
        self.header_value = header_value
