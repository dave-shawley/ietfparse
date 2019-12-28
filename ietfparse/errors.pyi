class RootException(Exception):
    ...


class NoMatch(RootException):
    ...


class MalformedLinkValue(RootException):
    ...


class StrictHeaderParsingFailure(RootException, ValueError):
    ...
