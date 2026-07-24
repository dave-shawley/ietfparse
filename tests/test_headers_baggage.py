import unittest

from ietfparse import datastructures, errors, headers


class BaggageParsingTests(unittest.TestCase):
    def test_that_simple_members_are_parsed(self) -> None:
        baggage = headers.parse_baggage('key1=value1,key2=value2')
        self.assertEqual(baggage['key1'], 'value1')
        self.assertEqual(baggage['key2'], 'value2')

    def test_that_result_is_a_baggage_instance(self) -> None:
        self.assertIsInstance(
            headers.parse_baggage('a=b'), datastructures.Baggage
        )

    def test_that_ows_around_delimiters_is_ignored(self) -> None:
        self.assertEqual(
            headers.parse_baggage('key1 = value1 , key2 = value2'),
            headers.parse_baggage('key1=value1,key2=value2'),
        )

    def test_that_member_order_is_preserved(self) -> None:
        baggage = headers.parse_baggage('c=3,a=1,b=2')
        self.assertEqual(list(baggage), ['c', 'a', 'b'])

    def test_that_keys_are_case_sensitive(self) -> None:
        baggage = headers.parse_baggage('Key=upper,key=lower')
        self.assertEqual(baggage['Key'], 'upper')
        self.assertEqual(baggage['key'], 'lower')

    def test_that_duplicate_keys_keep_the_last_value(self) -> None:
        baggage = headers.parse_baggage('key=first,key=second')
        self.assertEqual(baggage['key'], 'second')
        self.assertEqual(len(baggage), 1)

    def test_that_empty_header_produces_empty_baggage(self) -> None:
        self.assertEqual(len(headers.parse_baggage('')), 0)

    def test_that_trailing_empty_members_are_ignored(self) -> None:
        self.assertEqual(headers.parse_baggage('key=value,'), {'key': 'value'})

    def test_that_empty_value_is_allowed(self) -> None:
        self.assertEqual(headers.parse_baggage('key=')['key'], '')

    def test_that_value_may_contain_equals_sign(self) -> None:
        self.assertEqual(headers.parse_baggage('key=a=b=c')['key'], 'a=b=c')


class BaggageDecodingTests(unittest.TestCase):
    def test_that_percent_encoded_octets_are_decoded(self) -> None:
        self.assertEqual(headers.parse_baggage('key=DF%2028')['key'], 'DF 28')

    def test_that_percent_sign_is_decoded(self) -> None:
        self.assertEqual(headers.parse_baggage('key=100%25')['key'], '100%')

    def test_that_utf8_sequences_are_decoded(self) -> None:
        self.assertEqual(
            headers.parse_baggage('key=%C3%A9')['key'],
            '\N{LATIN SMALL LETTER E WITH ACUTE}',
        )


class BaggagePropertyParsingTests(unittest.TestCase):
    def test_that_key_value_properties_are_parsed(self) -> None:
        baggage = headers.parse_baggage('key=value;ttl=30')
        self.assertEqual(list(baggage.get_properties('key')), [('ttl', '30')])

    def test_that_valueless_properties_are_parsed_as_none(self) -> None:
        baggage = headers.parse_baggage('key=value;secure')
        self.assertEqual(
            list(baggage.get_properties('key')), [('secure', None)]
        )

    def test_that_empty_property_value_differs_from_valueless(self) -> None:
        baggage = headers.parse_baggage('key=value;p1=;p2')
        self.assertEqual(
            list(baggage.get_properties('key')), [('p1', ''), ('p2', None)]
        )

    def test_that_property_values_are_decoded(self) -> None:
        baggage = headers.parse_baggage('key=value;note=a%20b')
        self.assertEqual(
            list(baggage.get_properties('key')), [('note', 'a b')]
        )

    def test_that_ows_around_properties_is_ignored(self) -> None:
        self.assertEqual(
            headers.parse_baggage('key=value ; ttl = 30 ; secure'),
            headers.parse_baggage('key=value;ttl=30;secure'),
        )


class BaggageStrictParsingTests(unittest.TestCase):
    def test_that_member_without_equals_is_skipped_when_lenient(self) -> None:
        baggage = headers.parse_baggage('bogus,key=value')
        self.assertEqual(baggage, {'key': 'value'})

    def test_that_member_without_equals_raises_when_strict(self) -> None:
        with self.assertRaises(errors.MalformedBaggage) as context:
            headers.parse_baggage('bogus', strict=True)
        self.assertEqual(context.exception.header_name, 'baggage')
        self.assertEqual(context.exception.header_value, 'bogus')

    def test_that_invalid_key_token_raises_when_strict(self) -> None:
        with self.assertRaises(errors.MalformedBaggage):
            headers.parse_baggage('bad key=value', strict=True)

    def test_that_invalid_value_octet_raises_when_strict(self) -> None:
        with self.assertRaises(errors.MalformedBaggage):
            headers.parse_baggage('key=with"quote', strict=True)

    def test_that_invalid_property_name_raises_when_strict(self) -> None:
        with self.assertRaises(errors.MalformedBaggage):
            headers.parse_baggage('key=value;bad name', strict=True)

    def test_that_invalid_property_value_octet_raises_when_strict(
        self,
    ) -> None:
        with self.assertRaises(errors.MalformedBaggage):
            headers.parse_baggage('key=value;note=a"b', strict=True)

    def test_that_empty_member_raises_when_strict(self) -> None:
        with self.assertRaises(errors.MalformedBaggage):
            headers.parse_baggage('key=value,,other=1', strict=True)

    def test_that_malformed_baggage_is_a_value_error(self) -> None:
        with self.assertRaises(ValueError):
            headers.parse_baggage('bogus', strict=True)


class BaggageRoundTripTests(unittest.TestCase):
    def test_that_parsing_and_serializing_round_trips(self) -> None:
        header = 'userId=alice,serverNode=DF%2028;ttl=30;secure'
        self.assertEqual(str(headers.parse_baggage(header)), header)

    def test_that_reserved_characters_are_re_encoded(self) -> None:
        baggage = headers.parse_baggage('key=a%2Cb%3Bc')
        self.assertEqual(baggage['key'], 'a,b;c')
        self.assertEqual(str(baggage), 'key=a%2Cb%3Bc')
