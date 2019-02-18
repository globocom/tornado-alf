#
# encoding: utf-8

import datetime

from unittest import TestCase
from mock import MagicMock
from tornadoalf.token import Token, TokenHTTPError
from tornado.httpclient import HTTPResponse


class TestToken(TestCase):

    def test_should_have_an_access_token(self):
        token = Token(access_token='access_token')
        self.assertEqual(token.access_token, 'access_token')

    def test_should_know_when_it_has_expired(self):
        token = Token(access_token='access_token', expires_in=0)
        self.assertFalse(token.is_valid())

    def test_should_know_when_it_is_valid(self):
        token = Token(access_token='access_token', expires_in=10)
        self.assertTrue(token.is_valid())

    def test_expires_on_using_utc(self):
        token = Token(access_token='access_token', expires_in=10)
        self.assertTrue(token.expires_on > datetime.datetime.utcnow())
        self.assertTrue(
            token.expires_on <
            datetime.datetime.utcnow() + datetime.timedelta(seconds=15))


class TestTokenHTTPError(TestCase):

    def test_should_show_http_response_in_exception(self):
        buf = MagicMock()
        buf.getvalue.return_value = '{"myError": true}'

        request = MagicMock()
        response = HTTPResponse(
            request=request, code=401, buffer=buf)

        err = TokenHTTPError('My Error', response)

        self.assertEqual(
            str(err),
            'My Error, StatusCode: 401, Body: {"myError": true}')
