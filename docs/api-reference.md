# API Reference

## ietfparse.algorithms

::: ietfparse.algorithms.select_content_type

## ietfparse.constants

This module contains some useful constant values for using alongside
[ietfparse.datastructures.ContentType][] instances or as parameters to the
[ietfparse.algorithms.select_content_type][] function. These are cherry-picked from the
[IANA Media Types registry](https://www.iana.org/assignments/media-types/media-types.xhtml).

::: ietfparse.constants
    options:
      summary:
        attributes: true

## ietfparse.datastructures

::: ietfparse.datastructures.ContentType
::: ietfparse.datastructures.LinkHeader

## ietfparse.errors

::: ietfparse.errors.RootException
::: ietfparse.errors.NoMatch
::: ietfparse.errors.MalformedContentType
::: ietfparse.errors.MalformedLinkValue
::: ietfparse.errors.StrictHeaderParsingFailure

## ietfparse.headers

::: ietfparse.headers.parse_accept
::: ietfparse.headers.parse_accept_charset
::: ietfparse.headers.parse_accept_encoding
::: ietfparse.headers.parse_accept_language
::: ietfparse.headers.parse_cache_control
::: ietfparse.headers.parse_content_type
::: ietfparse.headers.parse_forwarded
::: ietfparse.headers.parse_link
::: ietfparse.headers.parse_list
