import random
import unittest

from ietfparse import algorithms


class WhenReplacingTheHostPortion(unittest.TestCase):

    def test_host_name_is_replaced(self):
        self.assertEqual(algorithms.rewrite_url('http://example.com/docs',
                                                host='www.example.com'),
                         'http://www.example.com/docs')

    def test_host_equal_none_removes_host(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com/docs', host=None),
            'http:///docs')

    def test_host_equal_none_removes_port(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com:80/docs', host=None),
            'http:///docs')

    def test_host_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com',
                                   host=u'dollars-and-\u00a2s.com').lower(),
            'http://dollars-and-%c2%a2s.com'
        )

    def test_host_longer_than_255_characters_is_rejected(self):
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('http://example.com',
                                   host=u'\u00a2{0}'.format('a' * 250))

    def test_port_is_retained(self):
        self.assertEqual(algorithms.rewrite_url('http://example.com:8080',
                                                host='other.com'),
                         'http://other.com:8080')

    def test_long_host_names_can_be_enabled(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com',
                                   host='a' * 512, enable_long_host=True),
            'http://{0}'.format('a' * 512)
        )


class WhenReplacingThePortPortion(unittest.TestCase):

    def test_port_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com:443', port=80),
            'http://example.com:80')

    def test_non_integer_port_is_rejected(self):
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('http://example.com', port='blah')

    def test_negative_port_is_rejected(self):
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('http://example.com', port=-1)

    def test_port_is_ignored_without_host(self):
        self.assertEqual(
            algorithms.rewrite_url('http:///etc/passwd', port=80),
            'http:///etc/passwd')

    def test_port_equal_none_removes_port(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com:443', port=None),
            'http://example.com')
