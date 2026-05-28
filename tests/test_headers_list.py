import unittest

from ietfparse import errors, headers


class ListHeaderParsingTests(unittest.TestCase):
    def test_that_elements_are_whitespace_normalized(self) -> None:
        self.assertEqual(
            headers.parse_list('one, two,three    ,four,five'),
            ['one', 'two', 'three', 'four', 'five'],
        )

    def test_that_quotes_are_removed(self) -> None:
        self.assertEqual(
            headers.parse_list('"quoted value"'), ['quoted value']
        )

    def test_that_quoted_commas_are_retained(self) -> None:
        self.assertEqual(
            headers.parse_list('first, "comma ->,<- here", last'),
            ['first', 'comma ->,<- here', 'last'],
        )

    def test_that_quoted_parameters_are_not_disturbed(self) -> None:
        self.assertEqual(
            headers.parse_list('max-age=5, x-foo="prune"'),
            ['max-age=5', 'x-foo="prune"'],
        )

    def test_that_escaped_quotes_do_not_end_quoted_list_items(self) -> None:
        self.assertEqual(
            headers.parse_list('first, "a\\"b,c", last'),
            ['first', 'a"b,c', 'last'],
        )

    def test_that_trailing_empty_items_are_preserved(self) -> None:
        self.assertEqual(headers.parse_list('first,'), ['first', ''])

    def test_that_quoted_items_with_missing_delimiters_are_rejected(
        self,
    ) -> None:
        with self.assertRaises(errors.MalformedListSegment) as raised:
            headers.parse_list(
                'token, "space separated", "incorrect" "quoted"'
            )
        self.assertEqual(raised.exception.segment, '"incorrect" "quoted"')

    def test_that_malformed_quoted_items_raise_public_list_errors(
        self,
    ) -> None:
        with self.assertRaises(errors.MalformedListSegment) as raised:
            headers.parse_list('token, "unterminated')
        self.assertEqual(raised.exception.segment, 'token, "unterminated')
