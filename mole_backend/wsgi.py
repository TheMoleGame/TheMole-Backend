"""
WSGI config for mole_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import socketio

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mole_backend.settings")
django_app = get_wsgi_application()

from mole.views import sio

application = socketio.WSGIApp(sio, django_app)

from mole.db_init import *

# Initialize the database the first time
db_init()
