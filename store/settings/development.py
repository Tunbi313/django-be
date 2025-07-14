"""
Development settings.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'web',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': 'localhost',  # hoặc IP của server PostgreSQL
        'PORT': '5432',       # cổng mặc định của PostgreSQL
    }
}

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True 