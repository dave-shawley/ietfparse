import unittest

from ietfparse import _helpers, datastructures


class ParseHeaderTests(unittest.TestCase):
    def test_parse_accept_header(self) -> None:
        result = _helpers.parse_header(
            'parse_accept', 'text/html, text/plain;q=0.5'
        )
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], datastructures.ContentType)
        self.assertEqual(str(result[0]), 'text/html')
        self.assertEqual(str(result[1]), 'text/plain')

    def test_parse_content_type_header(self) -> None:
        result = _helpers.parse_header(
            'parse_content_type', 'text/html; charset=utf-8'
        )
        self.assertIsInstance(result, datastructures.ContentType)
        self.assertEqual(str(result), 'text/html; charset=utf-8')

    def test_parse_link_header(self) -> None:
        result = _helpers.parse_header(
            'parse_link', '<http://example.com>; rel="next"'
        )
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], datastructures.LinkHeader)
        self.assertEqual(result[0].target, 'http://example.com')
        self.assertEqual(result[0].rel, 'next')

    def test_unknown_parser_raises_error(self) -> None:
        with self.assertRaises(NotImplementedError):
            _helpers.parse_header('unknown_parser', 'some value')  # type: ignore[call-overload]

    def test_invalid_value_returns_original(self) -> None:
        result = _helpers.parse_header('parse_content_type', 'invalid value')
        self.assertEqual(result, 'invalid value')
