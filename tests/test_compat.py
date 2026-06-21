import enum
import unittest

from ietfparse import _compat


class StrEnumTests(unittest.TestCase):
    def test_strenum_members_render_as_values(self) -> None:
        class Example(_compat.StrEnum):
            VALUE = 'value'

        self.assertEqual(str(Example.VALUE), 'value')
        self.assertEqual(f'{Example.VALUE}', 'value')

    def test_strenum_members_remain_strings(self) -> None:
        class Example(_compat.StrEnum):
            VALUE = 'value'

        self.assertEqual(Example.VALUE, 'value')
        self.assertIsInstance(Example.VALUE, str)

    def test_strenum_uses_stdlib_when_available(self) -> None:
        if hasattr(enum, 'StrEnum'):
            self.assertIs(_compat.StrEnum, enum.StrEnum)
        else:
            self.assertTrue(issubclass(_compat.StrEnum, enum.Enum))

    def test_assert_never_raises_assertion_error(self) -> None:
        with self.assertRaisesRegex(
            AssertionError, 'Expected code to be unreachable'
        ):
            _compat.assert_never('value')  # ty: ignore[invalid-argument-type]
