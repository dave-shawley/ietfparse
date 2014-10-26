from __future__ import unicode_literals

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

    def test_host_is_idn_encoded_when_appropriate(self):
        self.assertEqual(
            algorithms.rewrite_url('http://example.com',
                                   host='dollars-and-\u00a2s.com'),
            'http://xn--dollars-and-s-7na.com'
        )

    def test_label_longer_than_63_characters_is_rejected(self):
        # encoded form would be 'xn--' + ('a' * 56) + '-nub' which
        # is 64 characters long
        with self.assertRaises(ValueError):
            algorithms.rewrite_url('http://example.com',
                                   host='\u00a2{0}'.format('a' * 56))

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
            algorithms.rewrite_url('http://user:pass@example.com',
                                   host='h\u00F8st'),
            'http://user:pass@xn--hst-0na',
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
            algorithms.rewrite_url('http://example.com',
                                   host='dollars-and-\u00a2s.com',
                                   encode_with_idna=False),
            'http://dollars-and-%C2%A2s.com',
        )

    def test_that_ipv6_literals_are_not_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://foo.com',
                                   host='[2600:807:320:202:8800::c77]'),
            'http://[2600:807:320:202:8800::c77]',
        )

    def test_that_non_idna_hosts_pass_through_allowed_characters(self):
        self.assertEqual(
            algorithms.rewrite_url('blah://path', host="!($&')*+~,;=)"),
            "blah://!($&')*+~,;=)",
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
                                   path='\u2115ew/\u2119ath').lower(),
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
            algorithms.rewrite_url('http://host', query={'len': '23\xB5'}),
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
            algorithms.rewrite_url('http://host', user='\u00BDuser'),
            'http://%C2%BDuser@host',
        )

    def test_that_quoted_password_is_retained(self):
        self.assertEqual(
            algorithms.rewrite_url('http://user:%E2%88%85@host', user='me'),
            'http://me:%E2%88%85@host',
        )

    def test_that_acceptable_characters_are_not_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://foo', user="~!&$'()+*,=:;"),
            "http://~!&$'()+*,=:;@foo",
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
            algorithms.rewrite_url('http://user@host', password='\u2205'),
            'http://user:%E2%88%85@host',
        )

    def test_that_quoted_user_is_retained(self):
        self.assertEqual(
            algorithms.rewrite_url('http://%C2%BD:pass@host', password=None),
            'http://%C2%BD@host',
        )

    def test_that_acceptable_characters_are_not_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://foo@foo', password="~!&$'()+*,=:;"),
            "http://foo:~!&$'()+*,=:;@foo",
        )


class WhenReplacingTheScheme(unittest.TestCase):

    def test_that_scheme_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host', scheme='https'),
            'https://host',
        )

    def test_that_setting_scheme_to_none_removes_it(self):
        self.assertEqual(
            algorithms.rewrite_url('http://host', scheme=None), '//host')

    def test_that_clearing_scheme_on_idn_url_does_not_change_host(self):
        self.assertEqual(
            algorithms.rewrite_url('http://xn--dollars-and-s-7na.com',
                                   scheme=None),
            '//xn--dollars-and-s-7na.com',
        )

    def test_that_changing_scheme_and_host_honors_idna_logic(self):
        self.assertEqual(
            algorithms.rewrite_url('http://xn--dollars-and-s-7na.com',
                                   scheme='blah', host='just-\u20ac-now'),
            'blah://just-%E2%82%AC-now',
        )
        self.assertEqual(
            algorithms.rewrite_url('blah://dollars-and-\u00a2s.com',
                                   scheme='http', host='just-\u20ac-now'),
            'http://xn--just--now-ki1e',
        )
        self.assertEqual(
            algorithms.rewrite_url('http://xn--dollars-and-s-7na.com',
                                   scheme='blah', host='just-\u20ac-now',
                                   encode_with_idna=True),
            'blah://xn--just--now-ki1e',
        )
        self.assertEqual(
            algorithms.rewrite_url('blah://dollars-and-\u00a2s.com',
                                   scheme='http', host='just-\u20ac-now',
                                   encode_with_idna=False),
            'http://just-%E2%82%AC-now',
        )


class WhenReplacingTheFragment(unittest.TestCase):

    def test_that_fragment_is_replaced(self):
        self.assertEqual(
            algorithms.rewrite_url('http://foo#fragment', fragment='boom'),
            'http://foo#boom',
        )

    def test_that_setting_fragment_to_none_removes_it(self):
        self.assertEqual(
            algorithms.rewrite_url('http://foo#fragment', fragment=None),
            'http://foo',
        )

    def test_that_fragment_is_percent_encoded(self):
        self.assertEqual(
            algorithms.rewrite_url('http://foo', fragment='/\u2620?'),
            'http://foo#/%E2%98%A0?',
        )
