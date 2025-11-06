"""
ASGI config for pre_system project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')

application = get_asgi_application()