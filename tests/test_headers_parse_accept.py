import unittest

from ietfparse import datastructures, headers


class ParseAcceptHeaderTests(unittest.TestCase):

    # First example from http://tools.ietf.org/html/rfc7231#section-5.3.2

    def test_that_all_items_are_returned(self):
        parsed = headers.parse_accept('audio/*;q=0.2,audio/basic,'
                                      'audio/aiff;q=0')
        self.assertEqual(len(parsed), 3)

    def test_that_highest_priority_is_first(self):
        parsed = headers.parse_accept('audio/*;q=0.2,audio/basic,'
                                      'audio/aiff;q=0')
        self.assertEqual(parsed[0],
                         datastructures.ContentType('audio', 'basic'))

    def test_that_quality_parameter_is_removed(self):
        parsed = headers.parse_accept('audio/*;q=0.2,audio/basic,'
                                      'audio/aiff;q=0')
        for value in parsed:
            self.assertNotIn('q', value.parameters)

    # Final example in http://tools.ietf.org/html/rfc7231#section-5.3.2

    def test_that_most_specific_value_is_first(self):
        parsed = headers.parse_accept('text/*, text/plain,'
                                      'text/plain;format=flowed, */*')
        self.assertEqual(
            parsed[0],
            datastructures.ContentType('text', 'plain', {'format': 'flowed'}))

    def test_that_specific_value_without_parameters_is_second(self):
        parsed = headers.parse_accept('text/*, text/plain,'
                                      'text/plain;format=flowed, */*')
        self.assertEqual(parsed[1],
                         datastructures.ContentType('text', 'plain'))

    def test_that_subtype_wildcard_is_next_to_last(self):
        parsed = headers.parse_accept('text/*, text/plain,'
                                      'text/plain;format=flowed, */*')
        self.assertEqual(parsed[2], datastructures.ContentType('text', '*'))

    def test_that_least_specific_wildcard_is_least_preferred(self):
        parsed = headers.parse_accept('text/*, text/plain,'
                                      'text/plain;format=flowed, */*')
        self.assertEqual(parsed[3], datastructures.ContentType('*', '*'))

    def test_that_extension_tokens_are_parsed(self):
        self.assertEqual(
            headers.parse_accept('application/json;charset="utf-8"'), [
                datastructures.ContentType('application', 'json',
                                           {'charset': 'utf-8'})
            ])

    def test_that_extension_tokens_with_spaces_are_parsed(self):
        self.assertEqual(
            headers.parse_accept('application/json;x-foo=" something else"'), [
                datastructures.ContentType('application', 'json',
                                           {'x-foo': ' something else'})
            ])

    def test_that_invalid_parts_are_skipped(self):
        parsed = headers.parse_accept('text/html, image/gif, image/jpeg, '
                                      '*; q=.2, */*; q=.2')
        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0], datastructures.ContentType('text', 'html'))
        self.assertEqual(parsed[1],
                         datastructures.ContentType('image', 'jpeg'))
        self.assertEqual(parsed[2], datastructures.ContentType('image', 'gif'))
        self.assertEqual(parsed[3], datastructures.ContentType('*', '*'))

    def test_that_invalid_parts_raise_error_when_strict_is_enabled(self):
        with self.assertRaises(ValueError):
            headers.parse_accept(
                'text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2',
                strict=True)

    def test_the_invalid_header_returns_empty_list(self):
        parsed = headers.parse_accept('*')
        self.assertEqual(len(parsed), 0)


class ParseAcceptCharsetHeaderTests(unittest.TestCase):

    # Final example in http://tools.ietf.org/html/rfc7231#section-5.3.3

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


class ParseAcceptEncodingTests(unittest.TestCase):

    # Final example in http://tools.ietf.org/html/rfc7231#section-5.3.4

    def test_that_simple_wildcard_parses(self):
        self.assertEqual(headers.parse_accept_encoding('*'), ['*'])

    def test_that_response_sorted_by_quality(self):
        self.assertEqual(
            headers.parse_accept_encoding('compress, gzip;q=0.8, bzip;q=0.7'),
            ['compress', 'gzip', 'bzip'])

    def test_that_unspecified_quality_is_treated_as_highest(self):
        self.assertEqual(
            headers.parse_accept_encoding('snappy;q=0.1,gzip,bzip;q=0.8'),
            ['gzip', 'bzip', 'snappy'])

    def test_that_wildcard_sorts_before_rejected_character_sets(self):
        self.assertEqual(
            headers.parse_accept_encoding('gzip;q=0.5, compress;q=1.0,'
                                          'bzip;q=0.1, snappy;q=0, *'),
            ['compress', 'gzip', 'bzip', '*', 'snappy'])

    def test_that_quality_below_0_001_is_rejected(self):
        self.assertEqual(
            headers.parse_accept_encoding('bzip, gzip;q=0.0009, *'),
            ['bzip', '*', 'gzip'])


class ParseAcceptLanguageTests(unittest.TestCase):

    # Final example in http://tools.ietf.org/html/rfc7231#section-5.3.5

    def test_that_simple_wildcard_parses(self):
        self.assertEqual(headers.parse_accept_language('*'), ['*'])

    def test_that_response_sorted_by_quality(self):
        self.assertEqual(
            headers.parse_accept_language('de, en-gb;q=0.8, en;q=0.7'),
            ['de', 'en-gb', 'en'])

    def test_that_unspecified_quality_is_treated_as_highest(self):
        self.assertEqual(
            headers.parse_accept_language('en-gb;q=0.1,de,en;q=0.8'),
            ['de', 'en', 'en-gb'])

    def test_that_wildcard_sorts_before_rejected_character_sets(self):
        self.assertEqual(
            headers.parse_accept_language('es;q=0.5, es-mx;q=1.0,'
                                          'es-es;q=0.1, es-pr;q=0, *'),
            ['es-mx', 'es', 'es-es', '*', 'es-pr'])

    def test_that_quality_below_0_001_is_rejected(self):
        self.assertEqual(headers.parse_accept_language('aa, bb;q=0.0009, *'),
                         ['aa', '*', 'bb'])

    def test_that_order_is_retained_without_quality(self):
        self.assertEqual(
            headers.parse_accept_language('de-Latn-DE,de-Latf-DE,'
                                          'de-Latn-DE-1996'),
            ['de-Latn-DE', 'de-Latf-DE', 'de-Latn-DE-1996'],
        )

    def test_that_explicit_highest_quality_is_first(self):
        self.assertEqual(
            headers.parse_accept_language('de-Latn-DE,de-Latf-DE,'
                                          'de-Latn-DE-1996;q=1.0'),
            ['de-Latn-DE-1996', 'de-Latn-DE', 'de-Latf-DE'],
        )

    def test_that_order_is_retained_for_explicit_highest_quality(self):
        self.assertEqual(
            headers.parse_accept_language('de-Latn-DE,de-Latf-DE;q=1.0,'
                                          'de-Latn-DE-1996;q=1.0'),
            ['de-Latf-DE', 'de-Latn-DE-1996', 'de-Latn-DE'],
        )
