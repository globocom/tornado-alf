# -*- coding: utf-8 -*-

from mock import patch, Mock
from . import mkfuture, mkfuture_exception
from tornadoalf.manager import TokenManager, Token, TokenError
from tornado.testing import AsyncTestCase, gen_test


class TestTokenManager(AsyncTestCase):

    def setUp(self):
        super(TestTokenManager, self).setUp()
        self.end_point = 'http://endpoint/token'
        self.client_id = 'client_id'
        self.client_secret = 'client_secret'
        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret)
        self._fake_fetch = Mock()
        self.manager._fetch = self._fake_fetch

    def test_should_start_with_no_token(self):
        self.assertFalse(self.manager._has_token())

    def test_should_detect_expired_token(self):
        self.manager._token = Token('', expires_in=0)
        self.assertFalse(self.manager._has_token())

    def test_should_respect_valid_token(self):
        self.manager._token = Token('', expires_in=10)
        self.assertTrue(self.manager._has_token())

    def test_should_reset_token(self):
        self.manager.reset_token()

        self.assertEqual(self.manager._token.access_token, '')
        self.assertEqual(self.manager._token._expires_in, 0)

    @gen_test
    def test_should_be_able_to_request_a_new_token(self):
        self._fake_fetch.return_value = mkfuture({
            'access_token': 'accesstoken',
            'expires_in': 10,
        })

        yield self.manager._request_token()

        self._fake_fetch.assert_called_with(
            url=self.end_point,
            method="POST",
            auth=(self.client_id, self.client_secret),
            data={'grant_type': 'client_credentials'},
        )

    @gen_test
    def test_should_raise_token_error_for_bad_token(self):
        fake_response = Mock(error=Exception('fail'), status_code=500)
        self._fake_fetch.return_value = mkfuture_exception(
            TokenError('error', fake_response)
        )

        with self.assertRaises(TokenError) as context:
            yield self.manager._request_token()

        self.assertEqual(context.exception.response.status_code, 500)

    @gen_test
    def test_get_token_data_should_obtain_new_token(self):
        _request_token = Mock()
        _request_token.return_value = mkfuture({
            'access_token': 'new_access_token',
            'expires_in': 10,
        })
        self.manager._request_token = _request_token
        yield self.manager._get_token_data()

        self.assertTrue(_request_token.called)

    @gen_test
    def test_update_token_should_set_a_token_with_data_retrieved(self):
        _request_token = Mock()
        _request_token.return_value = mkfuture({
            'access_token': 'new_access_token',
            'expires_in': 10,
        })
        self.manager._request_token = _request_token
        self.manager._token = Token('access_token', expires_in=100)

        yield self.manager._update_token()

        self.assertTrue(_request_token.called)

        self.assertEqual(self.manager._token.access_token, 'new_access_token')
        self.assertEqual(self.manager._token._expires_in, 10)

    @gen_test
    def test_should_return_token_value(self):
        self.manager._token = Token('access_token', expires_in=10)
        token = yield self.manager.get_token()
        self.assertEqual(token, 'access_token')

    @gen_test
    @patch('tornadoalf.manager.TokenManager._update_token')
    @patch('tornadoalf.manager.TokenManager._has_token')
    def test_get_token_should_request_a_new_token_if_do_not_have_a_token(
            self, _has_token, _update_token):

        _has_token.return_value = False

        self.manager.get_token()

        self.assertTrue(_update_token.called)


class TestTokenManagerHTTP(AsyncTestCase):

    def setUp(self):
        super(TestTokenManagerHTTP, self).setUp()
        self.end_point = 'http://endpoint/token'
        self.client_id = 'client_id'
        self.client_secret = 'client_secret'
        self.http_options = {'request_timeout': 2}

    @gen_test
    def test_work_with_no_http_options(self):
        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret)
        self._fake_fetch = Mock()
        self.manager._http_client.fetch = self._fake_fetch

        fake_response = Mock(body=b'{"access_token":"access","expires_in":10}')
        self._fake_fetch.return_value = mkfuture(fake_response)

        yield self.manager._request_token()
        request = self._fake_fetch.call_args[0][0]
        assert request.request_timeout is None

    @gen_test
    def test_should_use_http_options(self):
        self.manager = TokenManager(self.end_point,
                                    self.client_id,
                                    self.client_secret,
                                    self.http_options)
        self._fake_fetch = Mock()
        self.manager._http_client.fetch = self._fake_fetch

        fake_response = Mock(
            body=b'{"access_token":"access","expires_in":10}')
        self._fake_fetch.return_value = mkfuture(fake_response)

        yield self.manager._request_token()
        request = self._fake_fetch.call_args[0][0]
        self.assertEqual(request.request_timeout, 2)
        self.assertEqual(request.headers['Authorization'],
                         'Basic Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ=')
