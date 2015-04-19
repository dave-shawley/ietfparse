import unittest

from fluenttest import test_case

from ietfparse import headers


class WhenParsingSimpleLinkHeader(test_case.TestCase, unittest.TestCase):
    @classmethod
    def act(cls):
        cls.parsed = headers.parse_link_header(
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
        cls.parsed = headers.parse_link_header(
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
        parsed = headers.parse_link_header('<http://host/matrix;param/>')
        self.assertEqual(parsed[0].target, 'http://host/matrix;param/')


class WhenParsingMalformedLinkHeader(unittest.TestCase):

    def test_that_value_error_when_url_brackets_are_missing(self):
        with self.assertRaises(ValueError):
            headers.parse_link_header('http://foo.com; rel=wrong')

    def test_that_first_semicolon_is_required(self):
        with self.assertRaises(ValueError):
            headers.parse_link_header('<http://foo.com> rel="still wrong"')

    def test_that_first_rel_parameter_is_used(self):
        # semantically malformed but handled appropriately
        # see RFC5988 sec. 5.3
        parsed = headers.parse_link_header('<>; rel=first; rel=ignored')
        self.assertIn(('rel', 'first'), parsed[0].parameters)
        self.assertNotIn(('rel', 'ignored'), parsed[0].parameters)
