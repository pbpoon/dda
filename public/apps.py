#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/6
from django.apps import AppConfig


class PublicConfig(AppConfig):
    name = 'public'

    def ready(self):
        import public.signal