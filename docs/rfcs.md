# Relevant RFCs

## [RFC-2045]
[ietfparse.datastructures.ContentType][] is an abstraction of the [HTTP-Content-Type].
This header is fully specified in [RFC-2045-section-5.1].

## [RFC-6839]
[ietfparse.headers.parse_content_type][] and [ietfparse.datastructures.ContentType][]
support structured syntax content suffixes.

## [RFC-7239]
[ietfparse.headers.parse_forwarded][] parses a [HTTP-Forwarded] header

## [RFC-8288]
- [ietfparse.headers.parse_link][] parses a [HTTP-Link] header
- [ietfparse.datastructures.LinkHeader][] represents an element in a [HTTP-Link] header

## [RFC-9110]
- [ietfparse.algorithms.select_content_type][] implements Proactive Content Negotiation
  as described in [RFC-9110-name-proactive-negotiation]
- [ietfparse.headers.parse_accept][] parses [HTTP-Accept]
- [ietfparse.headers.parse_accept_charset][] parses [HTTP-Accept-Charset]
- [ietfparse.headers.parse_accept_encoding][] parses [HTTP-Accept-Encoding]
- [ietfparse.headers.parse_accept_language][] parses [HTTP-Accept-Language]
- [ietfparse.headers.parse_list][] parses many of the comma-separated list headers

## [RFC-9111]
[ietfparse.headers.parse_cache_control][] parses a [HTTP-Cache-Control] header
