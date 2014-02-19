tornado-alf
===========

Tornado OAuth 2 Client
---------------------

`tornado-alf` is a OAuth 2 Client base on the tornado's AsyncHTTPClient

Features
--------

* Automatic token retrieving and renewing
* Token expiration control
* Automatic retry on status 401 (UNAUTHORIZED)

Usage
-----

Initialize the client and use it as a AsyncHTTPClient object.

.. code-block:: python

    from tornadoalf.client import Client

    client = Client(
        token_endpoint='http://example.com/token',
        client_id='client-id',
        client_secret='secret')

    resource_uri = 'http://example.com/resource'

    response = yield client.fetch(resource_uri,
        method='POST', body='{"name": "alf"}',
        headers={'Content-Type': 'application/json'})


How it works?
-------------

Before any request the client tries to retrive a token on the endpoint,
expecting a JSON response with the ``access_token`` and ``expires_in`` keys.

The client keeps the token until it is expired, according to the ``expires_in``
value.

After getting the token, the request is issued with a `Bearer authorization
header <http://tools.ietf.org/html/draft-ietf-oauth-v2-31#section-7.1>`_:

.. code-block::

    GET /resource/1 HTTP/1.1
    Host: example.com
    Authorization: Bearer token

If the request fails with a 401 (UNAUTHORIZED) status, a new token is retrieved
from the endpoint and the request is retried. This happens only once, if it
fails again the error response is returned.


Troubleshooting
---------------

In case of an error retrieving a token, the error response will be returned,
the real request won't happen.


Related projects
----------------

This project tries to be an adaptaion to tornado of
`alf <https://github.com/globocom/alf>`_

