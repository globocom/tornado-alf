# -*- coding: utf-8 -*-
from base64 import b64encode
from tornadoalf.token import Token, TokenError
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado import gen
try:
    from simplejson import json
except ImportError:
    import json

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import logging


class TokenManager(object):

    def __init__(self, token_endpoint, client_id, client_secret, http_options=None):
        self._token_endpoint = token_endpoint
        self._client_id = client_id
        self._client_secret = client_secret
        self._token = Token()
        self._http_options = http_options is None and {} or http_options
        self._http_client = AsyncHTTPClient()

    def _has_token(self):
        return self._token.is_valid()

    @gen.coroutine
    def get_token(self):
        if not self._has_token():
            yield self._update_token()
        raise gen.Return(self._token.access_token)

    @gen.coroutine
    def _get_token_data(self):
        token_data = yield self._request_token()
        raise gen.Return(token_data)

    def reset_token(self):
        self._token = Token()

    @gen.coroutine
    def _update_token(self):
        token_data = yield self._get_token_data()
        self._token = Token(token_data.get('access_token', ''),
                            token_data.get('expires_in', 0))

    @gen.coroutine
    def _request_token(self):
        if not self._token_endpoint:
            raise TokenError('Missing token endpoint')

        token_data = yield self._fetch(
            url=self._token_endpoint,
            method="POST",
            auth=(self._client_id, self._client_secret),
            data={'grant_type': 'client_credentials'}
        )

        raise gen.Return(token_data)

    @gen.coroutine
    def _fetch(self, url, method="GET", data=None, auth=None):
        if type(data) == dict:
            data = urlencode(data)

        request_data = dict(
            url=url,
            headers={},
            method=method,
            body=data
        )

        if auth is not None:
            try:
                passhash = b64encode(':'.join(auth))
            except TypeError as e:
                raise TokenError('Missing credentials (client_id:client_secret)', e.message)
            request_data['headers']['Authorization'] = 'Basic %s' % passhash

        request_data.update(self._http_options)
        request = HTTPRequest(**request_data)
        logging.info('request:%s %s\n%s\n%s' % (request.method, request.url, request.headers, request.body))
        try:
            response = yield self._http_client.fetch(request)
        except HTTPError as e:
            raise TokenError('Failed to request token', e)
        result = json.loads(response.body)
        raise gen.Return(result)
