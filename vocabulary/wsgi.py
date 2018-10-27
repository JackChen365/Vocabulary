"""
WSGI config for vocabulary project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
WORK_DIRECTORY = os.path.join(CURRENT_DIRECTORY, '..')
# adding the project to the python path
sys.path.append(WORK_DIRECTORY)
# adding the parent directory to the python path
sys.path.append(os.path.join(WORK_DIRECTORY, '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vocabulary.settings')
application = get_wsgi_application()
