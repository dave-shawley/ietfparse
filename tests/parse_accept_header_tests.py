import unittest

from fluenttest import test_case

from ietfparse import datastructures, headers


class WhenParsingSimpleHttpAcceptHeader(test_case.TestCase, unittest.TestCase):

    # First example from http://tools.ietf.org/html/rfc7231#section-5.3.2

    @classmethod
    def act(cls):
        cls.parsed = headers.parse_http_accept_header(
            'audio/*;q=0.2, audio/basic')

    def test_that_both_items_are_returned(self):
        self.assertEqual(len(self.parsed), 2)

    def test_that_highest_priority_is_first(self):
        self.assertEqual(
            self.parsed[0], datastructures.ContentType('audio', 'basic'))

    def test_that_quality_parameter_is_removed(self):
        self.assertNotIn('q', self.parsed[1].parameters)


class WhenParsingHttpAcceptHeaderWithoutQualities(
        test_case.TestCase, unittest.TestCase):

    # Final example in http://tools.ietf.org/html/rfc7231#section-5.3.2

    @classmethod
    def act(cls):
        cls.parsed = headers.parse_http_accept_header(
            'text/*, text/plain, text/plain;format=flowed, */*')

    def test_that_most_specific_value_is_first(self):
        self.assertEqual(
            self.parsed[0],
            datastructures.ContentType('text', 'plain', {'format': 'flowed'}))

    def test_that_specific_value_without_parameters_is_second(self):
        self.assertEqual(
            self.parsed[1], datastructures.ContentType('text', 'plain'))

    def test_that_subtype_wildcard_is_next_to_last(self):
        self.assertEqual(
            self.parsed[2], datastructures.ContentType('text', '*'))

    def test_that_least_specific_wildcard_is_least_preferred(self):
        self.assertEqual(self.parsed[3], datastructures.ContentType('*', '*'))
