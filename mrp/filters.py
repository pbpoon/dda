#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q

from mrp.models import InOutOrder, MoveLocationOrder, ProductionOrder, InventoryOrder
from product.models import Quarry, Batch, Product
from product.models import TYPE_CHOICES
from public.filters import StateOrderFilter


class InOutOrderFilter(StateOrderFilter):
    # state = django_filters.ChoiceFilter(label='订单状态', method='filter_by_partner', help_text='可输入姓名，电话，公司名称等信息来筛选')

    # type = django_filters.CharFilter(label='订单类型', method='filter_by_address')

    class Meta:
        model = InOutOrder
        fields = ('state', 'type')


class MoveLocationOrderFilter(StateOrderFilter):
    class Meta:
        model = MoveLocationOrder
        fields = ('state', 'warehouse', 'warehouse_dest')


class ProductionOrderFilter(StateOrderFilter):
    class Meta:
        model = ProductionOrder
        fields = ('state', 'production_type', 'partner')


class InventoryOrderFilter(StateOrderFilter):
    class Meta:
        model = InventoryOrder
        fields = ('state', 'warehouse', 'product_type')


class ProductFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(label='编号', method='filter_by_block')


    class Meta:
        model = Product
        # fields = ('name',)
        fields = ('name',)

    def filter_by_block(self, queryset, name, value):
        expression = {'product__block__name__icontains': value}
        return queryset.filter(**expression)
