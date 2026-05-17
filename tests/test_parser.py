import typing
import unittest

from ietfparse import _parser


class ExposedCursorParser(_parser.CursorParser):
    def error_message(self) -> str:
        return self._error_message()

    def raise_error(self, message: str) -> typing.NoReturn:
        self._raise(message)

    def parse_quoted_string(self) -> str:
        return self._parse_quoted_string()


class ExposedParameterTokenizer(_parser.ParameterTokenizer):
    def error_message(self) -> str:
        return self._error_message()


class CursorParserTests(unittest.TestCase):
    def test_that_default_error_message_includes_input(self) -> None:
        parser = ExposedCursorParser('abc')
        self.assertEqual(
            parser.error_message(),
            "malformed parser input: 'abc'",
        )

    def test_that_raise_uses_value_error(self) -> None:
        parser = ExposedCursorParser('abc')
        with self.assertRaisesRegex(ValueError, 'bad input'):
            parser.raise_error('bad input')

    def test_that_unterminated_quoted_strings_keep_the_unreachable_guard(
        self,
    ) -> None:
        class NonRaisingParser(ExposedCursorParser):
            def __init__(self, value: str) -> None:
                super().__init__(value)
                self.message: str | None = None

            def _raise(self, message: str) -> None:
                self.message = message

        parser = NonRaisingParser('"unterminated')
        with self.assertRaisesRegex(AssertionError, 'unreachable'):
            parser.parse_quoted_string()
        self.assertEqual(
            parser.message,
            "malformed parser input: '\"unterminated'",
        )


class ParameterTokenizerTests(unittest.TestCase):
    def test_that_error_message_mentions_parameter_lists(self) -> None:
        parser = ExposedParameterTokenizer('foo=bar')
        self.assertEqual(
            parser.error_message(),
            "malformed parameter list: 'foo=bar'",
        )

    def test_that_repeated_semicolon_delimiters_are_skipped(self) -> None:
        parser = _parser.ParameterTokenizer(
            '; ; foo=bar;; baz=qux ;',
            normalize_parameter_values=False,
        )
        self.assertEqual(
            parser.parse(),
            [('foo', 'bar'), ('baz', 'qux')],
        )

    def test_that_missing_semicolon_between_parameters_raises(self) -> None:
        parser = _parser.ParameterTokenizer('foo=bar baz=qux')
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'foo=bar baz=qux'",
        ):
            parser.parse()

    def test_that_parameters_without_equals_sign_raise(self) -> None:
        parser = _parser.ParameterTokenizer('foo')
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'foo'",
        ):
            parser.parse()
