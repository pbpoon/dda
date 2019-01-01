#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q
from .models import PurchaseOrder


class PurchaseOrderFilter(django_filters.FilterSet):
    # state = django_filters.ChoiceFilter(label='订单状态', method='filter_by_partner', help_text='可输入姓名，电话，公司名称等信息来筛选')

    # type = django_filters.CharFilter(label='订单类型', method='filter_by_address')
    partner = django_filters.CharFilter(label='客户资料', method='filter_by_partner',help_text='可输入姓名，电话，公司名称等信息来筛选')


    class Meta:
        model = PurchaseOrder
        fields = ('state', 'partner')


    def filter_by_partner(self, queryset, name, value):
        lst = []
        if value:
            for key in ['partner__name__contains', 'partner__phone__contains', 'partner__company__name__contains', 'partner__company__phone__contains', ]:
                q_obj = Q(**{key: value})
                lst.append(q_obj)
        return queryset.filter(reduce(operator.or_, lst))