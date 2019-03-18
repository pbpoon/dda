#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/3/18
import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stone.settings.local")
django.setup()


def my_scheduled_job():
    from datetime import datetime
    from .models.leads import SalesLeads
    s = SalesLeads.objects.first()
    s.comments.create(user_id=1, content='test%s' % datetime.now())


def test():
    print('123')

my_scheduled_job()
