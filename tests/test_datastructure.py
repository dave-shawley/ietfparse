import decimal
import unittest

from ietfparse import (
    constants,  # noqa: F401 -- imported for coverage
    datastructures,
)


class ContentTypeCreationTests(unittest.TestCase):
    def test_that_primary_type_is_normalized(self) -> None:
        content_type = datastructures.ContentType('COntentType', 'b')
        self.assertEqual(content_type.content_type, 'contenttype')

    def test_that_subtype_is_normalized(self) -> None:
        content_type = datastructures.ContentType('a', '  SubType  ')
        self.assertEqual(content_type.content_subtype, 'subtype')

    def test_that_content_suffix_is_normalized(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', content_suffix=' JSON'
        )
        self.assertEqual(content_type.content_suffix, 'json')

    def test_that_parameter_names_are_casefolded(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'KEY': 'Value'}
        )
        self.assertDictEqual({'key': 'Value'}, content_type.parameters)


class ContentTypeStringificationTests(unittest.TestCase):
    def test_that_simple_case_works(self) -> None:
        content_type = datastructures.ContentType('primary', 'subtype')
        self.assertEqual(str(content_type), 'primary/subtype')

    def test_that_parameters_are_sorted_by_name(self) -> None:
        ct = datastructures.ContentType(
            'a', 'b', {'one': '1', 'two': '2', 'three': 3}
        )
        self.assertEqual(str(ct), 'a/b; one=1; three=3; two=2')

    def test_that_content_suffix_is_appended(self) -> None:
        ct = datastructures.ContentType(
            'a', 'b', {'foo': 'bar'}, content_suffix='xml'
        )
        self.assertEqual(str(ct), 'a/b+xml; foo=bar')


class ContentTypeQualityTests(unittest.TestCase):
    def test_that_quality_defaults_to_highest(self) -> None:
        self.assertEqual(datastructures.ContentType('a', 'b').quality, 1.0)

    def test_that_quality_is_derived_from_q_parameter(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.1236'}
        )
        self.assertEqual(content_type.quality, 0.124)

    def test_that_quality_below_minimum_is_rejected(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.0009'}
        )
        self.assertEqual(content_type.quality, 0.0)

    def test_that_quality_above_maximum_is_treated_as_highest(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.9994'}
        )
        self.assertEqual(content_type.quality, 1.0)

    def test_that_setting_quality_overrides_parameter_value(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.1'}
        )
        content_type.quality = 0.9876
        self.assertEqual(content_type.quality, 0.988)

    def test_that_decimal_quality_rounding_uses_decimal_semantics(
        self,
    ) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.1245'}
        )
        self.assertEqual(content_type.quality, 0.125)

    def test_that_large_decimal_quality_is_treated_as_highest(self) -> None:
        content_type = datastructures.ContentType('a', 'b')
        content_type.quality = decimal.Decimal('1E+100000')
        self.assertEqual(content_type.quality, 1.0)

    def test_clearing_quality_override(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.11111'}
        )
        self.assertEqual(content_type.quality, 0.111)

        content_type.quality = 0.999999
        self.assertEqual(content_type.quality, 1.0)

        content_type.quality = None
        self.assertEqual(content_type.quality, 0.111)

    def test_that_invalid_quality_raises_value_error(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.1'}
        )
        with self.assertRaises(ValueError):
            content_type.quality = 'something else'

    def test_that_non_number_quality_is_rejected(self) -> None:
        content_type = datastructures.ContentType(
            'a', 'b', parameters={'q': '0.1'}
        )
        with self.assertRaises(ValueError):
            content_type.quality = 'nan'
        with self.assertRaises(ValueError):
            content_type.quality = 'inf'


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
        self.assertEqual(content_type, 'text/plain')
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

    def test_hash_comparison(self) -> None:
        ct1 = datastructures.ContentType(
            'first', 'one', parameters={'1': 1, '2': 2}
        )
        ct2 = datastructures.ContentType('second', 'one', parameters={'1': 1})
        ct3 = datastructures.ContentType(
            'first', 'one', parameters={'2': 2, '1': 1}
        )

        self.assertIsInstance(hash(ct1), int)
        self.assertNotEqual(hash(ct1), hash(ct2))
        self.assertEqual(hash(ct1), hash(ct3))


class BaggageCreationTests(unittest.TestCase):
    def test_that_it_starts_empty(self) -> None:
        self.assertEqual(len(datastructures.Baggage()), 0)

    def test_that_it_seeds_from_a_mapping(self) -> None:
        baggage = datastructures.Baggage({'a': '1', 'b': '2'})
        self.assertEqual(dict(baggage), {'a': '1', 'b': '2'})

    def test_that_it_seeds_from_pairs(self) -> None:
        baggage = datastructures.Baggage([('a', '1'), ('b', '2')])
        self.assertEqual(dict(baggage), {'a': '1', 'b': '2'})

    def test_that_it_copies_another_baggage_with_properties(self) -> None:
        original = datastructures.Baggage()
        original.set('a', '1', properties=[('ttl', '30')])
        copy = datastructures.Baggage(original)
        self.assertEqual(list(copy.get_properties('a')), [('ttl', '30')])
        copy.set('a', '2')
        self.assertEqual(original['a'], '1')


class BaggageMutationTests(unittest.TestCase):
    def test_that_items_can_be_set_and_read(self) -> None:
        baggage = datastructures.Baggage()
        baggage['key'] = 'value'
        self.assertEqual(baggage['key'], 'value')

    def test_that_items_can_be_deleted(self) -> None:
        baggage = datastructures.Baggage({'key': 'value'})
        del baggage['key']
        self.assertNotIn('key', baggage)

    def test_that_setitem_discards_existing_properties(self) -> None:
        baggage = datastructures.Baggage()
        baggage.set('key', 'value', properties=[('ttl', '30')])
        baggage['key'] = 'new'
        self.assertEqual(list(baggage.get_properties('key')), [])

    def test_that_invalid_key_is_rejected(self) -> None:
        baggage = datastructures.Baggage()
        with self.assertRaises(ValueError):
            baggage.set('bad key', 'value')

    def test_that_invalid_property_name_is_rejected(self) -> None:
        baggage = datastructures.Baggage()
        with self.assertRaises(ValueError):
            baggage.set('key', 'value', properties={'bad name': 'x'})

    def test_that_properties_accept_a_mapping(self) -> None:
        baggage = datastructures.Baggage()
        baggage.set('key', 'value', properties={'ttl': '30', 'flag': None})
        self.assertEqual(
            list(baggage.get_properties('key')),
            [('ttl', '30'), ('flag', None)],
        )

    def test_that_get_properties_is_immutable(self) -> None:
        baggage = datastructures.Baggage()
        baggage.set('key', 'value', properties=[('ttl', '30')])
        with self.assertRaises(TypeError):
            baggage.get_properties('key')[0] = ('nope', '0')  # type: ignore[unsupported-operation]  # pyrefly  # ty: ignore[invalid-assignment]


class BaggageSerializationTests(unittest.TestCase):
    def test_that_members_are_comma_separated(self) -> None:
        baggage = datastructures.Baggage([('a', '1'), ('b', '2')])
        self.assertEqual(str(baggage), 'a=1,b=2')

    def test_that_values_are_percent_encoded(self) -> None:
        baggage = datastructures.Baggage({'key': 'a b,c'})
        self.assertEqual(str(baggage), 'key=a%20b%2Cc')

    def test_that_properties_are_serialized(self) -> None:
        baggage = datastructures.Baggage()
        baggage.set(
            'key', 'value', properties=[('ttl', '30'), ('secure', None)]
        )
        self.assertEqual(str(baggage), 'key=value;ttl=30;secure')


class BaggageComparisonTests(unittest.TestCase):
    def test_that_equal_baggage_compares_equal(self) -> None:
        one = datastructures.Baggage({'a': '1'})
        two = datastructures.Baggage({'a': '1'})
        self.assertEqual(one, two)

    def test_that_differing_properties_are_not_equal(self) -> None:
        one = datastructures.Baggage()
        one.set('a', '1', properties=[('ttl', '30')])
        two = datastructures.Baggage({'a': '1'})
        self.assertNotEqual(one, two)

    def test_that_it_compares_equal_to_a_plain_mapping(self) -> None:
        self.assertEqual(datastructures.Baggage({'a': '1'}), {'a': '1'})

    def test_that_it_is_not_equal_to_unrelated_types(self) -> None:
        self.assertNotEqual(datastructures.Baggage({'a': '1'}), object())

    def test_that_it_is_unhashable(self) -> None:
        baggage = datastructures.Baggage()
        with self.assertRaises(TypeError):
            hash(baggage)
