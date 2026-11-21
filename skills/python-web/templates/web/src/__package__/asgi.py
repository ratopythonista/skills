"""ASGI entry point used by Granian.

In development the ASGI static handler serves the app's static files; with
``DEBUG=0`` run ``collectstatic`` and let the front proxy serve them.
"""

import os

from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler  # ty: ignore[missing-module-member]  # django-types stub gap
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{PACKAGE}}.settings")

application = get_asgi_application()
if settings.DEBUG:
    application = ASGIStaticFilesHandler(application)
