#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q

from .models import SalesOrder
from product.models import Quarry, Batch
from product.models import TYPE_CHOICES


class SalesOrderFilter(django_filters.FilterSet):
    # WH_CHOICES = [(w.id, w) for w in Warehouse.objects.all()]
    QUARRY = [(q.id, q) for q in Quarry.objects.all()]
    BATCH = [(b.id, b) for b in Batch.objects.all()]
    # partner = django_filters.ChoiceFilter(label='仓库',  method='filter_by_warehouse')
    partner = django_filters.CharFilter(label='客户资料', method='filter_by_partner',help_text='可输入姓名，电话，公司名称等信息来筛选')

    address = django_filters.CharFilter(label='发货地址', method='filter_by_address')
    #
    # quarry = django_filters.ChoiceFilter(label='矿口', choices=QUARRY, method='filter_by_quarry')
    # batch = django_filters.ChoiceFilter(label='批次', choices=BATCH, method='filter_by_batch')

    class Meta:
        model = SalesOrder
        fields = ('state', 'partner', 'address')

    # def filter_by_warehouse(self, queryset, name, value):
    #     loc_ids = Warehouse.objects.get(pk=value).get_main_location().get_child_list()
    #     return queryset.filter(**{'location_id__in': loc_ids})

    # def filter_by_block(self, queryset, name, value):
    #     expression = {'product__block__name__icontains': value}
    #     return queryset.filter(**expression)

    def filter_by_partner(self, queryset, name, value):
        lst = []
        if value:
            for key in ['partner__name__contains', 'partner__phone__contains', 'partner__company__name__contains', 'partner__company__phone__contains', ]:
                q_obj = Q(**{key: value})
                lst.append(q_obj)
        return queryset.filter(reduce(operator.or_, lst))

    def filter_by_address(self, queryset, name, value):
        lst = []
        if value:
            for key in ['province__name__contains',
                        'city__name__contains', ]:
                q_obj = Q(**{key: value})
                lst.append(q_obj)
        return queryset.filter(reduce(operator.or_, lst))

    def filter_by_batch(self, queryset, name, value):
        expression = {'product__block__batch_id': value}
        return queryset.filter(**expression)
