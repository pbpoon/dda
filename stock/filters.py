#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q
from .models import Stock, Warehouse, Location


class StockFilter(django_filters.FilterSet):
    from product.models import Quarry, Batch
    from product.models import TYPE_CHOICES
    # THICKNESS_CHOICES = sorted([(t, t) for t in to_set(Stock.objects.select_related('product'))],
    #                            key=lambda tup: tup[0])

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
    batch = django_filters.ModelMultipleChoiceFilter(label='批次', queryset=Batch.objects.all().order_by('name'), method='filter_by_batch')
    long = django_filters.NumericRangeFilter(label='长', method='filter_by_long')
    height = django_filters.NumericRangeFilter(label='高/宽', method='filter_by_height')

    class Meta:
        model = Stock
        fields = ('block', 'warehouse', 'quarry', 'batch', 'type', 'thickness', 'long', 'height')

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

    def filter_by_long(self, queryset, name, value):
        cd = self.form.cleaned_data
        if cd.get('type') != 'slab':
            if value:
                if value.start is not None and value.stop is not None:
                    query = {'product__block__%s__range' % (name): [value.start, value.stop]}
                elif value.start is not None:
                    query = {'product__block__%s__gt' % (name): value.start}
                elif value.stop is not None:
                    query = {'product__block__%s__lt' % (name): value.stop}
                return queryset.filter(**query)
        else:
            if value.start is not None and value.stop is not None:
                query = {'items__%s__range' % (name): [value.start, value.stop]}
            elif value.start is not None:
                query = {'items__%s__gt' % (name): value.start}
            elif value.stop is not None:
                query = {'items__%s__lt' % (name): value.stop}
            return queryset.filter(**query)

    def filter_by_height(self, queryset, name, value):
        cd = self.form.cleaned_data
        if cd.get('type') != 'slab':
            lst = []
            if value:
                if value.start is not None and value.stop is not None:
                    lookup_lst = ['product__block__height__range',
                                  'product__block__width__range']
                    lookup_value = [value.start, value.stop]
                    # query = {'product__block__%s__range' % (name): [value.start, value.stop]}
                elif value.start is not None:
                    lookup_lst = ['product__block__height__gt',
                                  'product__block__width__gt']
                    lookup_value = value.start
                elif value.stop is not None:
                    lookup_lst = ['product__block__height__lt',
                                  'product__block__width__lt']
                    lookup_value = value.stop
                for key in lookup_lst:
                    q_obj = Q(**{key: lookup_value})
                    lst.append(q_obj)
                return queryset.filter(reduce(operator.or_, lst)).distinct()
            return queryset
        else:
            if value.start is not None and value.stop is not None:
                query = {'items__%s__range' % (name): [value.start, value.stop]}
            elif value.start is not None:
                query = {'items__%s__gt' % (name): value.start}
            elif value.stop is not None:
                query = {'items__%s__lt' % (name): value.stop}
            return queryset.filter(**query)


class WarehouseLocationFilter(django_filters.FilterSet):
    class Meta:
        model = Location
        # fields = ['name']
        fields = {
            'name': ['icontains'],
        }
