#
# encoding: utf-8
import logging

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornadoalf.manager import TokenManager, TokenError

BAD_TOKEN = 401

logger = logging.getLogger(__name__)


class Client:

    token_manager_class = TokenManager

    def __init__(self, client_id, client_secret,
                 token_endpoint, http_options=None):
        http_options = {} if http_options is None else http_options
        self._http_client = AsyncHTTPClient()
        self._token_manager = self.token_manager_class(
            token_endpoint=token_endpoint,
            client_id=client_id,
            client_secret=client_secret,
            http_options=http_options)

    async def fetch(self, request, raise_error=True, **kwargs):
        """Executes a request by AsyncHTTPClient,
        asynchronously returning an `tornado.HTTPResponse`.

           The ``raise_error=False`` argument currently suppresses
           *all* errors, encapsulating them in `HTTPResponse` objects
           following the tornado http-client standard

            The ``callback`` argument was removed. Use the await.
        """
        # accepts request as string then convert it to HTTPRequest
        if isinstance(request, str):
            request = HTTPRequest(request, **kwargs)

        try:
            # The first request calls tornado-client ignoring the
            # possible exception, in case of 401 response,
            # renews the access token and replay it
            response = await self._authorized_fetch(request,
                                                    raise_error=False,
                                                    **kwargs)

            if response.code == BAD_TOKEN:
                await self._token_manager.reset_token()
            elif response.error and raise_error:
                raise response.error
            else:
                return response

            # The request with renewed token
            response = await self._authorized_fetch(request,
                                                    raise_error=raise_error,
                                                    **kwargs)
            return response

        except TokenError as err:
            await self._token_manager.reset_token()
            raise err

    async def _authorized_fetch(self, request, **kwargs):
        access_token = await self._token_manager.get_token()
        request.headers['Authorization'] = f'Bearer {access_token}'

        logger.debug('Request: %s %s', request.method, request.url)
        for header in request.headers:
            logger.debug('Header %s: %s', header, request.headers[header])

        return await self._http_client.fetch(request, **kwargs)
