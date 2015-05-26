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


class WhenParsingAcceptCharsetHeader(unittest.TestCase):

    def test_that_simple_wildcard_parses(self):
        self.assertEqual(headers.parse_accept_charset('*'), ['*'])

    def test_that_response_sorted_by_quality(self):
        self.assertEqual(
            headers.parse_accept_charset('us-ascii;q=0.1, latin1;q=0.5,'
                                         'utf-8; q=1.0'),
            ['utf-8', 'latin1', 'us-ascii'],
        )

    def test_that_unspecified_quality_is_treated_as_highest(self):
        self.assertEqual(
            headers.parse_accept_charset('us-ascii;q=0.1,utf-8,latin1;q=0.8'),
            ['utf-8', 'latin1', 'us-ascii'],
        )

    def test_that_wildcard_sorts_before_rejected_character_sets(self):
        self.assertEqual(
            headers.parse_accept_charset('latin1;q=0.5, utf-8;q=1.0,'
                                         'us-ascii;q=0.1, ebcdic;q=0, *'),
            ['utf-8', 'latin1', 'us-ascii', '*', 'ebcdic'],
        )

    def test_that_quality_below_0_001_is_rejected(self):
        self.assertEqual(
            headers.parse_accept_charset('acceptable, rejected;q=0.0009, *'),
            ['acceptable', '*', 'rejected'],
        )
