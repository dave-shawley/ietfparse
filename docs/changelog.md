# Release History

## [Unreleased]

### Breaking Changes

- removed support for Python versions before 3.9
- `datastructures.LinkHeader` is now immutable
- converted positional Boolean parameters to keyword-only parameters

  | Function           | Parameter                  |
  |--------------------|----------------------------|
  | parse_accept       | strict                     |
  | parse_content_type | normalize_parameter_values |
  | parse_forwarded    | only_standard_parameters   |
  | parse_link         | strict                     |


### Added

- `ietfparse.constants` module -- _this contains constant ContentType instances_
- [pre-commit](https://pre-commit.com/) utility usage
- `datastructures.LinkHeader.rel` property
- indexed parameter lookup in `datastructures.LinkHeader`
- `datastructures.ImmutableSequence` helper class
- `errors.MalformedContentType` exception explicitly identifies [HTTP-Content-Type]
  parsing failures. It is a subclass of `ValueError` for the sake of compatability.
- `default` parameter to `algorithms.select_content_type`

### Changed

- `headers.parse_link` changed to honor the allow multiple `media` and `type`
  parameters as described in [RFC-8288-section-3.4.1].
- `datastructures.LinkHeader` changed to combine multiple relationship type
  (rel) parameters into a single space-separated parameter as described in
  [RFC-8288-section-3]. Note that this is only relevant if you disable strict
  mode parsing.
- `headers.parse_content_type` changed to raise `MalformedContentType` error
  instead of `ValueError`.
- `datastructures.ContentType` instances can now be compared to strings
- `algorithms.select_content_type` changed to accept strings as well as `ContentType`
  instances


### Removed

- previously deprecated functions: `parse_http_accept_header`, `parse_link_header`,
  `parse_list_header`, `remove_url_auth`, `rewrite_url`

### Development environment changes

- replaced setuptools with [hatch](https://hatch.pypa.io/)
- switched from sphinx to mkdocs
- switch to the [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)

## [1.9.0] -- 2022-07-08

### Deprecated
- using `len()` on the return value from `algorithms.remove_url_auth`
- `rewrite_url` and `remove_url_auth`.  Use [yarl] instead.  It is an
  awesome library and a more general solution.

### Changed
- `algorithms.RemoveUrlAuthResult` from a named tuple to a proper class.
- Replace type hints with annotations.

### Removed
- ``ietfparse.compat`` module.
- universal wheels

## [1.8.0] -- 2021-08-11

### Removed
- support for Python versions before 3.7

## [1.7.0] -- 2020-11-04

### Behavioural Change
`headers.parse_accept` used to fail with a `ValueError` when it encountered
an invalid content type value in the header. Now it skips the invalid value
instead. If you want the previous behaviour, then pass `strict=True`.

### Added
- support for Python 3.7-3.9

### Removed
- support for 3.4 and 3.5

### Changed
- clarified that `headers.parse_content_type` raises a `ValueError` when it
  encounters an invalid content type header
- `headers.parse_accept` skips unparseable content types unless the new
  `strict` keyword parameter is truthy

## [1.6.1] -- 2020-01-26

### Fixed
- corrected packaging metadata

## [1.6.0] -- 2020-01-25

### Added
- typestubs

### Changed
- switched from travis-ci to circle-ci
- allow "bad whitespace" around `=` in link header parameter lists as
  indicated in [RFC-8288-section-3]
- replaced *nosetests* with *python -m unittest*

## [1.5.1] -- 2018-03-04

### Added
- [RFC-6839] content suffix support in `datastructures.ContentType` and
  `headers.parse_content_type()`

## [1.5.0] -- 2017-12-24

### Deprecated
- the `normalized_parameter_values` keyword parameter to the
  `headers._parse_parameter_list` function

### Added
- `normalize_parameter_names` keyword parameter to the
  `headers._parse_parameter_list` function. This replaces the
  `normalized_parameter_values` keyword parameter.
- support for parsing [HTTP-Forwarded] headers with `headers.parse_forwarded`
- `algorithms.remove_url_auth` function


### Removed
- support for Python 2.6 and 3.3

### Changed
- `headers.parse_accept()` now prefers *explicit* highest quality preferences
  over the *inferred* highest quality preferences

## [1.4.3] -- (2017-10-30)

### Changed
The parsing of qualified lists now retains the initial ordering whenever
possible. The algoritm prefers explicit highest quality preferences (1.0)
over inferred highest quality preferences. It also retains the initial
ordering in the presense of multiple highest quality matches. This affects
the `headers.parse_accept_charset`, `headers.parse_accept_encoding` and
`headers.parse_accept_language` functions.

## [1.4.2] -- (2017-07-04)

### Added
- formatting of [HTTP-Link] headers using `str(header)`

## [1.4.1] -- (2017-04-03)

### Added
- error handling documentation for header parsing functions

## [1.4.0] -- (2016-10-18)

### Added
- `headers.parse_accept_encoding` which parse the [HTTP-Accept-Encoding] header
- `headers.parse_accept_language` which parses the [HTTP-Accept-Language] header

### Fixed
- parsing of parameter lists values ending in a quote character. For example,
  `max-age=5, x-foo="prune"` was parsed as `['max-age=5', 'x-foo="prune']`

## [1.3.0] -- (2016-08-11)

### Added
- [HTTP-Cache-Control] header parsing with `headers.parse_cache_control`

### Deprecated
- `headers.parse_http_accept_header` renamed to `headers.parse_accept`
- `headers.parse_link_header` renamed to `headers.parse_link`
- `headers.parse_list_header` renamed to `headers.parse_list`

## [1.2.2] -- (2015-05-27)

### Added
- `headers.parse_list_header` which parses generic comma-separated
  list headers with support for quoted parts
- `headers.parse_accept_charset` which parses the [HTTP-Accept-Charset]
  header into a sorted list

## [1.2.1] -- (2015-05-25)

### Fixed
`algorithms.select_content_type` only worked with the augmented
`datastructures.ContentType` values returned from the
`algorithms.parse_http_accept_header`. IOW, the algorithm required
that the quality attribute existed on instances. [RFC-9110-section-12.4.2]
requires that missing quality values are treated as `1`

## [1.2.0] -- (2015-04-19)

### Added
- `headers.parse_link_header` which parses [HTTP-Link] headers.
- `datastructures.LinkHeader` class

## [1.1.1] -- (2015-02-10)

### Removed
- the `setupext` module since it was causing problems with source
  distributions

## [1.1.0] -- (2014-10-26)

### Added
- `algorithms.rewrite_url` function

## [1.0.0] -- (2014-09-21)
Initial implementation containing the following functionality:
- `algorithms.select_content_type` function
- `datastructures.ContentType` class
- `errors.NoMatch` class
- `errors.RootException` class
- `headers.parse_content_type` function
- `headers.parse_http_accept_header` function

[yarl]: https://yarl.aio-libs.org/en/stable/

[1.0.0]: https://github.com/dave-shawley/ietfparse/tags/1.0.0
[1.1.0]: https://github.com/dave-shawley/ietfparse/compare/1.0.0...1.1.0
[1.1.1]: https://github.com/dave-shawley/ietfparse/compare/1.1.0...1.1.1
[1.2.0]: https://github.com/dave-shawley/ietfparse/compare/1.1.1...1.2.0
[1.2.1]: https://github.com/dave-shawley/ietfparse/compare/1.2.0...1.2.1
[1.2.2]: https://github.com/dave-shawley/ietfparse/compare/1.2.1...1.2.2
[1.3.0]: https://github.com/dave-shawley/ietfparse/compare/1.2.2...1.3.0
[1.4.0]: https://github.com/dave-shawley/ietfparse/compare/1.3.0...1.4.0
[1.4.1]: https://github.com/dave-shawley/ietfparse/compare/1.4.0...1.4.1
[1.4.2]: https://github.com/dave-shawley/ietfparse/compare/1.4.1...1.4.2
[1.4.3]: https://github.com/dave-shawley/ietfparse/compare/1.4.2...1.4.3
[1.5.0]: https://github.com/dave-shawley/ietfparse/compare/1.4.3...1.5.0
[1.5.1]: https://github.com/dave-shawley/ietfparse/compare/1.5.0...1.5.1
[1.6.0]: https://github.com/dave-shawley/ietfparse/compare/1.5.1...1.6.0
[1.6.1]: https://github.com/dave-shawley/ietfparse/compare/1.6.0...1.6.1
[1.7.0]: https://github.com/dave-shawley/ietfparse/compare/1.6.1...1.7.0
[1.8.0]: https://github.com/dave-shawley/ietfparse/compare/1.7.0...1.8.0
[1.9.0]: https://github.com/dave-shawley/ietfparse/compare/1.8.0...1.9.0
[Unreleased]: https://github.com/dave-shawley/ietfparse/compare/1.9.0...master
