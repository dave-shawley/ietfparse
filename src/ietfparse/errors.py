"""Exceptions raised from within ietfparse.

All exceptions are rooted at [ietfparse.errors.RootException][], so
you can catch it to implement error handling behavior associated with
this library's functionality.

"""


class RootException(Exception):
    """Root of the ``ietfparse`` exception hierarchy."""


class NoMatch(RootException):
    """No match was found when selecting a content type."""


class MalformedLinkValue(RootException):
    """Value specified is not a valid link header."""


class StrictHeaderParsingFailure(RootException, ValueError):
    """Non-standard header value detected.

    This is raised when "strict" conformance is enabled for a
    header parsing function and a header value fails due to one
    of the "strict" rules.

    See [ietfparse.headers.parse_forwarded][] for an example.

    """

    def __init__(self, header_name: str, header_value: str) -> None:
        super().__init__(header_name, header_value)
        self.header_name = header_name
        self.header_value = header_value


class MalformedContentType(StrictHeaderParsingFailure):
    """Attempted to parse a malformed [HTTP-Content-Type] header."""

    def __init__(self, header_value: str) -> None:
        super().__init__('content-type', header_value)
