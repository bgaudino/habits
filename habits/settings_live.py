"""
Settings suitable for use on sites resolvable over the public internet.

This module provides the base configuration for staging and production (and other potential)
live environments.
"""

from .settings import *

DEBUG = False

ALLOWED_HOSTS = ['habit.fly.dev']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
