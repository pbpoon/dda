#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/3/18
from django.core.management.base import BaseCommand
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from account.views import get_day_daily
from django.conf import settings


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
        from action.models import SchemeWxPush
        now = timezone.now()
        kwargs = {'year': now.year, 'month': now.month, 'day': now.day}
        data = get_day_daily(**kwargs)
        desc = f'收付款:{data["payments"].count()}笔\n'
        desc += f'账单:{data["invoices"].count()}张\n'
        desc += f'销售订单:{data["sales_orders"].count()}张\n'
        desc += f'出入库:{data["inout_orders"].count()}张\n'
        desc += f'运输单:{data["move_orders"].count()}张\n'
        desc += f'生产单:{data["production_orders"].count()}张\n'
        path = f'{settings.DEFAULT_DOMAIN}{reverse_lazy("day_daily", kwargs=kwargs)}'
        push = SchemeWxPush.objects.create(time=now + timedelta(minutes=1), title=now.strftime('%Y年%m月%d日 汇总'),
                                           description=desc, url=path, app_name='payment')
        print(push)
