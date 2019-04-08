#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/3/18
from django.core.management.base import BaseCommand
from datetime import datetime


class Command(BaseCommand):
    """
    每日总结
    #开单数量
        共几多单，数量，金额，
    #界石数量
        几颗料，
    #提货数量
    """

    def handle(self, *args, **options):
        from datetime import datetime
        from action.models import SchemeWxPush
        now = datetime.now()
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
