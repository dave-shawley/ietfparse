import unittest

from fluenttest import test_case

from ietfparse import headers


class WhenParsingCacheControl(test_case.TestCase, unittest.TestCase):

    @classmethod
    def act(cls):
        cls.parsed = headers.parse_cache_control(
            'public, must-revalidate, max-age=100, min-fresh=20, '
            'community="UCI", x-token=" foo bar "')

    def test_that_public_is_parsed(self):
        print(self.parsed)
        self.assertTrue(self.parsed.get('public'))

    def test_that_must_revalidate_is_parsed(self):
        self.assertTrue(self.parsed.get('must-revalidate'))

    def test_that_private_is_not_set(self):
        self.assertNotIn('private', self.parsed)

    def test_that_max_age_is_set(self):
        self.assertEqual(self.parsed.get('max-age'), 100)

    def test_that_min_fresh_is_set(self):
        self.assertEqual(self.parsed.get('min-fresh'), 20)

    def test_that_community_is_set(self):
        self.assertEqual(self.parsed.get('community'), 'UCI')

    def test_that_extension_parameter_is_parsed(self):
        self.assertEqual(self.parsed.get('x-token'), ' foo bar ')
