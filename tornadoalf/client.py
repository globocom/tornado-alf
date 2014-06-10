#
# encoding: utf-8

from tornado.httpclient import AsyncHTTPClient
from tornado import gen
from tornadoalf.manager import TokenManager, TokenError

import logging


BAD_TOKEN = 401


class Client(object):

    token_manager_class = TokenManager

    def __init__(self, client_id, client_secret, token_endpoint):
        self._http_client = AsyncHTTPClient()
        self._token_manager = self.token_manager_class(
            token_endpoint=token_endpoint,
            client_id=client_id,
            client_secret=client_secret)

    @gen.coroutine
    def fetch(self, request, callback=None, **kwargs):
        try:
            response = yield self._authorized_fetch(request, callback, **kwargs)
            if response.code != BAD_TOKEN:
                raise gen.Return(response)

            self._token_manager.reset_token()
            response = yield self._authorized_fetch(request, callback, **kwargs)
            raise gen.Return(response)

        except TokenError:
            self._token_manager.reset_token()
            raise

    @gen.coroutine
    def _authorized_fetch(self, request, callback, **kwargs):
        access_token = yield self._token_manager.get_token()
        request.headers['Authorization'] = 'Bearer {}'.format(access_token)

        logging.info('tornadoalf request:%s %s\n%s\n%s' % (request.method, request.url, request.headers, request.body))

        result = yield self._http_client.fetch(request, callback, **kwargs)
        raise gen.Return(result)
