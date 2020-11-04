import unittest

from ietfparse import datastructures, headers


class SimpleContentTypeParsingTests(unittest.TestCase):
    def setUp(self):
        super(SimpleContentTypeParsingTests, self).setUp()
        self.parsed = headers.parse_content_type(
            'text/plain', normalize_parameter_values=False)

    def test_that_type_is_parsed(self):
        self.assertEqual(self.parsed.content_type, 'text')

    def test_that_subtype_is_parsed(self):
        self.assertEqual(self.parsed.content_subtype, 'plain')

    def test_that_no_parameters_are_found(self):
        self.assertEqual(self.parsed.parameters, {})

    def test_that_no_suffix_is_foudn(self):
        self.assertEqual(self.parsed.content_suffix, None)


class ParsingComplexContentTypeTests(unittest.TestCase):
    def setUp(self):
        super(ParsingComplexContentTypeTests, self).setUp()
        self.parsed = headers.parse_content_type(
            'message/HTTP+JSON; version=2.0 (someday); MsgType="Request"',
            normalize_parameter_values=False)

    def test_that_type_is_parsed(self):
        self.assertEqual(self.parsed.content_type, 'message')

    def test_that_subtype_is_parsed(self):
        self.assertEqual(self.parsed.content_subtype, 'http')

    def test_that_suffix_is_parsed(self):
        self.assertEqual(self.parsed.content_suffix, 'json')

    def test_that_version_parameter_is_parsed(self):
        self.assertEqual(self.parsed.parameters['version'], '2.0')

    def test_that_message_type_parameter_is_parsed(self):
        self.assertEqual(self.parsed.parameters['msgtype'], 'Request')


class ParsingBrokenContentTypes(unittest.TestCase):
    def test_that_missing_subtype_raises_value_error(self):
        with self.assertRaises(ValueError):
            headers.parse_content_type('*')


class Rfc7231ExampleTests(unittest.TestCase):
    """Test cases from RFC7231, Section 3.1.1.1"""
    def setUp(self):
        self.normalized = datastructures.ContentType('text', 'html',
                                                     {'charset': 'utf-8'})

    def test_that_simplest_header_matches(self):
        self.assertEqual(headers.parse_content_type('text/html;charset=utf-8'),
                         self.normalized)

    def test_that_media_type_parameters_are_case_insensitive(self):
        self.assertEqual(headers.parse_content_type('text/html;charset=UTF-8'),
                         self.normalized)

    def test_that_media_type_is_case_insensitive(self):
        self.assertEqual(
            headers.parse_content_type('Text/HTML;Charset="utf-8"'),
            self.normalized)

    def test_that_whitespace_is_ignored(self):
        self.assertEqual(
            headers.parse_content_type('text/html; charset="utf-8"'),
            self.normalized)
