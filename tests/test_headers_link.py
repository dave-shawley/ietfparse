import contextlib
import typing
import unittest
from collections import abc

from ietfparse import datastructures, errors, headers


class LinkHeaderParsingTests(unittest.TestCase):
    def test_parsing_single_link(self) -> None:
        parsed = headers.parse_link(
            '<https://example.com/TheBook/chapter2>; rel="previous"; '
            'title="previous chapter"'
        )

        self.assertEqual(len(parsed), 1)
        self.assertEqual(
            parsed[0].target, 'https://example.com/TheBook/chapter2'
        )
        self.assertIn(('rel', 'previous'), parsed[0].parameters)
        self.assertIn(('title', 'previous chapter'), parsed[0].parameters)

    def test_parsing_multiple_link_headers(self) -> None:
        parsed = headers.parse_link(
            '<https://example.com/first>; rel=first;another=value,'
            '<https://example.com/second>'
        )
        self.assertEqual(parsed[0].target, 'https://example.com/first')
        self.assertEqual(
            parsed[0].parameters, [('rel', 'first'), ('another', 'value')]
        )

        self.assertEqual(parsed[1].target, 'https://example.com/second')
        self.assertEqual(parsed[1].parameters, [])

    def test_that_quoted_uris_can_contain_semicolons(self) -> None:
        parsed = headers.parse_link('<https://host/matrix;param/>')
        self.assertEqual(parsed[0].target, 'https://host/matrix;param/')

    def test_that_quoted_parameters_can_contain_commas(self) -> None:
        parsed = headers.parse_link(
            '<https://example/com>; rel="quoted, with comma", <1>'
        )
        self.assertEqual(parsed[0].parameters, [('rel', 'quoted, with comma')])

    def test_that_quoted_parameters_can_contain_semicolons(self) -> None:
        parsed = headers.parse_link(
            '<https://example/com>; rel="quoted; with semicolon", <1>'
        )
        self.assertEqual(
            parsed[0].parameters, [('rel', 'quoted; with semicolon')]
        )

    def test_that_title_star_overrides_title_parameter(self) -> None:
        parsed = headers.parse_link('<>; title=title; title*=title*')
        self.assertEqual(
            parsed[0].parameters, [('title*', 'title*'), ('title', 'title*')]
        )

    def test_optional_white_space(self) -> None:
        parsed = headers.parse_link('<one> ; rel="one" , <two> ; rel=two')
        self.assertEqual(2, len(parsed))
        self.assertEqual('one', dict(parsed[0].parameters)['rel'])
        self.assertEqual('two', dict(parsed[1].parameters)['rel'])

    def test_bad_white_space(self) -> None:
        parsed = headers.parse_link('<one>; rel = "one", <two>; rel = two')
        self.assertEqual(2, len(parsed))

        self.assertEqual('one', dict(parsed[0].parameters)['rel'])
        self.assertEqual('<one>; rel="one"', str(parsed[0]))

        self.assertEqual('two', dict(parsed[1].parameters)['rel'])
        self.assertEqual('<two>; rel="two"', str(parsed[1]))

    def test_indexed_access(self) -> None:
        parsed = headers.parse_link(
            '<>; rel=one; single=one; double=two; double="three"'
        )
        self.assertEqual(1, len(parsed))
        link = parsed[0]
        self.assertEqual(link['rel'], ['one'])
        self.assertEqual(link['single'], ['one'])
        self.assertEqual(link['double'], ['two', 'three'])
        self.assertEqual(link['missing'], [])

    def test_containment_check(self) -> None:
        parsed = headers.parse_link('<>; rel=one')
        self.assertEqual(1, len(parsed))

        # ensure that these work as well... they will never
        # return in the naive implementation of __getitem__
        link = parsed[0]
        self.assertIn('rel', link)
        self.assertNotIn('missing', link)


class MalformedLinkHeaderTests(unittest.TestCase):
    def test_that_value_error_when_url_brackets_are_missing(self) -> None:
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('https://example.com; rel=wrong')

    def test_that_first_semicolon_is_required(self) -> None:
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('<https://example.com> rel="still wrong"')

    def test_that_first_rel_parameter_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC-8288 sec. 3.3
        parsed = headers.parse_link('<>; rel=first; rel=ignored')
        self.assertIn(('rel', 'first'), parsed[0].parameters)
        self.assertNotIn(('rel', 'ignored'), parsed[0].parameters)
        self.assertEqual('first', parsed[0].rel)

    def test_that_first_media_parameters_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC-8288 sec. 3.4.1
        parsed = headers.parse_link('<>; media=first; media=ignored')
        self.assertIn(('media', 'first'), parsed[0].parameters)
        self.assertNotIn(('media', 'ignored'), parsed[0].parameters)

    def test_that_first_title_parameter_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC-8288 sec. 3.4.1
        parsed = headers.parse_link('<>; title=first; title=ignored')
        self.assertIn(('title', 'first'), parsed[0].parameters)
        self.assertNotIn(('title', 'ignored'), parsed[0].parameters)

    def test_that_first_title_star_parameter_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC-8288 sec. 3.4.1
        parsed = headers.parse_link('<>; title*=first; title*=ignored')
        self.assertIn(('title*', 'first'), parsed[0].parameters)
        self.assertNotIn(('title*', 'ignored'), parsed[0].parameters)

    def test_that_the_first_type_parameters_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC-8288 sec. 3.4.1
        parsed = headers.parse_link('<>; type=first; type=ignored')
        self.assertIn(('type', 'first'), parsed[0].parameters)
        self.assertNotIn(('type', 'ignored'), parsed[0].parameters)

    def test_that_semantic_tests_can_be_turned_off(self) -> None:
        parsed = headers.parse_link(
            '<multiple-titles>;title=one;title=two;title*=three;title*=four, '
            '<multiple-rels>; rel=first; rel=second,'
            '<multiple-medias>; media=one; media=two',
            strict=False,
        )
        self.assertEqual(len(parsed), 3)
        self.assertEqual(
            parsed[0].parameters,
            [
                ('title', 'one'),
                ('title', 'two'),
                ('title*', 'three'),
                ('title*', 'four'),
            ],
        )
        self.assertEqual(
            parsed[1].parameters, [('rel', 'first'), ('rel', 'second')]
        )
        self.assertEqual(parsed[1].rel, 'first second')
        self.assertEqual(
            parsed[2].parameters, [('media', 'one'), ('media', 'two')]
        )


class LinkHeaderFormattingTests(unittest.TestCase):
    def test_that_parameters_are_sorted_after_rel(self) -> None:
        parsed = headers.parse_link(
            '<https://example.com>; title="foo"; rel="next"; hreflang="en"'
        )
        self.assertEqual(
            str(parsed[0]),
            '<https://example.com>; rel="next"; hreflang="en"; title="foo"',
        )

    def test_that_rel_is_not_required(self) -> None:
        parsed = headers.parse_link('<>')
        self.assertEqual(str(parsed[0]), '<>')
        self.assertEqual(parsed[0].rel, '')

    def test_that_only_first_rel_is_used(self) -> None:
        parsed = headers.parse_link('<>; rel=used; rel=first; rel=one')
        self.assertEqual(str(parsed[0]), '<>; rel="used"')
        self.assertEqual(parsed[0].rel, 'used')

    def test_that_parameters_are_sorted_without_rel(self) -> None:
        parsed = headers.parse_link('<>; title=foo; hreflang="en"')
        self.assertEqual(str(parsed[0]), '<>; hreflang="en"; title="foo"')

    def test_that_rels_are_combined_in_non_strict_mode(self) -> None:
        parsed = headers.parse_link(
            '<>; rel=one; rel=two; rel=three', strict=False
        )
        self.assertEqual(str(parsed[0]), '<>; rel="one two three"')
        self.assertEqual(parsed[0].rel, 'one two three')


class ImmutableSequenceTests(unittest.TestCase):
    def test_that_immutable_sequence_looks_like_sequence(self) -> None:
        seq = ['one', 'two']
        imm_seq = datastructures.ImmutableSequence[str](seq)
        self.assertEqual(repr(imm_seq), repr(seq))
        self.assertEqual(len(imm_seq), len(seq))
        self.assertEqual(bool(imm_seq), bool(seq))
        self.assertEqual(imm_seq, seq)
        for a, b in zip(seq, imm_seq):
            self.assertEqual(a, b)

    def test_modifying_target(self) -> None:
        parsed = headers.parse_link('<>; values=one; values=two')
        self.assertEqual(len(parsed), 1)
        with self.assert_raises_one_of(AttributeError, TypeError):
            parsed[0].target = 'whatever'  # type: ignore[misc]

    def test_modifying_link_parameters(self) -> None:
        parsed = headers.parse_link('<>; values=one; values=two')
        self.assertEqual(len(parsed), 1)
        params = typing.cast(list[tuple[str, str]], parsed[0].parameters)
        with self.assert_raises_one_of(AttributeError, TypeError):
            params.append(('values', 'three'))
        with self.assert_raises_one_of(AttributeError, TypeError):
            params += [('values', 'four')]

    def test_modifying_indexed_result(self) -> None:
        parsed = headers.parse_link('<>; values=one; values=two')
        self.assertEqual(len(parsed), 1)
        params = typing.cast(list[str], parsed[0]['values'])
        with self.assert_raises_one_of(AttributeError, TypeError):
            params.append('three')
        with self.assert_raises_one_of(AttributeError, TypeError):
            params += ['three']
        with self.assert_raises_one_of(AttributeError, TypeError):
            params[0] = 'one'

    def test_modifying_empty_indexed_result(self) -> None:
        parsed = headers.parse_link('<>')
        self.assertEqual(len(parsed), 1)
        params = typing.cast(list[str], parsed[0]['non-existent'])
        with self.assert_raises_one_of(AttributeError, TypeError):
            params.append('value')
        with self.assert_raises_one_of(AttributeError, TypeError):
            params += ['value']

    def test_sequence_expectations(self) -> None:
        parsed = headers.parse_link('<>; param=one; param=two')
        self.assertEqual(len(parsed), 1)
        link = parsed[0]
        self.assertEqual(len(link['param']), 2)
        self.assertEqual(link['param'], ['one', 'two'])
        self.assertEqual(link['param'][0], 'one')
        self.assertEqual(link['param'][:2], ['one', 'two'])
        self.assertEqual(link['param'].count('one'), 1)
        self.assertEqual(link['param'].index('two'), 1)
        self.assertNotEqual(link['param'], object())
        self.assertEqual(list(reversed(link['param'])), ['two', 'one'])

    @contextlib.contextmanager
    def assert_raises_one_of(
        self, *exc_cls: type[Exception]
    ) -> abc.Iterator[None]:
        try:
            yield
        except Exception as exc:
            if isinstance(exc, exc_cls):
                return
            raise
        else:
            self.fail(
                'Exception not raised, expected one of '
                + ', '.join(cls.__name__ for cls in exc_cls)
            )
