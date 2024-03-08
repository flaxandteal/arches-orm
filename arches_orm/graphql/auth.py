import os
import binascii
from asgiref.sync import sync_to_async
from oauth2_provider.models import AccessToken, get_application_model
from oauth2_provider.oauth2_backends import OAuthLibCore
from oauthlib.common import Request as OauthlibRequest

from starlette_context import context
from starlette.authentication import (
    AuthCredentials, AuthenticationBackend, AuthenticationError, SimpleUser
)
from django.contrib.auth import authenticate
from django.http.request import HttpRequest

ALLOW_ANONYMOUS = os.environ.get("ALLOW_ANONYMOUS", False)

oauth_lib = OAuthLibCore()
authenticator = oauth_lib.server.request_validator.authenticate_client
validate_bearer_token = oauth_lib.server.request_validator.validate_bearer_token

class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        context.data["user"] = None
        if "Authorization" not in conn.headers:
            # FIXME: for now, allow anonymous internal access
            if ALLOW_ANONYMOUS:
                return AuthCredentials(["anonymous"]), SimpleUser("anonymous")
            else:
                raise AuthenticationError("Require basic auth credentials")

        auth = conn.headers["Authorization"]
        try:
            scheme, token = auth.split()
            if scheme.lower() not in ('basic', 'bearer'):
                raise AuthenticationError('Invalid basic/bearer auth credentials')

        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError('Invalid basic auth credentials')

        uri = conn.url.path
        oauth_request = OauthlibRequest(
                uri, "POST", b"", {"HTTP_AUTHORIZATION": conn.headers["Authorization"]}
        )
        if scheme.lower() == "basic":
            if not await sync_to_async(authenticator)(oauth_request):
                raise AuthenticationError('Incorrect basic auth credentials found')

            def get_user(request):
                return request.client.user
            user = await sync_to_async(get_user)(oauth_request)
        else:
            request = HttpRequest()
            request.path = uri
            request.META.update(conn.headers)
            user = await sync_to_async(authenticate)(request)
        if user:
            context.data["user"] = user
            return AuthCredentials(["authenticated"]), SimpleUser(user.username)

        raise AuthenticationError('Incorrect auth credentials')

