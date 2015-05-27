import unittest

from ietfparse import headers


class WhenParsingListHeader(unittest.TestCase):

    def test_that_elements_are_whitespace_normalized(self):
        self.assertEqual(
            headers.parse_list_header('one, two,three    ,four,five'),
            ['one', 'two', 'three', 'four', 'five'])

    def test_that_quotes_are_removed(self):
        self.assertEqual(headers.parse_list_header('"quoted value"'),
                         ['quoted value'])

    def test_that_quoted_commas_are_retained(self):
        self.assertEqual(
            headers.parse_list_header('first, "comma ->,<- here", last'),
            ['first', 'comma ->,<- here', 'last'])
