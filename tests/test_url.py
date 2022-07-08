from __future__ import unicode_literals

import unittest

from ietfparse import algorithms


class RewriteUrlHostTests(unittest.TestCase):
    def test_host_name_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com/docs',
                                   host='www.example.com'),
            'https://www.example.com/docs')

    def test_host_equal_none_removes_host(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com/docs', host=None),
            'https:///docs')

    def test_host_equal_none_removes_port(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com:80/docs', host=None),
            'https:///docs')

    def test_host_is_idn_encoded_when_appropriate(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com',
                                   host='dollars-and-\u00a2s.com'),
            'https://xn--dollars-and-s-7na.com')

    def test_label_longer_than_63_characters_is_rejected(self):
        # encoded form would be 'xn--' + ('a' * 56) + '-nub' which
        # is 64 characters long
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('https://example.com',
                                   host='\u00a2{0}'.format('a' * 56))

    def test_port_is_retained(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com:8080',
                                   host='other.com'), 'https://other.com:8080')

    def test_long_hosts_are_rejected(self):
        long_host_name = '{0}.{1}.{2}.{3}.com'.format('a' * 63, 'b' * 63,
                                                      'c' * 63, 'd' * 63)
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('https://example.com', host=long_host_name)

    def test_long_host_names_can_be_enabled(self):
        long_host_name = '{0}.{1}.{2}.{3}.com'.format('a' * 63, 'b' * 63,
                                                      'c' * 63, 'd' * 63)
        self.assertEqual(
            algorithms.rewrite_url('https://example.com',
                                   host=long_host_name,
                                   enable_long_host=True),
            'https://{0}'.format(long_host_name))

    def test_long_labels_are_always_rejected(self):
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('https://example.com',
                                   host='{0}.com'.format('a' * 64),
                                   enable_long_host=True)

    def test_that_user_portion_is_not_idna_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user:pass@example.com',
                                   host='h\u00F8st'),
            'https://user:pass@xn--hst-0na',
        )

    def test_that_non_idna_schemes_are_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('blah://example.com',
                                   host='dollars-and-\u00a2s.com'),
            'blah://dollars-and-%C2%A2s.com',
        )

    def test_that_idna_encoding_can_be_required(self):
        self.assertEqual(
            algorithms.rewrite_url('blah://example.com',
                                   host='dollars-and-\u00a2s.com',
                                   encode_with_idna=True),
            'blah://xn--dollars-and-s-7na.com',
        )

    def test_that_idna_encoding_can_be_prohibited(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com',
                                   host='dollars-and-\u00a2s.com',
                                   encode_with_idna=False),
            'https://dollars-and-%C2%A2s.com',
        )

    def test_that_ipv6_literals_are_not_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://foo.com',
                                   host='[2600:807:320:202:8800::c77]'),
            'https://[2600:807:320:202:8800::c77]',
        )

    def test_that_non_idna_hosts_pass_through_allowed_characters(self):
        self.assertEqual(
            algorithms.rewrite_url('blah://path', host="!($&')*+~,;=)"),
            "blah://!($&')*+~,;=)",
        )


class RewriteUrlPortTests(unittest.TestCase):
    def test_port_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com:443', port=80),
            'https://example.com:80')

    def test_non_integer_port_is_rejected(self):
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('https://example.com', port='blah')

    def test_negative_port_is_rejected(self):
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('https://example.com', port=-1)

    def test_port_is_ignored_without_host(self):
        self.assertEqual(
            algorithms.rewrite_url('https:///etc/passwd', port=80),
            'https:///etc/passwd')

    def test_port_equal_none_removes_port(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com:443', port=None),
            'https://example.com')


class RewriteUrlPathTests(unittest.TestCase):
    def test_path_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com/path',
                                   path='new-path'),
            'https://example.com/new-path')

    def test_path_equal_none_removes_path(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com/path', path=None),
            'https://example.com/')

    def test_path_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com/path',
                                   path='new path'),
            'https://example.com/new%20path')

    def test_path_containing_slashes_is_not_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com/path',
                                   path='new/path'),
            'https://example.com/new/path')

    def test_unicode_replace_characters_are_encoded_in_utf8(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com/path',
                                   path='\u2115ew/\u2119ath').lower(),
            'https://example.com/%e2%84%95ew/%e2%84%99ath',
        )

    def test_empty_path_replaced_properly(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com?q=value', path='foo'),
            'https://example.com/foo?q=value')

    def test_path_with_question_mark_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://example.com?q=value',
                                   path='?').lower(),
            'https://example.com/%3f?q=value',
        )


class RewriteUrlQueryTests(unittest.TestCase):
    def test_query_string_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('https://host/path?foo=bar', query='1=2'),
            'https://host/path?1=2',
        )

    def test_query_string_is_not_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url(
                'https://host/path',
                query='redirect=https://example.com&q=foo? bar'),
            'https://host/path?redirect=https://example.com&q=foo? bar',
        )

    def test_query_of_none_removes_query(self):
        self.assertEqual(
            algorithms.rewrite_url('https://host/path?foo=bar', query=None),
            'https://host/path',
        )

    def test_mapping_query_is_encoded_with_ampersands(self):
        self.assertEqual(
            algorithms.rewrite_url('https://host?foo=bar',
                                   query={
                                       'first': 1,
                                       'last': 2
                                   }), 'https://host?first=1&last=2')

    def test_list_query_is_encoded_with_ampersands(self):
        self.assertEqual(
            algorithms.rewrite_url('https://host?foo=bar',
                                   query=[('superior', 1), ('inferior', 2)]),
            'https://host?superior=1&inferior=2')

    def test_that_nonascii_is_percent_encoded_as_utf8(self):
        self.assertEqual(
            algorithms.rewrite_url('https://host', query={'len': '23\xB5'}),
            'https://host?len=23%C2%B5',
        )


class RewriteUrlUserTests(unittest.TestCase):
    def test_that_user_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user1@host', user='user2'),
            'https://user2@host',
        )

    def test_that_user_does_not_replace_password(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user:pass@host', user='user2'),
            'https://user2:pass@host',
        )

    def test_that_setting_user_to_none_removes_user(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user@host', user=None),
            'https://host',
        )

    def test_that_setting_user_to_none_remove_password(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user:pass@host', user=None),
            'https://host',
        )

    def test_that_user_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://host', user='\u00BDuser'),
            'https://%C2%BDuser@host',
        )

    def test_that_quoted_password_is_retained(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user:%E2%88%85@host', user='me'),
            'https://me:%E2%88%85@host',
        )

    def test_that_acceptable_characters_are_not_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://foo', user="~!&$'()+*,=:;"),
            "https://~!&$'()+*,=:;@foo",
        )


class RewriteUrlPasswordTests(unittest.TestCase):
    def test_that_password_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user:pass@host', password='PASS'),
            'https://user:PASS@host',
        )

    def test_that_setting_password_to_none_removes_password(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user:pass@host', password=None),
            'https://user@host',
        )

    def test_that_password_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://user@host', password='\u2205'),
            'https://user:%E2%88%85@host',
        )

    def test_that_quoted_user_is_retained(self):
        self.assertEqual(
            algorithms.rewrite_url('https://%C2%BD:pass@host', password=None),
            'https://%C2%BD@host',
        )

    def test_that_acceptable_characters_are_not_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://foo@foo',
                                   password="~!&$'()+*,=:;"),
            "https://foo:~!&$'()+*,=:;@foo",
        )


class RewriteUrlSchemeTests(unittest.TestCase):
    def test_that_scheme_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com', scheme='https'),
            'https://example.com',
        )

    def test_that_setting_scheme_to_none_removes_it(self):
        self.assertEqual(algorithms.rewrite_url('https://host', scheme=None),
                         '//host')

    def test_that_clearing_scheme_on_idn_url_does_not_change_host(self):
        self.assertEqual(
            algorithms.rewrite_url('https://xn--dollars-and-s-7na.com',
                                   scheme=None),
            '//xn--dollars-and-s-7na.com',
        )

    def test_that_changing_scheme_and_host_honors_idna_logic(self):
        self.assertEqual(
            algorithms.rewrite_url('https://xn--dollars-and-s-7na.com',
                                   scheme='blah',
                                   host='just-\u20ac-now'),
            'blah://just-%E2%82%AC-now',
        )
        self.assertEqual(
            algorithms.rewrite_url('blah://dollars-and-\u00a2s.com',
                                   scheme='https',
                                   host='just-\u20ac-now'),
            'https://xn--just--now-ki1e',
        )
        self.assertEqual(
            algorithms.rewrite_url('https://xn--dollars-and-s-7na.com',
                                   scheme='blah',
                                   host='just-\u20ac-now',
                                   encode_with_idna=True),
            'blah://xn--just--now-ki1e',
        )
        self.assertEqual(
            algorithms.rewrite_url('blah://dollars-and-\u00a2s.com',
                                   scheme='https',
                                   host='just-\u20ac-now',
                                   encode_with_idna=False),
            'https://just-%E2%82%AC-now',
        )


class RewriteUrlFragmentTests(unittest.TestCase):
    def test_that_fragment_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('https://foo#fragment', fragment='boom'),
            'https://foo#boom',
        )

    def test_that_setting_fragment_to_none_removes_it(self):
        self.assertEqual(
            algorithms.rewrite_url('https://foo#fragment', fragment=None),
            'https://foo',
        )

    def test_that_fragment_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('https://foo', fragment='/\u2620?'),
            'https://foo#/%E2%98%A0?',
        )
