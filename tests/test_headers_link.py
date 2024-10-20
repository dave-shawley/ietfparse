import unittest

from ietfparse import errors, headers


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


class MalformedLinkHeaderTests(unittest.TestCase):
    def test_that_value_error_when_url_brackets_are_missing(self) -> None:
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('https://example.com; rel=wrong')

    def test_that_first_semicolon_is_required(self) -> None:
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('<https://example.com> rel="still wrong"')

    def test_that_first_rel_parameter_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC5988 sec. 5.3
        parsed = headers.parse_link('<>; rel=first; rel=ignored')
        self.assertIn(('rel', 'first'), parsed[0].parameters)
        self.assertNotIn(('rel', 'ignored'), parsed[0].parameters)

    def test_that_multiple_media_parameters_are_rejected(self) -> None:
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('<first-link>; media=1; media=2')

    def test_that_first_title_parameter_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC5988 sec. 5.4
        parsed = headers.parse_link('<>; title=first; title=ignored')
        self.assertIn(('title', 'first'), parsed[0].parameters)
        self.assertNotIn(('title', 'ignored'), parsed[0].parameters)

    def test_that_first_title_star_parameter_is_used(self) -> None:
        # semantically malformed but handled appropriately
        # see RFC5988 sec. 5.4
        parsed = headers.parse_link('<>; title*=first; title*=ignored')
        self.assertIn(('title*', 'first'), parsed[0].parameters)
        self.assertNotIn(('title*', 'ignored'), parsed[0].parameters)

    def test_that_multiple_type_parameters_are_rejected(self) -> None:
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('<>; type=1; type=2')

    def test_that_semantic_tests_can_be_turned_off(self) -> None:
        parsed = headers.parse_link(
            '<multiple-titles>;title=one;title=two;title*=three;title*=four, '
            '<multiple-rels>; rel=first; rel=second,'
            '<multiple-medias>; media=one; media=two',
            strict=False,
        )
        self.assertEqual(len(parsed), 3)


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

    def test_that_only_first_rel_is_used(self) -> None:
        parsed = headers.parse_link('<>; rel=used; rel=first; rel=one')
        self.assertEqual(str(parsed[0]), '<>; rel="used"')

    def test_that_parameters_are_sorted_without_rel(self) -> None:
        parsed = headers.parse_link('<>; title=foo; hreflang="en"')
        self.assertEqual(str(parsed[0]), '<>; hreflang="en"; title="foo"')
