import unittest

from fluenttest import test_case

from ietfparse import errors, headers


class WhenParsingSimpleLinkHeader(test_case.TestCase, unittest.TestCase):
    @classmethod
    def act(cls):
        cls.parsed = headers.parse_link(
            '<http://example.com/TheBook/chapter2>; rel="previous"; '
            'title="previous chapter"')

    def test_that_single_header_is_returned(self):
        self.assertEqual(len(self.parsed), 1)

    def test_that_target_iri_is_returned(self):
        self.assertEqual(self.parsed[0].target,
                         'http://example.com/TheBook/chapter2')

    def test_that_rel_parameter_is_returned(self):
        self.assertIn(('rel', 'previous'), self.parsed[0].parameters)

    def test_that_title_parameter_is_returned(self):
        self.assertIn(('title', 'previous chapter'), self.parsed[0].parameters)


class MultipleLinkParsingTests(test_case.TestCase, unittest.TestCase):
    @classmethod
    def act(cls):
        cls.parsed = headers.parse_link(
            '<http://example.com/first>; rel=first;another=value,'
            '<http://example.com/second>',
        )

    def test_that_both_links_are_returned(self):
        self.assertEqual(self.parsed[0].target, 'http://example.com/first')
        self.assertEqual(self.parsed[1].target, 'http://example.com/second')

    def test_that_parameters_are_returned_when_present(self):
        self.assertEqual(self.parsed[0].parameters,
                         [('rel', 'first'), ('another', 'value')])

    def test_that_empty_parameters_are_returned_when_appropriate(self):
        self.assertEqual(self.parsed[1].parameters, [])


class UglyParsingTests(unittest.TestCase):

    def test_that_quoted_uris_can_contain_semicolons(self):
        parsed = headers.parse_link('<http://host/matrix;param/>')
        self.assertEqual(parsed[0].target, 'http://host/matrix;param/')

    def test_that_quoted_parameters_can_contain_commas(self):
        parsed = headers.parse_link(
            '<http://example/com>; rel="quoted, with comma", <1>')
        self.assertEqual(parsed[0].parameters, [('rel', 'quoted, with comma')])

    def test_that_quoted_parameters_can_contain_semicolons(self):
        parsed = headers.parse_link(
            '<http://example/com>; rel="quoted; with semicolon", <1>')
        self.assertEqual(parsed[0].parameters,
                         [('rel', 'quoted; with semicolon')])

    def test_that_title_star_overrides_title_parameter(self):
        parsed = headers.parse_link('<>; title=title; title*=title*')
        self.assertEqual(parsed[0].parameters,
                         [('title*', 'title*'), ('title', 'title*')])


class WhenParsingMalformedLinkHeader(unittest.TestCase):

    def test_that_value_error_when_url_brackets_are_missing(self):
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('http://foo.com; rel=wrong')

    def test_that_first_semicolon_is_required(self):
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('<http://foo.com> rel="still wrong"')

    def test_that_first_rel_parameter_is_used(self):
        # semantically malformed but handled appropriately
        # see RFC5988 sec. 5.3
        parsed = headers.parse_link('<>; rel=first; rel=ignored')
        self.assertIn(('rel', 'first'), parsed[0].parameters)
        self.assertNotIn(('rel', 'ignored'), parsed[0].parameters)

    def test_that_multiple_media_parameters_are_rejected(self):
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('<first-link>; media=1; media=2')

    def test_that_first_title_parameter_is_used(self):
        # semantically malformed but handled appropriately
        # see RFC5988 sec. 5.4
        parsed = headers.parse_link('<>; title=first; title=ignored')
        self.assertIn(('title', 'first'), parsed[0].parameters)
        self.assertNotIn(('title', 'ignored'), parsed[0].parameters)

    def test_that_first_title_star_parameter_is_used(self):
        # semantically malformed but handled appropriately
        # see RFC5988 sec. 5.4
        parsed = headers.parse_link('<>; title*=first; title*=ignored')
        self.assertIn(('title*', 'first'), parsed[0].parameters)
        self.assertNotIn(('title*', 'ignored'), parsed[0].parameters)

    def test_that_multiple_type_parameters_are_rejected(self):
        with self.assertRaises(errors.MalformedLinkValue):
            headers.parse_link('<>; type=1; type=2')

    def test_that_semantic_tests_can_be_turned_off(self):
        parsed = headers.parse_link(
            '<multiple-titles>;title=one;title=two;title*=three;title*=four, '
            '<multiple-rels>; rel=first; rel=second,'
            '<multiple-medias>; media=one; media=two',
            strict=False,
        )
        self.assertEqual(len(parsed), 3)
