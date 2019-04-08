#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/3/18
from django.core.management.base import BaseCommand
from django.utils import timezone
class Command(BaseCommand):
    """
    自定义命令
    """

    def handle(self, *args, **options):
        from action.models import SchemeWxPush
        from datetime import datetime
        now = datetime.now()
        print(now)
        now_pushs = SchemeWxPush.objects.filter(
            time__year=now.year,
            time__month=now.month,
            time__day=now.day,
            time__hour=now.hour,
            time__minute=now.minute,
        )
        for push in now_pushs:
            push.sent_msg()
            print(push)
