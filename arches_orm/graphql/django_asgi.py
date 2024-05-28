import os
from asgiref.sync import sync_to_async
import django
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    raise RuntimeError("DJANGO_SETTINGS_MODULE must be explicitly set")

django.setup()
from arches_orm.graphql import _asgi

async def app(scope, receive, send):
    await _asgi.app(scope, receive, send)
