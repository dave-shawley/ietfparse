import unittest

from ietfparse import algorithms
from ietfparse.compat import parse


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

    def test_host_is_idn_encoded_when_appropriate(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com',
                                   host=u'dollars-and-\u00a2s.com'),
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

    def test_that_non_idna_schemes_are_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('blah://example.com',
                                   host=u'dollars-and-\u00a2s.com'),
            'blah://dollars-and-%C2%A2s.com',
        )

    def test_that_idna_encoding_can_be_required(self):
        self.assertEqual(
            algorithms.rewrite_url('blah://example.com',
                                   host=u'dollars-and-\u00a2s.com',
                                   encode_with_idna=True),
            'blah://xn--dollars-and-s-7na.com',
        )

    def test_that_idna_encoding_can_be_prohibited(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com',
                                   host=u'dollars-and-\u00a2s.com',
                                   encode_with_idna=False),
            'http://dollars-and-%C2%A2s.com',
        )

    def test_that_ipv6_literals_are_not_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://foo.com',
                                   host='[2600:807:320:202:8800::c77]'),
            'http://[2600:807:320:202:8800::c77]',
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


class WhenReplacingTheQueryPortion(unittest.TestCase):

    def test_query_string_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host/path?foo=bar', query='1=2'),
            'http://host/path?1=2',
        )

    def test_query_string_is_not_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url(
                'http://host/path',
                query='redirect=http://example.com&q=foo? bar'),
            'http://host/path?redirect=http://example.com&q=foo? bar',
        )

    def test_query_of_none_removes_query(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host/path?foo=bar', query=None),
            'http://host/path',
        )

    def test_mapping_query_is_encoded_with_ampersands(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host?foo=bar',
                                   query={'first': 1, 'last': 2}),
            'http://host?first=1&last=2'
        )

    def test_list_query_is_encoded_with_ampersands(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host?foo=bar',
                                   query=[('superior', 1), ('inferior', 2)]),
            'http://host?superior=1&inferior=2'
        )

    def test_that_nonascii_is_percent_encoded_as_utf8(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host', query={'len': u'23\xB5'}),
            'http://host?len=23%C2%B5',
        )


class WhenReplacingUserPortion(unittest.TestCase):

    def test_that_user_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user1@host', user='user2'),
            'http://user2@host',
        )

    def test_that_user_does_not_replace_password(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user:pass@host', user='user2'),
            'http://user2:pass@host',
        )

    def test_that_setting_user_to_none_removes_user(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user@host', user=None),
            'http://host',
        )

    def test_that_setting_user_to_none_remove_password(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user:pass@host', user=None),
            'http://host',
        )

    def test_that_user_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host', user=u'\u00BDuser'),
            'http://%C2%BDuser@host',
        )

    def test_that_quoted_password_is_retained(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user:%E2%88%85@host', user='me'),
            'http://me:%E2%88%85@host',
        )


class WhenReplacingThePasswordPortion(unittest.TestCase):

    def test_that_password_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user:pass@host', password='PASS'),
            'http://user:PASS@host',
        )

    def test_that_setting_password_to_none_removes_password(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user:pass@host', password=None),
            'http://user@host',
        )

    def test_that_password_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user@host', password=u'\u2205'),
            'http://user:%E2%88%85@host',
        )

    def test_that_quoted_user_is_retained(self):
        self.assertEqual(
            algorithms.rewrite_url('http://%C2%BD:pass@host', password=None),
            'http://%C2%BD@host',
        )


class WhenComparingUrls(unittest.TestCase):

    def assertExampleSet(self, *examples):
        for left in examples:
            for right in examples:
                self.assertTrue(
                    algorithms.urls_equal(left, right),
                    '{0} should equal {1}'.format(left, right))

    def test_that_implementation_matches_rfc7230_examples(self):
        self.assertExampleSet(
            'http://example.com:80/~smith/home.html',
            'http://EXAMPLE.com/%7Esmith/home.html',
            'http://EXAMPLE.com:/%7esmith/home.html',
        )

    def test_that_percent_encoded_hosts_match(self):
        self.assertTrue(
            algorithms.urls_equal('http://host', 'http://%48%6F%53%74'))

    def test_that_schemes_are_case_insensitive(self):
        self.assertTrue(algorithms.urls_equal('http://host', 'HTTP://host'))

    def test_that_implementation_matches_rfc2141_examples(self):
        self.assertExampleSet(
            'URN:foo:a123,456',
            'urn:foo:a123,456',
            'urn:FOO:a123,456',
        )
        self.assertExampleSet(
            'urn:foo:a123%2C456',
            'URN:FOO:a123%2c456',
        )


class WhenCanonicalizingAURL(unittest.TestCase):

    def assertUrlCanonicalizedAs(self, input_url, canonicalized_url):
        self.assertEqual(algorithms.canonicalize_url(input_url),
                         canonicalized_url)

    def test_that_scheme_is_lowercased(self):
        self.assertUrlCanonicalizedAs('HTTP://.', 'http://./')

    def test_that_userinfo_is_percent_encoded(self):
        self.assertUrlCanonicalizedAs(
            'http://user::@host', 'http://user:%3A@host/')

    def test_that_host_is_lowercased(self):
        self.assertUrlCanonicalizedAs('http://EXAMPLE', 'http://example/')

    def test_that_default_port_is_stripped(self):
        self.assertUrlCanonicalizedAs('ftp://host:21/foo', 'ftp://host/foo')

    def test_that_host_is_percent_encoded(self):
        self.assertUrlCanonicalizedAs(u'blah://\u00a7', 'blah://%C2%A7')

    def test_that_url_encoding_is_upper_cased(self):
        self.assertUrlCanonicalizedAs('http://%c2%a7', 'http://%C2%A7/')

    def test_that_path_is_normalize(self):
        self.assertUrlCanonicalizedAs(
            'http://host:123/head/skipped/./../tail/./',
            'http://host:123/head/tail/'
        )

    def test_that_empty_path_is_normalized(self):
        self.assertUrlCanonicalizedAs('http://host', 'http://host/')

    # def test_simple_non_hierarchical_url(self):
    #     self.assertUrlCanonicalizedAs(
    #         u'URN:name:Oddbj\u00F8rg:R\u00e5d:Reenskaug:wife',
    #         'urn:name:Oddbj%3C%B8rg:R%C3%A5d:Reenskaug:wife',
    #     )
