import unittest

from ietfparse import errors, headers


class ForwardedHeaderParsingTests(unittest.TestCase):
    def test_that_whitespace_is_irrelevant(self):
        # RFC7239. sec 7.1
        self.assertEqual(
            headers.parse_forwarded('for=192.0.2.43,'
                                    'for="[2001:db8:cafe::17]",for=unknown'),
            headers.parse_forwarded('for=192.0.2.43, '
                                    'for="[2001:db8:cafe::17]", for=unknown'))

    def test_that_order_is_preserved(self):
        parsed = headers.parse_forwarded('for=192.0.2.43,'
                                         'for="[2001:db8:cafe::17]",'
                                         'for=unknown')
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], {'for': '192.0.2.43'})
        self.assertEqual(parsed[1], {'for': '[2001:db8:cafe::17]'})
        self.assertEqual(parsed[2], {'for': 'unknown'})

    def test_that_param_names_are_normalized(self):
        parsed = headers.parse_forwarded('For="[2001:db8:cafe::17]:4711"')
        self.assertEqual(parsed, [{'for': '[2001:db8:cafe::17]:4711'}])

    def test_parsing_full_header(self):
        parsed = headers.parse_forwarded(
            'for=192.0.2.60;proto=http;'
            'by=203.0.113.43;host=example.com',
            only_standard_parameters=True)
        self.assertEqual(parsed[0]['for'], '192.0.2.60')
        self.assertEqual(parsed[0]['proto'], 'http')
        self.assertEqual(parsed[0]['by'], '203.0.113.43')
        self.assertEqual(parsed[0]['host'], 'example.com')

    def test_that_non_standard_parameters_are_parsed(self):
        parsed = headers.parse_forwarded('for=127.0.0.1;one=two')
        self.assertEqual(parsed[0]['one'], 'two')

    def test_that_non_standard_parameters_can_be_prohibited(self):
        with self.assertRaises(errors.StrictHeaderParsingFailure) as context:
            headers.parse_forwarded('for=127.0.0.1;one=2',
                                    only_standard_parameters=True)
        self.assertEqual(context.exception.header_name, 'Forwarded')
        self.assertEqual(context.exception.header_value, 'for=127.0.0.1;one=2')
