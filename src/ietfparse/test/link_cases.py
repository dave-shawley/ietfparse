"""Curated Link header parsing cases for cross-implementation comparisons."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class LinkCase:
    """One Link header sample used for implementation comparisons."""

    case_id: str
    description: str
    sample: str
    strict: bool = True


CASES: tuple[LinkCase, ...] = (
    LinkCase(
        case_id='single-link',
        description='single link with rel and title',
        sample=(
            '<https://example.com/TheBook/chapter2>; rel="previous"; '
            'title="previous chapter"'
        ),
    ),
    LinkCase(
        case_id='multi-link',
        description='multiple link-values with parameters',
        sample=(
            '<https://example.com/first>; rel=first;another=value,'
            '<https://example.com/second>'
        ),
    ),
    LinkCase(
        case_id='target-semicolon',
        description='target containing semicolon',
        sample='<https://host/matrix;param/>',
    ),
    LinkCase(
        case_id='quoted-comma',
        description='quoted parameter containing comma',
        sample='<https://example/com>; rel="quoted, with comma", <1>',
    ),
    LinkCase(
        case_id='quoted-semicolon',
        description='quoted parameter containing semicolon',
        sample='<https://example/com>; rel="quoted; with semicolon", <1>',
    ),
    LinkCase(
        case_id='target-parentheses',
        description='target containing parentheses',
        sample='<https://example.com/foo(bar)>; rel=next',
    ),
    LinkCase(
        case_id='quoted-parentheses',
        description='quoted parameter containing parentheses',
        sample='<>; title="foo(bar)"',
    ),
    LinkCase(
        case_id='escaped-quote',
        description='quoted parameter containing escaped quote and comma',
        sample='<>; title="a\\"b,c"; rel=next, <1>',
    ),
    LinkCase(
        case_id='quoted-equals',
        description='quoted parameter containing equals sign',
        sample='<>; title="a=b"',
    ),
    LinkCase(
        case_id='case-preserving',
        description='parameter values preserve original case',
        sample=(
            '<>; foo="BarBaz"; title="Previous Chapter"; '
            "title*=UTF-8'en'MixedCase"
        ),
    ),
    LinkCase(
        case_id='empty-segment',
        description='empty parameter segment is ignored',
        sample='<>; ; rel=next',
    ),
    LinkCase(
        case_id='valueless-parameter',
        description='valueless parameter is preserved',
        sample='<>; flag',
    ),
    LinkCase(
        case_id='title-star-precedence',
        description='title* overrides title',
        sample='<>; title=title; title*=title*',
    ),
    LinkCase(
        case_id='ows',
        description='optional whitespace around delimiters',
        sample='<one> ; rel="one" , <two> ; rel=two',
    ),
    LinkCase(
        case_id='bws',
        description='bad whitespace around equals',
        sample='<one>; rel = "one", <two>; rel = two',
    ),
    LinkCase(
        case_id='same-rel-multiple-links',
        description='multiple links sharing the same relation',
        sample=(
            '<https://example.com/one>; rel="next", '
            '<https://example.com/two>; rel="next"'
        ),
    ),
    LinkCase(
        case_id='missing-angle-brackets',
        description='missing angle brackets around target',
        sample='https://example.com; rel=wrong',
    ),
    LinkCase(
        case_id='missing-first-semicolon',
        description='missing semicolon before parameters',
        sample='<https://example.com> rel="still wrong"',
    ),
    LinkCase(
        case_id='missing-closing-bracket',
        description='missing closing angle bracket',
        sample='<https://example.com; rel=next',
    ),
    LinkCase(
        case_id='extra-equals',
        description='malformed parameter value with extra equals',
        sample='<>; weird=a=b',
    ),
    LinkCase(
        case_id='missing-parameter-name',
        description='parameter name must not be empty',
        sample='<>; =value',
    ),
    LinkCase(
        case_id='missing-parameter-value',
        description='parameter value required after equals',
        sample='<>; flag=',
    ),
    LinkCase(
        case_id='dangling-escape',
        description='dangling quoted-pair',
        sample='<>; title="value\\',
    ),
    LinkCase(
        case_id='unterminated-quote',
        description='unterminated quoted string',
        sample='<>; title="value',
    ),
    LinkCase(
        case_id='duplicate-rel-strict',
        description='strict mode keeps first rel parameter',
        sample='<>; rel=first; rel=ignored',
    ),
    LinkCase(
        case_id='duplicate-title-strict',
        description='strict mode keeps first title parameter',
        sample='<>; title=first; title=ignored',
    ),
    LinkCase(
        case_id='duplicate-title-star-strict',
        description='strict mode keeps first title* parameter',
        sample='<>; title*=first; title*=ignored',
    ),
    LinkCase(
        case_id='duplicate-media-strict',
        description='strict mode keeps first media parameter',
        sample='<>; media=first; media=ignored',
    ),
    LinkCase(
        case_id='duplicate-type-strict',
        description='strict mode keeps first type parameter',
        sample='<>; type=first; type=ignored',
    ),
    LinkCase(
        case_id='non-strict-semantic-duplicates',
        description='non-strict mode preserves duplicate semantic parameters',
        sample=(
            '<multiple-titles>;title=one;title=two;title*=three;title*=four, '
            '<multiple-rels>; rel=first; rel=second,'
            '<multiple-medias>; media=one; media=two'
        ),
        strict=False,
    ),
)
