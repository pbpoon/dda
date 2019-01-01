#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/1
from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'stone',
        'USER': 'stone',
        'PASSWORD': 'fangfang@1987'
    }
}
DEBUG = True
ALLOWED_HOSTS = ['120.78.136.222', '127.0.0.1']
