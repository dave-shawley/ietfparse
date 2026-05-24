import unittest

from ietfparse import _parser, datastructures, errors, headers


class SimpleContentTypeParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.parsed = headers.parse_content_type(
            'text/plain', normalize_parameter_values=False
        )

    def test_that_type_is_parsed(self) -> None:
        self.assertEqual(self.parsed.content_type, 'text')

    def test_that_subtype_is_parsed(self) -> None:
        self.assertEqual(self.parsed.content_subtype, 'plain')

    def test_that_no_parameters_are_found(self) -> None:
        self.assertEqual(self.parsed.parameters, {})

    def test_that_no_suffix_is_foudn(self) -> None:
        self.assertEqual(self.parsed.content_suffix, None)


class ParsingComplexContentTypeTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.parsed = headers.parse_content_type(
            'message/HTTP+JSON; version=2.0 (someday); MsgType="Request"',
            normalize_parameter_values=False,
        )

    def test_that_type_is_parsed(self) -> None:
        self.assertEqual(self.parsed.content_type, 'message')

    def test_that_subtype_is_parsed(self) -> None:
        self.assertEqual(self.parsed.content_subtype, 'http')

    def test_that_suffix_is_parsed(self) -> None:
        self.assertEqual(self.parsed.content_suffix, 'json')

    def test_that_version_parameter_is_parsed(self) -> None:
        self.assertEqual(self.parsed.parameters['version'], '2.0')

    def test_that_message_type_parameter_is_parsed(self) -> None:
        self.assertEqual(self.parsed.parameters['msgtype'], 'Request')


class QuotedContentTypeParameterParsingTests(unittest.TestCase):
    def test_that_quoted_parameters_can_contain_semicolons(self) -> None:
        parsed = headers.parse_content_type(
            'text/plain; note="a;b"; charset=utf-8',
            normalize_parameter_values=False,
        )
        self.assertEqual(parsed.parameters['note'], 'a;b')
        self.assertEqual(parsed.parameters['charset'], 'utf-8')

    def test_that_quoted_parameters_can_contain_equals_signs(self) -> None:
        parsed = headers.parse_content_type(
            'text/plain; note="a=b"; charset=utf-8',
            normalize_parameter_values=False,
        )
        self.assertEqual(parsed.parameters['note'], 'a=b')
        self.assertEqual(parsed.parameters['charset'], 'utf-8')

    def test_that_quoted_pairs_are_unescaped(self) -> None:
        parsed = headers.parse_content_type(
            'text/plain; note="a\\"b"',
            normalize_parameter_values=False,
        )
        self.assertEqual(parsed.parameters['note'], 'a"b')

    def test_that_comments_with_nesting_and_escapes_are_ignored(self) -> None:
        parsed = headers.parse_content_type(
            'text/plain (outer(inner\\)value)); charset=utf-8',
            normalize_parameter_values=False,
        )
        self.assertEqual(parsed.content_type, 'text')
        self.assertEqual(parsed.content_subtype, 'plain')
        self.assertEqual(parsed.parameters['charset'], 'utf-8')

    def test_that_parentheses_inside_quoted_parameters_are_not_comments(
        self,
    ) -> None:
        parsed = headers.parse_content_type(
            'text/plain; note="(kept)"; charset=utf-8 (discard)',
            normalize_parameter_values=False,
        )
        self.assertEqual(parsed.parameters['note'], '(kept)')
        self.assertEqual(parsed.parameters['charset'], 'utf-8')


class ParsingBrokenContentTypes(unittest.TestCase):
    def test_that_missing_subtype_raises_value_error(self) -> None:
        with self.assertRaises(errors.MalformedContentType):
            headers.parse_content_type('*')

    def test_that_comment_parse_errors_raise_malformed_content_type(
        self,
    ) -> None:
        value = 'text/plain (unterminated'
        with self.assertRaises(errors.MalformedContentType) as raised:
            headers.parse_content_type(value)

        self.assertEqual(raised.exception.header_value, value)
        self.assertIsInstance(raised.exception.__cause__, _parser.ParseError)

    def test_that_multiple_suffix_delimiters_raise_value_error(self) -> None:
        with self.assertRaises(errors.MalformedContentType):
            headers.parse_content_type('application/example+json+xml')


class Rfc7231ExampleTests(unittest.TestCase):
    """Test cases from RFC7231, Section 3.1.1.1"""

    def setUp(self) -> None:
        self.normalized = datastructures.ContentType(
            'text', 'html', {'charset': 'utf-8'}
        )

    def test_that_simplest_header_matches(self) -> None:
        self.assertEqual(
            headers.parse_content_type('text/html;charset=utf-8'),
            self.normalized,
        )

    def test_that_media_type_parameters_are_case_insensitive(self) -> None:
        self.assertEqual(
            headers.parse_content_type('text/html;charset=UTF-8'),
            self.normalized,
        )

    def test_that_media_type_is_case_insensitive(self) -> None:
        self.assertEqual(
            headers.parse_content_type('Text/HTML;Charset="utf-8"'),
            self.normalized,
        )

    def test_that_whitespace_is_ignored(self) -> None:
        self.assertEqual(
            headers.parse_content_type('text/html; charset="utf-8"'),
            self.normalized,
        )
