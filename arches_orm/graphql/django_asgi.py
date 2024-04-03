import os
from asgiref.sync import sync_to_async
import django
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    raise RuntimeError("DJANGO_SETTINGS_MODULE must be explicitly set")

async def app(scope, receive, send):
    await sync_to_async(django.setup)()
    import importlib
    _asgi = await sync_to_async(importlib.import_module)("arches_orm.graphql._asgi")
    await _asgi.app(scope, receive, send)
