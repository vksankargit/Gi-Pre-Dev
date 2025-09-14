"""
WSGI config for pre_system project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')

application = get_wsgi_application()