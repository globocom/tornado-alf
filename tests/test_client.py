# -*- coding: utf-8 -*-

from mock import patch, Mock
from unittest import TestCase
from . import mkfuture

from tornado import gen
from tornado.testing import AsyncTestCase, gen_test
from tornadoalf.manager import TokenManager
from tornadoalf.client import Client


class TestClient(AsyncTestCase):

    end_point = 'http://endpoint/token'
    resource_url = 'http://api/some/resource'

    def test_Client_should_have_a_variable_with_a_token_manager_class(self):
        self.assertEquals(Client.token_manager_class, TokenManager)

    def test_token_manager_object_should_be_an_instance_of_token_manager_class(self):
        client = Client(token_endpoint=self.end_point, client_id='client-id', client_secret='client_secret')

        self.assertTrue(isinstance(client._token_manager, client.token_manager_class))

    @patch('tornadoalf.client.TokenManager')
    @patch('tornadoalf.client.Client._authorized_fetch')
    def test_should_retry_a_bad_request_once(self, Manager, f_fetch):
        f_fetch.return_value = mkfuture(Mock(code=401))
        self._fake_manager(Manager, has_token=False)

        yield self._request(Manager)

        self.assertEqual(request.call_count, 2)

    @patch('tornadoalf.client.Client._authorized_fetch')
    def test_should_stop_the_request_when_token_fails(self, f_fetch):
        f_fetch.return_value = mkfuture(Mock(code=500, error=Exception('fail')))

        client = Client(
            token_endpoint=self.end_point,
            client_id='client_id',
            client_secret='client_secret'
        )

        response = yield client.fetch(self.resource_url, method="GET")

        self.assertEqual(response.code, 500)

    @patch('tornadoalf.client.Client._authorized_fetch')
    @patch('tornadoalf.client.TokenManager.reset_token')
    def test_should_reset_token_when_token_fails(self, reset_token, _authorized_fetch):
        _authorized_fetch.return_value = mkfuture(Mock(code=500, error=Exception('fail')))

        client = Client(
            token_endpoint=self.end_point,
            client_id='client_id',
            client_secret='client_secret'
        )

        response = yield client.fetch(self.resource_url, method="GET")
        self.assertTrue(reset_token.called)
        self.assertEqual(response.status_code, 500)

    @patch('tornadoalf.client.TokenManager._has_token')
    @patch('tornadoalf.client.TokenManager.reset_token')
    @patch('tornadoalf.client.Client._authorized_fetch')
    def test_should_reset_token_when_gets_an_unauthorized_error(self, _authorized_fetch, reset_token, _has_token):
        _authorized_fetch.return_value = mkfuture(Mock(code=401))
        _has_token.return_value = True

        client = Client(
            token_endpoint=self.end_point,
            client_id='client_id',
            client_secret='client_secret'
        )

        response = yield client.fetch(self.resource_url, method="GET")

        self.assertTrue(reset_token.called)
        self.assertEqual(response.code, 401)

    @gen.coroutine
    def _request(self, manager):
        class ClientTest(Client):
            token_manager_class = manager

        client = ClientTest(
            token_endpoint=self.end_point,
            client_id='client_id',
            client_secret='client_secret')

        result = yield client.fetch('GET', self.resource_url)
        raise gen.Return(result)

    def _fake_manager(self, Manager, has_token=True, access_token='', code=200):
        if not isinstance(access_token, list):
            access_token = [access_token]

        access_token.reverse()

        manager = Mock()
        manager._has_token.return_value = has_token
        manager.get_token.return_value = mkfuture(access_token[0])
        manager.request_token.return_value = mkfuture(Mock(
            status_code=status_code, error=(code == 200 and None or Exception('error'))))
        Manager.return_value = manager

        return manager
