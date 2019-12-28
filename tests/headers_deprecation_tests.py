import unittest
import warnings

from ietfparse import headers


class DeprecationTests(unittest.TestCase):
    def test_that_parse_http_accept_header_emits_deprecation_warning(self):
        warnings.simplefilter('always')
        with warnings.catch_warnings(record=True) as caught:
            headers.parse_http_accept_header('Accept: application/json')
            self.assertEqual(len(caught), 1)
            self.assertEqual(caught[-1].category, DeprecationWarning)

    def test_that_parse_link_header_emits_deprecation_warning(self):
        warnings.simplefilter('always')
        with warnings.catch_warnings(record=True) as caught:
            headers.parse_link_header(
                '<http://example.com/TheBook/chapter2>; rel="previous"; '
                'title="previous chapter"')
            self.assertEqual(len(caught), 1)
            self.assertEqual(caught[-1].category, DeprecationWarning)

    def test_that_parse_list_header_emits_deprecation_warning(self):
        warnings.simplefilter('always')
        with warnings.catch_warnings(record=True) as caught:
            headers.parse_list_header('one, two,three    ,four,five')
            self.assertEqual(len(caught), 1)
            self.assertEqual(caught[-1].category, DeprecationWarning)
