#
# encoding: utf-8
import logging

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen
from tornadoalf.manager import TokenManager, TokenError

BAD_TOKEN = 401

logger = logging.getLogger(__name__)


class Client(object):

    token_manager_class = TokenManager

    def __init__(self, client_id, client_secret,
                 token_endpoint, http_options=None):
        http_options = http_options is None and {} or http_options
        self._http_client = AsyncHTTPClient()
        self._token_manager = self.token_manager_class(
            token_endpoint=token_endpoint,
            client_id=client_id,
            client_secret=client_secret,
            http_options=http_options)

    @gen.coroutine
    def fetch(self, request, callback=None, **kwargs):

        # accepts request as string then convert it to HTTPRequest
        if isinstance(request, str):
            request = HTTPRequest(request, **kwargs)

        try:
            response = yield self._authorized_fetch(request,
                                                    callback,
                                                    **kwargs)
            if response.code != BAD_TOKEN:
                raise gen.Return(response)

            yield self._token_manager.reset_token()
            response = yield self._authorized_fetch(request,
                                                    callback,
                                                    **kwargs)
            raise gen.Return(response)

        except TokenError as err:
            yield self._token_manager.reset_token()
            raise err

    @gen.coroutine
    def _authorized_fetch(self, request, callback, **kwargs):
        access_token = yield self._token_manager.get_token()
        request.headers['Authorization'] = 'Bearer {}'.format(access_token)

        logger.debug('Request: %s %s', request.method, request.url)
        for header in request.headers:
            logger.debug('Header %s: %s', header, request.headers[header])

        result = yield self._http_client.fetch(request, callback, **kwargs)
        raise gen.Return(result)
