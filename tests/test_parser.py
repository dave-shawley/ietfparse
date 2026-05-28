import unittest

from ietfparse import _links, _parser


class ParseErrorTests(unittest.TestCase):
    def test_that_parse_error_is_a_runtime_error(self) -> None:
        self.assertTrue(issubclass(_parser.ParseError, RuntimeError))


class CursorParserTests(unittest.TestCase):
    def test_that_tokens_are_parsed_after_optional_whitespace(self) -> None:
        parser = _parser.CursorParser(' \t token')
        parser.skip_ows()
        self.assertEqual(parser.parse_token(), 'token')

    def test_that_parameter_values_can_be_quoted_strings(self) -> None:
        parser = _parser.CursorParser(' "a\\"b"')
        self.assertEqual(parser.parse_parameter_value(), 'a"b')

    def test_that_parse_token_raises_parse_error_when_no_token_exists(
        self,
    ) -> None:
        parser = _parser.CursorParser(' \t')
        parser.skip_ows()
        with self.assertRaisesRegex(
            _parser.ParseError,
            r"malformed parser input: ' \\t'",
        ):
            parser.parse_token()

    def test_that_dangling_quoted_pairs_raise_parse_error(self) -> None:
        parser = _parser.CursorParser('"value\\')
        with self.assertRaisesRegex(
            _parser.ParseError,
            r'malformed parser input: \'"value\\\\\'',
        ):
            parser.parse_quoted_string()

    def test_that_unterminated_quoted_strings_raise_parse_error(
        self,
    ) -> None:
        parser = _parser.CursorParser('"value')
        with self.assertRaisesRegex(
            _parser.ParseError,
            r'malformed parser input: \'"value\'',
        ):
            parser.parse_quoted_string()

    def test_that_nested_comments_can_be_skipped(self) -> None:
        parser = _parser.CursorParser('(outer(inner\\)value))')
        parser.skip_comment()
        self.assertEqual(parser.index, len(parser.value))

    def test_that_skip_comment_requires_an_opening_parenthesis(self) -> None:
        parser = _parser.CursorParser('not-a-comment')
        with self.assertRaisesRegex(
            _parser.ParseError,
            r"malformed parser input: 'not-a-comment'",
        ):
            parser.skip_comment()

    def test_that_dangling_escaped_comment_characters_raise_parse_error(
        self,
    ) -> None:
        parser = _parser.CursorParser('(dangling\\')
        with self.assertRaisesRegex(
            _parser.ParseError,
            r"malformed parser input: '\(dangling\\\\'",
        ):
            parser.skip_comment()

    def test_that_unterminated_comments_raise_parse_error(self) -> None:
        parser = _parser.CursorParser('(unterminated')
        with self.assertRaisesRegex(
            _parser.ParseError,
            r"malformed parser input: '\(unterminated'",
        ):
            parser.skip_comment()


class ParameterTokenizerTests(unittest.TestCase):
    def test_that_quoted_semicolons_are_preserved(self) -> None:
        self.assertEqual(
            _parser.parse_http_parameters(
                'foo="bar;baz"; qux=zap',
                normalize_parameter_values=False,
            ),
            [('foo', 'bar;baz'), ('qux', 'zap')],
        )

    def test_that_parse_http_parameters_uses_the_tokenizer(self) -> None:
        self.assertEqual(
            _parser.parse_http_parameters(
                '; foo=bar; baz=qux',
                normalize_parameter_values=False,
            ),
            [('foo', 'bar'), ('baz', 'qux')],
        )

    def test_that_repeated_semicolon_delimiters_are_skipped(self) -> None:
        parser = _parser.ParameterTokenizer(normalize_parameter_values=False)
        self.assertEqual(
            parser.parse('; ; foo=bar;; baz=qux ;'),
            [('foo', 'bar'), ('baz', 'qux')],
        )

    def test_that_missing_semicolon_between_parameters_raises(self) -> None:
        parser = _parser.ParameterTokenizer()
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'foo=bar baz=qux'",
        ):
            parser.parse('foo=bar baz=qux')

    def test_that_parameters_without_equals_sign_raise(self) -> None:
        parser = _parser.ParameterTokenizer()
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'foo'",
        ):
            parser.parse('foo')

    def test_that_cursor_parse_errors_are_mapped_to_value_error(self) -> None:
        parser = _parser.ParameterTokenizer()
        with self.assertRaisesRegex(
            ValueError,
            r'malformed parameter list: \'foo="value\\\\\'',
        ):
            parser.parse('foo="value\\')

    def test_that_tokenizer_instances_can_be_reused(self) -> None:
        parser = _parser.ParameterTokenizer(normalize_parameter_values=False)
        self.assertEqual(parser.parse('foo=bar'), [('foo', 'bar')])
        self.assertEqual(parser.parse('baz=qux'), [('baz', 'qux')])

    def test_that_fast_parameter_parser_rejects_missing_equals_sign(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'foo'",
        ):
            _parser.parse_http_parameters('foo')

    def test_that_fast_parameter_parser_rejects_missing_parameter_value(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'foo='",
        ):
            _parser.parse_http_parameters('foo=')

    def test_that_fast_parameter_parser_rejects_invalid_parameter_name(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'bad name=value'",
        ):
            _parser.parse_http_parameters('bad name=value')

    def test_that_fast_parameter_parser_rejects_embedded_quote_in_value(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r'malformed parameter list: \'foo="a""b"\'',
        ):
            _parser.parse_http_parameters('foo="a""b"')

    def test_that_fast_parameter_parser_rejects_invalid_token_value(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"malformed parameter list: 'foo=bad value'",
        ):
            _parser.parse_http_parameters('foo=bad value')


class ListItemParserTests(unittest.TestCase):
    def test_that_quoted_commas_are_preserved(self) -> None:
        self.assertEqual(
            _parser.parse_list_items('first, "comma ->,<- here", last'),
            ['first', '"comma ->,<- here"', 'last'],
        )

    def test_that_unterminated_quoted_items_raise_parse_error(self) -> None:
        with self.assertRaisesRegex(
            _parser.ParseError,
            r'malformed parser input: \'first, "unterminated, last\'',
        ):
            _parser.parse_list_items('first, "unterminated, last')

    def test_that_dangling_quoted_pairs_raise_parse_error(self) -> None:
        with self.assertRaisesRegex(
            _parser.ParseError,
            r'malformed parser input: \'first, "dangling\\\\, last\'',
        ):
            _parser.parse_list_items('first, "dangling\\, last')


class CommentRemovalTests(unittest.TestCase):
    def test_that_nested_comments_are_removed(self) -> None:
        self.assertEqual(
            _parser.remove_http_comments(
                'text/plain (outer(inner\\)value)); charset=utf-8'
            ),
            'text/plain ; charset=utf-8',
        )

    def test_that_parentheses_inside_quoted_strings_are_preserved(
        self,
    ) -> None:
        self.assertEqual(
            _parser.remove_http_comments(
                'text/plain; note="(kept)" (discard)'
            ),
            'text/plain; note="(kept)" ',
        )


class LinkParserTests(unittest.TestCase):
    def test_that_parse_link_header_uses_the_link_parser(self) -> None:
        self.assertEqual(
            _links.parse_link_header('<one>; rel=next, <two>'),
            [('one', [('rel', 'next')]), ('two', [])],
        )

    def test_that_link_parser_instances_can_be_reused(self) -> None:
        parser = _links.ParameterParser()
        self.assertEqual(
            parser.parse('<>; title=one; title*=two'),
            [('', [('title*', 'two'), ('title', 'two')])],
        )
        self.assertEqual(
            parser.parse('<>; title=three'),
            [('', [('title', 'three')])],
        )
