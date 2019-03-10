#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q, F, Count
from .models import Stock, Warehouse, Location


class StockFilter(django_filters.FilterSet):
    from product.models import Quarry, Batch
    from product.models import TYPE_CHOICES

    def to_set(objs):
        lst = set()
        for obj in objs:
            if obj.product.thickness is None:
                continue
            lst.add(obj.product.thickness)
        return lst

    THICKNESS_CHOICES = sorted(
        [(t, t) for t in to_set(Stock.objects.select_related('product').all())],
        key=lambda tup: tup[0])
    warehouse = django_filters.ModelMultipleChoiceFilter(label='仓库', queryset=Warehouse.objects.all(),
                                                         method='filter_by_warehouse')
    block = django_filters.CharFilter(label='编号', method='filter_by_block')
    type = django_filters.MultipleChoiceFilter(label='类型', method='filter_by_type', choices=TYPE_CHOICES)
    thickness = django_filters.MultipleChoiceFilter(label='厚度', method='filter_by_thickness', choices=THICKNESS_CHOICES)
    quarry = django_filters.ModelMultipleChoiceFilter(label='矿口', queryset=Quarry.objects.all(),
                                                      method='filter_by_quarry')
    batch = django_filters.ModelMultipleChoiceFilter(label='批次', queryset=Batch.objects.all().order_by('name'),
                                                     method='filter_by_batch')
    main_long = django_filters.RangeFilter(label='长')
    main_height = django_filters.RangeFilter(label='高')
    main_width = django_filters.RangeFilter(label='宽(荒料)')

    class Meta:
        model = Stock
        fields = (
        'block', 'warehouse', 'quarry', 'batch', 'type', 'thickness', 'main_long', 'main_height', 'main_width')

    def filter_by_warehouse(self, queryset, name, value):
        lst = []
        for val in value:
            lst.extend(val.get_main_location().get_child_list())
        if lst:
            return queryset.filter(**{'location_id__in': lst})
        else:
            return queryset

    def filter_by_block(self, queryset, name, value):
        expression = {'product__block__name__icontains': value}
        return queryset.filter(**expression)

    def filter_by_type(self, queryset, name, value):
        if value:
            expression = {'product__type__in': value}
            return queryset.filter(**expression)
        return queryset

    def filter_by_thickness(self, queryset, name, value):
        if value:
            expression = {'product__thickness__in': value}
            return queryset.filter(**expression)
        return queryset

    def filter_by_quarry(self, queryset, name, value):
        if value:
            expression = {'product__block__quarry__in': value}
            return queryset.filter(**expression)
        return queryset

    def filter_by_batch(self, queryset, name, value):
        if value:
            expression = {'product__block__batch__in': value}
            return queryset.filter(**expression)
        return queryset


class WarehouseLocationFilter(django_filters.FilterSet):
    class Meta:
        model = Location
        # fields = ['name']
        fields = {
            'name': ['icontains'],
        }
