#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/3/18
from django.core.management.base import BaseCommand
from datetime import datetime


class Command(BaseCommand):
    """
    自定义命令
    """


    def handle(self, *args, **options):
        from sales.models import SalesLeads
        s = SalesLeads.objects.first()
        print(s)
        s.comments.create(user_id=1, content='test%s' % datetime.now())
        print('ok')