import unittest

from ietfparse import headers


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
