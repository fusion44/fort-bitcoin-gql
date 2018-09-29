"""Adapted from https://github.com/SmileyChris/graphql-ws/tree/channels2/graphql_ws/django (MIT)
"""

import traceback

import jwt
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist
from django.urls import path
from jwt import DecodeError, ExpiredSignatureError, InvalidSignatureError

from backend.subscriptions.consumers import GraphQLSubscriptionConsumer


class TokenAuthMiddleware:
    """
    Token authorization middleware for Django Channels 2
    https://github.com/jaquan1227/django-channel-jwt-auth

    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        headers = dict(scope["headers"])
        token_name = None
        token_key = None
        scope['user'] = AnonymousUser()

        if b"authorization" in headers:
            token_name, token_key = headers[b'authorization'].decode().split()

        if token_name.startswith("JWT"):
            try:
                user_jwt = jwt.decode(
                    token_key,
                    settings.SECRET_KEY,
                )
                scope["user"] = User.objects.get(id=user_jwt["user_id"])
            except (InvalidSignatureError, KeyError, ExpiredSignatureError,
                    DecodeError, ObjectDoesNotExist):
                traceback.print_exc()

        return self.inner(scope)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))

if apps.is_installed("django.contrib.auth"):
    from channels.auth import AuthMiddlewareStack
else:
    AuthMiddlewareStack = None

websocket_urlpatterns = [path("subscriptions", GraphQLSubscriptionConsumer)]

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns)
})

session_application = ProtocolTypeRouter({
    "websocket":
    TokenAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
})

if AuthMiddlewareStack:
    auth_application = ProtocolTypeRouter({
        "websocket":
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    })
