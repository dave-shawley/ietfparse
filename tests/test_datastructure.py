import unittest

from ietfparse import (
    constants,  # noqa: F401 -- imported for coverage
    datastructures,
)


class ContentTypeCreationTests(unittest.TestCase):
    def test_that_primary_type_is_normalized(self) -> None:
        content_type = datastructures.ContentType('COntentType', 'b')
        self.assertEqual('contenttype', content_type.content_type)

    def test_that_subtype_is_normalized(self) -> None:
        content_type = datastructures.ContentType('a', '  SubType  ')
        self.assertEqual('subtype', content_type.content_subtype)

    def test_that_content_suffix_is_normalized(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', content_suffix=' JSON'
        )
        self.assertEqual('json', content_type.content_suffix)

    def test_that_parameter_names_are_casefolded(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'KEY': 'Value'}
        )
        self.assertDictEqual({'key': 'Value'}, content_type.parameters)


class ContentTypeStringificationTests(unittest.TestCase):
    def test_that_simple_case_works(self) -> None:
        content_type = datastructures.ContentType('primary', 'subtype')
        self.assertEqual('primary/subtype', str(content_type))

    def test_that_parameters_are_sorted_by_name(self) -> None:
        ct = datastructures.ContentType(
            'a', 'b', {'one': '1', 'two': '2', 'three': 3}
        )
        self.assertEqual('a/b; one=1; three=3; two=2', str(ct))

    def test_that_content_suffix_is_appended(self) -> None:
        ct = datastructures.ContentType(
            'a', 'b', {'foo': 'bar'}, content_suffix='xml'
        )
        self.assertEqual('a/b+xml; foo=bar', str(ct))


class ContentTypeComparisonTests(unittest.TestCase):
    def test_type_equals_itself(self) -> None:
        ct1 = datastructures.ContentType('a', 'b')
        ct2 = datastructures.ContentType('a', 'b')
        self.assertEqual(ct1, ct2)

    def test_that_differing_types_are_not_equal(self) -> None:
        ct1 = datastructures.ContentType('a', 'b')
        ct2 = datastructures.ContentType('b', 'a')
        self.assertNotEqual(ct1, ct2)

    def test_that_differing_suffixes_are_not_equal(self) -> None:
        ct1 = datastructures.ContentType('a', 'b', content_suffix='1')
        ct2 = datastructures.ContentType('a', 'b', content_suffix='2')
        self.assertNotEqual(ct1, ct2)

    def test_that_differing_params_are_not_equal(self) -> None:
        ct1 = datastructures.ContentType('a', 'b', parameters={'one': '1'})
        ct2 = datastructures.ContentType('a', 'b')
        self.assertNotEqual(ct1, ct2)

    def test_that_case_is_ignored_when_comparing_types(self) -> None:
        ct1 = datastructures.ContentType(
            'text', 'html', {'level': '3.2'}, 'json'
        )
        ct2 = datastructures.ContentType(
            'Text', 'Html', {'Level': '3.2'}, 'JSON'
        )
        self.assertEqual(ct1, ct2)

    def test_primary_wildcard_is_less_than_anything_else(self) -> None:
        wildcard = datastructures.ContentType('*', '*')
        text_plain = datastructures.ContentType('text', 'plain')
        text_wildcard = datastructures.ContentType('text', '*')
        self.assertLess(wildcard, text_plain)
        self.assertLess(wildcard, text_wildcard)

    def test_subtype_wildcard_is_less_than_concrete_types(self) -> None:
        app_wildcard = datastructures.ContentType('application', '*')
        app_json = datastructures.ContentType('application', 'json')
        text_wildcard = datastructures.ContentType('text', '*')
        self.assertLess(app_wildcard, app_json)
        self.assertLess(text_wildcard, app_json)

    def test_type_with_fewer_parameters_is_lesser(self) -> None:
        ct1 = datastructures.ContentType(
            'application', 'text', parameters={'1': 1}
        )
        ct2 = datastructures.ContentType(
            'application', 'text', parameters={'1': 1, '2': 2}
        )
        self.assertLess(ct1, ct2)

    def test_otherwise_equal_types_ordered_by_primary(self) -> None:
        ct1 = datastructures.ContentType('first', 'one', parameters={'1': 1})
        ct2 = datastructures.ContentType('second', 'one', parameters={'1': 1})
        self.assertLess(ct1, ct2)

    def test_otherwise_equal_types_ordered_by_subtype(self) -> None:
        ct1 = datastructures.ContentType(
            'application', 'first', parameters={'1': 1}
        )
        ct2 = datastructures.ContentType(
            'application', 'second', parameters={'1': 1}
        )
        self.assertLess(ct1, ct2)

    def test_comparing_with_strings(self) -> None:
        content_type = datastructures.ContentType('text', 'plain')
        self.assertEqual('text/plain', content_type)
        self.assertGreater(content_type, 'application/json')
        text_plain = datastructures.ContentType('text', 'plain')
        self.assertNotEqual(text_plain, 'text')

    def test_comparing_non_content_type_instances(self) -> None:
        ct = datastructures.ContentType('application', 'binary')
        obj = object()
        self.assertNotEqual(ct, obj)
        for cmp in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            dunder = f'__{cmp}__'
            self.assertIs(
                getattr(ct, dunder)(obj),
                NotImplemented,
                f'{dunder} should return NotImplemented for other type',
            )
