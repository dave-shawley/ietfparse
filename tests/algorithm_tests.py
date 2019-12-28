import unittest

from ietfparse import algorithms, errors, headers


class ContentNegotiationTestCase(unittest.TestCase):
    requested = []

    def assertContentTypeMatchedAs(self, expected, *supported, **kwargs):
        selected, matched = algorithms.select_content_type(
            self.requested,
            [headers.parse_content_type(value) for value in supported],
        )
        self.assertEqual(
            selected, headers.parse_content_type(expected),
            '\nExpected to select "{!s}", actual selection was "{!s}"'.format(
                expected,
                selected,
            ))
        if 'matching_pattern' in kwargs:
            self.assertEqual(str(matched), kwargs['matching_pattern'])


class ProactiveContentNegotiationTests(ContentNegotiationTestCase):
    @classmethod
    def setUpClass(cls):
        super(ProactiveContentNegotiationTests, cls).setUpClass()
        cls.requested.extend(
            headers.parse_accept(
                'application/vnd.example.com+json;version=2, '
                'application/vnd.example.com+json;version=1;q=0.9, '
                'application/vnd.example.com+json;version=3;spec=1, '
                'application/vnd.example.com+json;version=3;spec=2, '
                'application/json;q=0.7, '
                'application/*;q=0.6, '
                'text/json;q=0.2, '
                'text/*;q=0.1, '
                'text/javascript;q=0'))

    def test_that_exact_match_is_selected(self):
        self.assertContentTypeMatchedAs('application/json', 'application/json')

    def test_that_exact_match_including_parameters_is_selected(self):
        self.assertContentTypeMatchedAs(
            'application/vnd.example.com+json;version=1',
            'application/vnd.example.com+json;version=1',
        )

    def test_that_differing_parameters_is_acceptable_as_weak_match(self):
        self.assertContentTypeMatchedAs(
            'application/vnd.example.com+json;version=3',
            'application/vnd.example.com+json;version=3',
        )

    def test_that_lower_quality_match_is_preferred_over_weak_match(self):
        self.assertContentTypeMatchedAs(
            'application/json',
            'application/vnd.example.com+json;version=3',
            'application/json',
        )

    def test_that_high_quality_wildcard_match_preferred(self):
        self.assertContentTypeMatchedAs(
            'application/other',
            'text/plain',
            'application/other',
        )

    def test_that_zero_quality_is_not_matched(self):
        with self.assertRaises(errors.NoMatch):
            algorithms.select_content_type(
                self.requested,
                [headers.parse_content_type('text/javascript')],
            )

    def test_that_inappropriate_value_is_not_matched(self):
        with self.assertRaises(errors.NoMatch):
            algorithms.select_content_type(
                self.requested,
                [headers.parse_content_type('image/png')],
            )


class Rfc7231ExampleTests(ContentNegotiationTestCase):
    @classmethod
    def setUpClass(cls):
        super(Rfc7231ExampleTests, cls).setUpClass()
        cls.requested.extend(
            headers.parse_accept(
                'text/*;q=0.3, text/html;q=0.7, text/html;level=1, '
                'text/html;level=2;q=0.4, */*;q=0.5'))

    def test_that_text_html_level_1_matches(self):
        self.assertContentTypeMatchedAs('text/html;level=1',
                                        'text/html;level=1')

    def test_that_text_html_matches(self):
        self.assertContentTypeMatchedAs('text/html', 'text/html')

    def test_that_text_plain_matches_text(self):
        self.assertContentTypeMatchedAs('text/plain',
                                        'text/plain',
                                        matching_pattern='text/*')

    def test_that_image_jpeg_matches_wildcard(self):
        self.assertContentTypeMatchedAs('image/jpeg',
                                        'image/jpeg',
                                        matching_pattern='*/*')

    def test_that_text_html_level_2_matches(self):
        self.assertContentTypeMatchedAs('text/html;level=2',
                                        'text/html;level=2',
                                        matching_pattern='text/html; level=2')

    def test_that_text_html_level_3_matches_text_html(self):
        self.assertContentTypeMatchedAs(
            'text/html;level=3',
            'text/html;level=3',
            matching_pattern='text/html',
        )


class PriorizationTests(unittest.TestCase):
    def test_that_explicit_priority_1_is_preferred(self):
        selected, matched = algorithms.select_content_type(
            headers.parse_accept(
                'application/vnd.com.example+json, '
                'application/vnd.com.example+json;version=1;q=1.0, '
                'application/vnd.com.example+json;version=2'),
            [
                headers.parse_content_type(value)
                for value in ('application/vnd.com.example+json;version=1',
                              'application/vnd.com.example+json;version=2',
                              'application/vnd.com.example+json;version=3')
            ],
        )
        self.assertEqual(str(selected),
                         'application/vnd.com.example+json; version=1')

    def test_that_multiple_matches_result_in_any_appropriate_value(self):
        # note that this also tests that duplicated values are acceptable
        selected, matched = algorithms.select_content_type(
            headers.parse_accept(
                'application/vnd.com.example+json;version=1, '
                'application/vnd.com.example+json;version=1, '
                'application/vnd.com.example+json;version=1;q=0.9, '
                'application/vnd.com.example+json;version=2;q=0.9'),
            [
                headers.parse_content_type(value)
                for value in ('application/vnd.com.example+json;version=1',
                              'application/vnd.com.example+json;version=2',
                              'application/vnd.com.example+json;version=3')
            ],
        )
        self.assertEqual(str(selected),
                         'application/vnd.com.example+json; version=1')


class RemoveUrlAuthTests(unittest.TestCase):
    def test_that_auth_and_url_are_returned(self):
        result = algorithms.remove_url_auth('http://me:secret@example.com')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ('me', 'secret'))
        self.assertEqual(result[1], 'http://example.com')

    def test_that_return_value_has_attributes_too(self):
        result = algorithms.remove_url_auth('http://me:secret@example.com')
        self.assertEqual(result.auth, ('me', 'secret'))
        self.assertEqual(result.username, 'me')
        self.assertEqual(result.password, 'secret')
        self.assertEqual(result.url, 'http://example.com')

    def test_that_username_can_be_omitted(self):
        result = algorithms.remove_url_auth('http://:secret@example.com')
        self.assertIsNone(result.username)
        self.assertEqual(result.password, 'secret')
        self.assertEqual(result.url, 'http://example.com')

    def test_that_password_can_be_omitted(self):
        result = algorithms.remove_url_auth('http://insecure@example.com')
        self.assertEqual(result.username, 'insecure')
        self.assertIsNone(result.password)
        self.assertEqual(result.url, 'http://example.com')
