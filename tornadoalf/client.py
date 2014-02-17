#
# encoding: utf-8

from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from tornadoalf.manager import TokenManager


class Client(AsyncHTTPClient):

    token_manager_class = TokenManager

    def __new__(cls, *args, **kwargs):
        client_id = kwargs.pop('client_id')
        client_secret = kwargs.pop('client_secret')
        token_endpoint = kwargs.pop('token_endpoint')
        instance = super(Client, cls).__new__(cls, *args, **kwargs)
        instance.set_client_access(client_id, client_secret, token_endpoint)
        return instance

    def set_client_access(self, client_id, client_secret, token_endpoint):
        self._token_manager = self.token_manager_class(
            token_endpoint=token_endpoint,
            client_id=client_id,
            client_secret=client_secret)

    @gen.coroutine
    def fetch(self, request, callback=None, **kwargs):
        access_token = yield self._token_manager.get_token()
        request.headers['Authorization'] = 'Bearer {}'.format(access_token)
        result = yield gen.Task(super(Client, self).fetch, request, callback, **kwargs)
        raise gen.Return(result)
