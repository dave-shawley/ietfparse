import unittest

from fluenttest import test_case

from ietfparse import headers


class WhenCreatingContentType(test_case.TestCase, unittest.TestCase):
    @classmethod
    def act(cls):
        cls.value = headers.ContentType(
            'ContentType', ' SubType ', parameters={'Key': 'Value'})

    def should_normalize_primary_type(self):
        self.assertEqual(self.value.content_type, 'contenttype')

    def should_normalize_subtype(self):
        self.assertEqual(self.value.content_subtype, 'subtype')

    def should_convert_parameters_to_lowercase(self):
        self.assertEqual(self.value.parameters['key'], 'Value')


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


class WhenComparingContentTypesForEquality(unittest.TestCase):

    def test_type_equals_itself(self):
        self.assertEqual(
            headers.ContentType('primary', 'subtype'),
            headers.ContentType('primary', 'subtype'))

    def test_different_types_are_not_equal(self):
        self.assertNotEqual(
            headers.ContentType('text', 'json'),
            headers.ContentType('application', 'json'))

    def test_types_differing_by_case_are_equal(self):
        self.assertEqual(
            headers.ContentType('text', 'html', {'Level': '3.2'}),
            headers.ContentType('text', 'HTML', {'level': '3.2'}))

    def test_types_with_differing_params_are_not_equal(self):
        self.assertNotEqual(
            headers.ContentType('text', 'html', {'level': '1'}),
            headers.ContentType('text', 'html', {'level': '2'}))
