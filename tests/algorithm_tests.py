import unittest

from ietfparse import algorithms, datastructures, errors, headers


class ContentNegotiationTestCase(unittest.TestCase):
    requested = []

    def assertContentTypeMatchedAs(self, expected, *supported, **kwargs):
        selected, matched = algorithms.select_content_type(
            self.requested,
            [headers.parse_content_type(value) for value in supported],
        )
        self.assertEqual(selected, headers.parse_content_type(expected))
        if 'matching_pattern' in kwargs:
            self.assertEqual(str(matched), kwargs['matching_pattern'])


class WhenUsingProactiveContentNegotiation(ContentNegotiationTestCase):

    @classmethod
    def setUpClass(cls):
        super(WhenUsingProactiveContentNegotiation, cls).setUpClass()
        cls.requested.extend(headers.parse_accept(
            'application/vnd.example.com+json;version=2, '
            'application/vnd.example.com+json;version=1;q=0.9, '
            'application/json;q=0.7, '
            'application/*;q=0.6, '
            'text/json;q=0.2, '
            'text/*;q=0.1, '
            'text/javascript;q=0'
        ))

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
            'application/vnd.example.com+json;version=3', 'application/json',
        )

    def test_that_high_quality_wildcard_match_preferred(self):
        self.assertContentTypeMatchedAs(
            'application/other',
            'text/plain', 'application/other',
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


class WhenUsingRfc7231Examples(ContentNegotiationTestCase):

    @classmethod
    def setUpClass(cls):
        super(WhenUsingRfc7231Examples, cls).setUpClass()
        cls.requested.extend(headers.parse_accept(
            'text/*;q=0.3, text/html;q=0.7, text/html;level=1, '
            'text/html;level=2;q=0.4, */*;q=0.5'
        ))

    def test_that_text_html_level_1_matches(self):
        self.assertContentTypeMatchedAs(
            'text/html;level=1', 'text/html;level=1')

    def test_that_text_html_matches(self):
        self.assertContentTypeMatchedAs('text/html', 'text/html')

    def test_that_text_plain_matches_text(self):
        self.assertContentTypeMatchedAs(
            'text/plain', 'text/plain', matching_pattern='text/*')

    def test_that_image_jpeg_matches_wildcard(self):
        self.assertContentTypeMatchedAs(
            'image/jpeg', 'image/jpeg', matching_pattern='*/*')

    def test_that_text_html_level_2_matches(self):
        self.assertContentTypeMatchedAs(
            'text/html;level=2', 'text/html;level=2',
            matching_pattern='text/html; level=2'
        )

    def test_that_text_html_level_3_matches_text_html(self):
        self.assertContentTypeMatchedAs(
            'text/html;level=3', 'text/html;level=3',
            matching_pattern='text/html',
        )


class WhenSelectingWithRawContentTypes(unittest.TestCase):

    def test_that_raw_content_type_has_highest_quality(self):
        selected, matched = algorithms.select_content_type(
            [
                datastructures.ContentType('type', 'preferred')
            ],
            [
                datastructures.ContentType('type', 'acceptable'),
                datastructures.ContentType('type', 'almost-perfect'),
                datastructures.ContentType('type', 'preferred'),
            ],
        )
        self.assertEqual(selected.content_subtype, 'preferred')
