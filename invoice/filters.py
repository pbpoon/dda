#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q
from django_filters.widgets import LinkWidget

from public.filters import StateOrderFilter
from .models import Invoice, Payment

TYPE_CHOICES = (
    ('-1', '付款'),
    ('1', '收款')
)


class InvoiceFilter(StateOrderFilter):
    # state = django_filters.ChoiceFilter(label='订单状态', method='filter_by_partner', help_text='可输入姓名，电话，公司名称等信息来筛选')

    # type = django_filters.CharFilter(label='订单类型', method='filter_by_address')

    class Meta:
        model = Invoice
        fields = ('state', 'type', 'usage', 'date', 'due_date')


class PaymentFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(label='状态', field_name='type',
                                        choices=TYPE_CHOICES,
                                        widget=LinkWidget(attrs={'class': 'inline-ul'}))
    confirm = django_filters.BooleanFilter(label='确认收款')

    class Meta:
        model = Payment
        fields = ('state', 'confirm')

    def __init__(self, data=None, *args, **kwargs):
        if not data:
            data = {'state': '1', 'confirm': False}
        super().__init__(data=data, *args, **kwargs)
