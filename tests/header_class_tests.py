import unittest

from fluenttest import test_case

from ietfparse import headers


class WhenConvertingSimpleContentTypeToStr(
        test_case.TestCase, unittest.TestCase):

    @classmethod
    def act(cls):
        cls.returned = str(headers.ContentType('primary', 'subtype'))

    def test_only_contains_type_information(self):
        self.assertEqual(self.returned, 'primary/subtype')


class WhenConvertingContentTypeWithParametersToStr(
        test_case.TestCase, unittest.TestCase):

    @classmethod
    def act(cls):
        cls.returned = str(headers.ContentType(
            'primary', 'subtype', {'one': '1', 'two': '2', 'three': 3}))

    def test_starts_with_primary_type(self):
        self.assertTrue(self.returned.startswith('primary/'))

    def test_contains_subtype(self):
        self.assertTrue(self.returned.startswith('primary/subtype'))

    def test_parameters_sorted_by_name(self):
        parameters = self.returned[self.returned.index(';') + 1:].strip()
        self.assertEqual(parameters, 'one=1; three=3; two=2')
