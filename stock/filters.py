#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q
from .models import Stock, Warehouse


def to_set(objs):
    lst = set()
    for obj in objs:
        if obj.product.thickness is None:
            continue
        lst.add(obj.product.thickness)
    return sorted(lst)


class StockFilter(django_filters.FilterSet):
    from product.models import Quarry, Batch
    from product.models import TYPE_CHOICES
    WH_CHOICES = [(w.id, w) for w in Warehouse.objects.all()]
    QUARRY = [(q.id, q) for q in Quarry.objects.all()]
    BATCH = [(b.id, b) for b in Batch.objects.all()]
    THICKNESS_CHOICES = [(t, t) for t in to_set(Stock.objects.select_related('product'))]
    warehouse = django_filters.ChoiceFilter(label='仓库', choices=WH_CHOICES, method='filter_by_warehouse')
    block = django_filters.CharFilter(label='编号', method='filter_by_block')
    type = django_filters.ChoiceFilter(label='类型', method='filter_by_type', choices=TYPE_CHOICES)
    thickness = django_filters.ChoiceFilter(label='厚度', method='filter_by_thickness', choices=THICKNESS_CHOICES)
    quarry = django_filters.ChoiceFilter(label='矿口', choices=QUARRY, method='filter_by_quarry')
    batch = django_filters.ChoiceFilter(label='批次', choices=BATCH, method='filter_by_batch')
    long_gt = django_filters.CharFilter(label='长度大于', method='filter_by_long_gt')
    long_lt = django_filters.CharFilter(label='长度小于', method='filter_by_long_lt')
    height_gt = django_filters.CharFilter(label='高度大于', method='filter_by_height_gt')
    height_lt = django_filters.CharFilter(label='高度小于', method='filter_by_height_lt')

    class Meta:
        model = Stock
        # fields = ('block', 'type',)
        fields = ('block', 'warehouse', 'type', 'quarry', 'batch')

    def filter_by_warehouse(self, queryset, name, value):
        loc_ids = Warehouse.objects.get(pk=value).get_main_location().get_child_list()
        return queryset.filter(**{'location_id__in': loc_ids})

    def filter_by_block(self, queryset, name, value):
        expression = {'product__block__name__icontains': value}
        return queryset.filter(**expression)

    def filter_by_type(self, queryset, name, value):
        expression = {'product__type': value}
        return queryset.filter(**expression)

    def filter_by_thickness(self, queryset, name, value):
        expression = {'product__thickness': value}
        return queryset.filter(**expression)

    def filter_by_quanrry(self, queryset, name, value):
        expression = {'product__block__quarry_id': value}
        return queryset.filter(**expression)

    def filter_by_batch(self, queryset, name, value):
        expression = {'product__block__batch_id': value}
        return queryset.filter(**expression)

    def filter_by_long_gt(self, queryset, name, value):
        lst = []
        for key in ['items__long__gt']:
            q_obj = Q(**{key: value})
            lst.append(q_obj)
        return queryset.filter(reduce(operator.or_, lst)).distinct()

    def filter_by_long_lt(self, queryset, name, value):
        lst = []
        for key in ['items__long__lt']:
            q_obj = Q(**{key: value})
            lst.append(q_obj)
        return queryset.filter(reduce(operator.or_, lst)).distinct()

    def filter_by_height_gt(self, queryset, name, value):
        lst = []
        for key in ['items__height__gt']:
            q_obj = Q(**{key: value})
            lst.append(q_obj)
        return queryset.filter(reduce(operator.or_, lst)).distinct()

    def filter_by_height_lt(self, queryset, name, value):
        lst = []
        for key in ['items__height__lt']:
            q_obj = Q(**{key: value})
            lst.append(q_obj)
        return queryset.filter(reduce(operator.or_, lst)).distinct()
