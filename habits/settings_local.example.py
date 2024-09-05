"""
Individual developer-specific settings.

This module provides additional configuration for your specific needs as a developer.
It should never be tracked.
"""

from .settings_dev import *

# Django Debug Toolbar configuration
try:
    import debug_toolbar
except ImportError:
    pass
else:
    INSTALLED_APPS.insert(
        INSTALLED_APPS.index('django.contrib.staticfiles') + 1,
        'debug_toolbar'
    )
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
