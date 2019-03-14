#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q
from django_filters.widgets import LinkWidget

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
    from mrp.models import ProductionType
    production_type = django_filters.ModelChoiceFilter(label='状态',queryset=ProductionType.objects.all(),
                                        widget=LinkWidget(attrs={'class': 'inline-ul'}))
    class Meta:
        model = ProductionOrder
        fields = ('state', 'production_type', 'partner')
        # widgets = {
        #     'production_type': LinkWidget(attrs={'class': 'inline-ul'})
        # }


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
