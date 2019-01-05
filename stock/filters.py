#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29

import django_filters
from .models import Stock, Warehouse


class StockFilter(django_filters.FilterSet):
    from product.models import Quarry, Batch
    from product.models import TYPE_CHOICES
    WH_CHOICES = [(w.id, w) for w in Warehouse.objects.all()]
    QUARRY = [(q.id, q) for q in Quarry.objects.all()]
    BATCH = [(b.id, b) for b in Batch.objects.all()]
    warehouse = django_filters.ChoiceFilter(label='仓库', choices=WH_CHOICES, method='filter_by_warehouse')
    block = django_filters.CharFilter(label='编号', method='filter_by_block')
    type = django_filters.ChoiceFilter(label='类型', method='filter_by_type', choices=TYPE_CHOICES)

    quarry = django_filters.ChoiceFilter(label='矿口', choices=QUARRY, method='filter_by_quarry')
    batch = django_filters.ChoiceFilter(label='批次', choices=BATCH, method='filter_by_batch')

    class Meta:
        model = Stock
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

    def filter_by_quanrry(self, queryset, name, value):
        expression = {'product__block__quarry_id': value}
        return queryset.filter(**expression)

    def filter_by_batch(self, queryset, name, value):
        expression = {'product__block__batch_id': value}
        return queryset.filter(**expression)
