from .settings import * # noqa: F403

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "guardian",
    "oauth2_provider",
    "arches",
    "arches.app.models",
)
OAUTH_CLIENT_ID = ''
