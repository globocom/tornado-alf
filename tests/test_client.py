# -*- coding: utf-8 -*-

from mock import patch, Mock
from . import mkfuture

from tornado import gen
from tornado.httpclient import HTTPError
from tornado.testing import AsyncTestCase, gen_test
from tornadoalf.manager import TokenManager, TokenError
from tornadoalf.client import Client


class TestClient(AsyncTestCase):

    end_point = 'http://endpoint/token'
    resource_url = 'http://api/some/resource'

    def test_Client_should_have_a_variable_with_a_token_manager_class(self):
        self.assertEquals(Client.token_manager_class, TokenManager)

    def test_manager_should_be_a_token_manager_class(self):
        client = Client(token_endpoint=self.end_point,
                        client_id='client-id', client_secret='client_secret')

        self.assertTrue(
            isinstance(client._token_manager, client.token_manager_class)
        )

    @gen_test
    @patch('tornadoalf.client.TokenManager')
    def test_should_return_a_good_request(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('tornadoalf.client.Client._authorized_fetch') as (
                   _authorized_fetch):

            response = Mock(code=200, error=None)
            _authorized_fetch.return_value = mkfuture(response)
            response = yield self._request(Manager)
            self.assertEqual(response.code, 200)
            self.assertEqual(manager.reset_token.call_count, 0)
            self.assertEqual(_authorized_fetch.call_count, 1)

    @gen_test
    @patch('tornadoalf.client.TokenManager')
    def test_should_raise_a_bad_request(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('tornadoalf.client.Client._authorized_fetch') as (
                   _authorized_fetch):

            error = HTTPError(400)
            response = Mock(code=400, error=error)
            _authorized_fetch.return_value = mkfuture(response)

            try:
                response = yield self._request(Manager)

                # to ensures that code breaks into an exception
            except Exception as err:
                self.assertEqual(err.code, 400)
                self.assertEqual(_authorized_fetch.call_count, 1)
                self.assertEqual(manager.reset_token.call_count, 0)
            else:
                assert False, "Not raised an exception"

    @gen_test
    @patch('tornadoalf.client.TokenManager')
    def test_should_return_a_bad_request_when_turn_off_raise_error(
            self, Manager):

        manager = self._fake_manager(Manager, has_token=False)

        with patch('tornadoalf.client.Client._authorized_fetch') as (
                   _authorized_fetch):

            error = HTTPError(400)
            response = Mock(code=400, error=error)
            _authorized_fetch.return_value = mkfuture(response)

            response = yield self._request(Manager, raise_error=False)

            self.assertEqual(response.code, 400)
            self.assertEqual(_authorized_fetch.call_count, 1)
            self.assertEqual(manager.reset_token.call_count, 0)

    @gen_test
    @patch('tornadoalf.client.TokenManager')
    def test_should_retry_a_bad_token_request_once(self, Manager):
        self._fake_manager(Manager, has_token=False)

        with patch('tornadoalf.client.Client._authorized_fetch') as (
                   _authorized_fetch):

            _authorized_fetch.return_value = mkfuture(Mock(code=401))
            response = yield self._request(Manager)
            self.assertEqual(response.code, 401)
            self.assertEqual(_authorized_fetch.call_count, 2)

    @gen_test
    @patch('tornadoalf.client.TokenManager')
    def test_should_reset_token_when_token_fails(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('tornadoalf.client.Client._authorized_fetch') as (
                   _authorized_fetch):

            _authorized_fetch.return_value = mkfuture(Mock(code=401))
            response = yield self._request(Manager)
            self.assertEqual(response.code, 401)
            self.assertEqual(manager.reset_token.call_count, 1)

    @gen_test
    @patch('tornadoalf.client.TokenManager')
    def test_should_reset_token_when_gets_a_token_error(self, Manager):
        manager = self._fake_manager(Manager, has_token=False)

        with patch('tornadoalf.client.Client._authorized_fetch') as (
                   _authorized_fetch):

            _authorized_fetch.side_effect = TokenError('boom', 'boom')
            try:
                yield self._request(Manager)
            except TokenError as e:
                if hasattr(e, 'message'):
                    self.assertEqual(e.message, 'boom')
                elif hasattr(e, 'response'):
                    self.assertEqual(e.response, 'boom')
                else:
                    assert False, 'Should not have got this far'
                self.assertEqual(_authorized_fetch.call_count, 1)
                self.assertEqual(manager.reset_token.call_count, 1)
            else:
                assert False, 'Should not have got this far'

    @gen.coroutine
    def _request(self, manager, **kwargs):
        class ClientTest(Client):
            token_manager_class = manager

        client = ClientTest(
            token_endpoint=self.end_point,
            client_id='client_id',
            client_secret='client_secret')

        result = yield client.fetch(self.resource_url, method='GET', **kwargs)
        raise gen.Return(result)

    def _fake_manager(self, Manager, has_token=True,
                      access_token='', code=200):
        if not isinstance(access_token, list):
            access_token = [access_token]

        access_token.reverse()

        manager = Mock()
        manager._has_token.return_value = has_token
        manager.get_token.return_value = mkfuture(access_token[0])
        manager.reset_token.return_value = mkfuture(None)
        manager.request_token.return_value = mkfuture(Mock(
            code=code,
            error=(code == 200 and None or Exception('error'))
        ))

        Manager.return_value = manager

        return manager
