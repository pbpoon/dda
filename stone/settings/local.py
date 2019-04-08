#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/1
from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'stone_dev',
        # 'NAME': 'stone_test',
        'USER': 'stone',
        'PASSWORD': 'password'
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
DEBUG = True
ALLOWED_HOSTS = []
SECRET_KEY = 'd6!)x_zzgf_u=^h^u+-7y7^23!az4n6e4bn1jkdq4@okj65%nv'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
STATIC_ROOT = os.path.join(BASE_DIR, "uuu")
INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_CONFIG = {'JQUERY_URL': '/static/js/jquery-3.3.1.min.js'}
