import unittest

from ietfparse import headers


class CacheControlParsingTests(unittest.TestCase):
    def test_that_flags_are_parsed_as_booleans(self):
        flags = {
            'must-revalidate', 'no-cache', 'no-store', 'no-transform',
            'only-if-cached', 'public', 'private', 'proxy-revalidate'
        }
        for flag in flags:
            parsed = headers.parse_cache_control(flag)
            self.assertIs(parsed[flag], True)

    def test_that_numeric_parameters_are_parsed(self):
        parsed = headers.parse_cache_control('min-fresh=20, max-age=100')
        self.assertEqual(100, parsed['max-age'])
        self.assertEqual(20, parsed['min-fresh'])

    def test_that_string_parameters_are_parsed(self):
        parsed = headers.parse_cache_control(
            'community="UCI", x-token=" foo bar "')
        self.assertEqual('UCI', parsed['community'])
        self.assertEqual(' foo bar ', parsed['x-token'])

    def test_that_empty_parameter_values_are_ignored(self):
        parsed = headers.parse_cache_control('x-should-be-ignored=')
        self.assertNotIn('x-should-be-ignored', parsed)
