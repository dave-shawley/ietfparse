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
