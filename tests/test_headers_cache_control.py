import unittest

from ietfparse import headers


class CacheControlParsingTests(unittest.TestCase):
    def test_that_flags_are_parsed_as_booleans(self) -> None:
        flags = {
            'must-revalidate',
            'no-cache',
            'no-store',
            'no-transform',
            'only-if-cached',
            'public',
            'private',
            'proxy-revalidate',
        }
        for flag in flags:
            parsed = headers.parse_cache_control(flag)
            self.assertIs(parsed[flag], True)  # noqa: FBT003

    def test_that_numeric_parameters_are_parsed(self) -> None:
        parsed = headers.parse_cache_control('min-fresh=20, max-age=100')
        self.assertEqual(parsed['max-age'], 100)
        self.assertEqual(parsed['min-fresh'], 20)

    def test_that_string_parameters_are_parsed(self) -> None:
        parsed = headers.parse_cache_control(
            'community="UCI", x-token=" foo bar "'
        )
        self.assertEqual(parsed['community'], 'UCI')
        self.assertEqual(parsed['x-token'], ' foo bar ')

    def test_that_escaped_quotes_do_not_split_quoted_directive_values(
        self,
    ) -> None:
        parsed = headers.parse_cache_control('x-token="a\\"b,c"')
        self.assertEqual(parsed['x-token'], 'a\\"b,c')

    def test_that_empty_parameter_values_are_ignored(self) -> None:
        parsed = headers.parse_cache_control('x-should-be-ignored=')
        self.assertNotIn('x-should-be-ignored', parsed)

    def test_that_trailing_empty_items_are_ignored(self) -> None:
        self.assertEqual(
            headers.parse_cache_control('max-age=100,'),
            {'max-age': 100},
        )

    def test_parsing_leniency(self) -> None:
        self.assertEqual(
            headers.parse_cache_control(',,'),
            {},
        )
        self.assertEqual(
            headers.parse_cache_control('""'),
            {},
        )
        self.assertEqual(
            headers.parse_cache_control('="",max-age=100'),
            {'max-age': 100},
        )
