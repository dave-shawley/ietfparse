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

    def test_host_is_idn_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com',
                                   host=u'dollars-and-\u00a2s.com').lower(),
            'http://xn--dollars-and-s-7na.com'
        )

    def test_label_longer_than_63_characters_is_rejected(self):
        # encoded form would be 'xn--' + ('a' * 56) + '-nub' which
        # is 64 characters long
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('http://example.com',
                                   host=u'\u00a2{0}'.format('a' * 56))

    def test_port_is_retained(self):
        self.assertEqual(algorithms.rewrite_url('http://example.com:8080',
                                                host='other.com'),
                         'http://other.com:8080')

    def test_long_hosts_are_rejected(self):
        long_host_name = '{0}.{1}.{2}.{3}.com'.format(
            'a' * 63, 'b' * 63, 'c' * 63, 'd' * 63)
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('http://example.com', host=long_host_name)

    def test_long_host_names_can_be_enabled(self):
        long_host_name = '{0}.{1}.{2}.{3}.com'.format(
            'a' * 63, 'b' * 63, 'c' * 63, 'd' * 63)
        self.assertEqual(
            algorithms.rewrite_url('http://example.com',
                                   host=long_host_name,
                                   enable_long_host=True),
            'http://{0}'.format(long_host_name)
        )

    def test_long_labels_are_always_rejected(self):
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('http://example.com',
                                   host='{0}.com'.format('a' * 64),
                                   enable_long_host=True)

    def test_that_user_portion_is_not_idna_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url(u'http://user:pass@example.com',
                                   host=u'h\u00F8st'),
            'http://user:pass@xn--hst-0na',
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


class WhenReplacingThePathPortion(unittest.TestCase):

    def test_path_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com/path', path='new-path'),
            'http://example.com/new-path')

    def test_path_equal_none_removes_path(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com/path', path=None),
            'http://example.com/')

    def test_path_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com/path', path='new path'),
            'http://example.com/new%20path')

    def test_path_containing_slashes_is_not_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com/path', path='new/path'),
            'http://example.com/new/path')

    def test_unicode_replace_characters_are_encoded_in_utf8(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com/path',
                                   path=u'\u2115ew/\u2119ath').lower(),
            'http://example.com/%e2%84%95ew/%e2%84%99ath',
        )

    def test_empty_path_replaced_properly(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com?q=value', path='foo'),
            'http://example.com/foo?q=value')

    def test_path_with_question_mark_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com?q=value',
                                   path='?').lower(),
            'http://example.com/%3f?q=value',
        )
