import unittest

from fluenttest import test_case

from ietfparse import headers


class WhenParsingSimpleContentType(test_case.TestCase, unittest.TestCase):

    @classmethod
    def act(cls):
        cls.parsed = headers.parse_content_type('text/plain')

    def test_that_type_is_parsed(self):
        self.assertEqual(self.parsed.content_type, 'text')

    def test_that_subtype_is_parsed(self):
        self.assertEqual(self.parsed.content_subtype, 'plain')

    def test_that_no_parameters_are_found(self):
        self.assertEqual(self.parsed.parameters, {})


class WhenParsingComplexContentType(test_case.TestCase, unittest.TestCase):

    @classmethod
    def act(cls):
        cls.parsed = headers.parse_content_type(
            'message/HTTP; version=2.0 (someday); MsgType="request"')

    def test_that_type_is_parsed(self):
        self.assertEqual(self.parsed.content_type, 'message')

    def test_that_subtype_is_parsed(self):
        self.assertEqual(self.parsed.content_subtype, 'http')

    def test_that_version_parameter_is_parsed(self):
        self.assertEqual(self.parsed.parameters['version'], '2.0')

    def test_that_message_type_parameter_is_parsed(self):
        self.assertEqual(self.parsed.parameters['msgtype'], 'request')
