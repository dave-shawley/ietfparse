import unittest

from ietfparse.datastructures import ContentType


class ContentTypeCreationTests(unittest.TestCase):
    def test_that_primary_type_is_normalized(self):
        self.assertEqual('contenttype',
                         ContentType('COntentType', 'b').content_type)

    def test_that_subtype_is_normalized(self):
        self.assertEqual('subtype',
                         ContentType('a', '  SubType  ').content_subtype)

    def test_that_content_suffix_is_normalized(self):
        self.assertEqual(
            'json',
            ContentType('a', 'b', content_suffix=' JSON').content_suffix)

    def test_that_parameter_names_are_casefolded(self):
        self.assertDictEqual({'key': 'Value'},
                             ContentType('a', 'b', parameters={
                                 'KEY': 'Value'
                             }).parameters)


class ContentTypeStringificationTests(unittest.TestCase):
    def test_that_simple_case_works(self):
        self.assertEqual('primary/subtype',
                         str(ContentType('primary', 'subtype')))

    def test_that_parameters_are_sorted_by_name(self):
        ct = ContentType('a', 'b', {'one': '1', 'two': '2', 'three': 3})
        self.assertEqual('a/b; one=1; three=3; two=2', str(ct))

    def test_that_content_suffix_is_appended(self):
        ct = ContentType('a', 'b', {'foo': 'bar'}, content_suffix='xml')
        self.assertEqual('a/b+xml; foo=bar', str(ct))


class ContentTypeComparisonTests(unittest.TestCase):
    def test_type_equals_itself(self):
        self.assertEqual(ContentType('a', 'b'), ContentType('a', 'b'))

    def test_that_differing_types_are_not_equal(self):
        self.assertNotEqual(ContentType('a', 'b'), ContentType('b', 'a'))

    def test_that_differing_suffixes_are_not_equal(self):
        self.assertNotEqual(ContentType('a', 'b', content_suffix='1'),
                            ContentType('a', 'b', content_suffix='2'))

    def test_that_differing_params_are_not_equal(self):
        self.assertNotEqual(ContentType('a', 'b', parameters={'one': '1'}),
                            ContentType('a', 'b'))

    def test_that_case_is_ignored_when_comparing_types(self):
        self.assertEqual(ContentType('text', 'html', {'level': '3.2'}, 'json'),
                         ContentType('Text', 'Html', {'Level': '3.2'}, 'JSON'))

    def test_primary_wildcard_is_less_than_anything_else(self):
        self.assertLess(ContentType('*', '*'), ContentType('text', 'plain'))
        self.assertLess(ContentType('*', '*'), ContentType('text', '*'))

    def test_subtype_wildcard_is_less_than_concrete_types(self):
        self.assertLess(ContentType('application', '*'),
                        ContentType('application', 'json'))
        self.assertLess(ContentType('text', '*'),
                        ContentType('application', 'json'))

    def test_type_with_fewer_parameters_is_lesser(self):
        self.assertLess(
            ContentType('application', 'text', parameters={'1': 1}),
            ContentType('application', 'text', parameters={
                '1': 1,
                '2': 2
            }))

    def test_otherwise_equal_types_ordered_by_primary(self):
        self.assertLess(ContentType('first', 'one', parameters={'1': 1}),
                        ContentType('second', 'one', parameters={'1': 1}))

    def test_otherwise_equal_types_ordered_by_subtype(self):
        self.assertLess(
            ContentType('application', 'first', parameters={'1': 1}),
            ContentType('application', 'second', parameters={'1': 1}))
