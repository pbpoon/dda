#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29

import django_filters
from .models import Category, Block, Product



class BlockFilter(django_filters.FilterSet):
    from product.models import Quarry, Batch
    QUARRY = [(q.id, q) for q in Quarry.objects.all()]
    BATCH = [(b.id, b) for b in Batch.objects.all()]
    CATEGORY = [(b.id, b) for b in Category.objects.all()]
    name = django_filters.CharFilter(label='编号', method='filter_by_block')

    category = django_filters.ChoiceFilter(label='品种分类', choices=CATEGORY, method='filter_by_category')
    quarry = django_filters.ChoiceFilter(label='矿口', choices=QUARRY, method='filter_by_quarry')
    batch = django_filters.ChoiceFilter(label='批次', choices=BATCH, method='filter_by_batch')

    class Meta:
        model = Block
        # fields = ('name',)
        fields = ('name', 'quarry', 'batch')

    def filter_by_block(self, queryset, name, value):
        expression = {'name__icontains': value}
        return queryset.filter(**expression)

    def filter_by_quarry(self, queryset, name, value):
        expression = {'quarry_id': value}
        return queryset.filter(**expression)

    def filter_by_batch(self, queryset, name, value):
        expression = {'batch_id': value}
        return queryset.filter(**expression)

    def filter_by_category(self, queryset, name, value):
        catgory_ids = Category.objects.get(pk=value).get_child_list()
        return queryset.filter(**{'category_id__in': catgory_ids})


class ProductFilter(BlockFilter):
    class Meta:
        model = Product
        fields = ('name', 'quarry', 'batch')

    def filter_by_block(self, queryset, name, value):
        expression = {'block__name__icontains': value}
        return queryset.filter(**expression)

    def filter_by_quarry(self, queryset, name, value):
        expression = {'block__quarry_id': value}
        return queryset.filter(**expression)

    def filter_by_batch(self, queryset, name, value):
        expression = {'block__batch_id': value}
        return queryset.filter(**expression)

    def filter_by_category(self, queryset, name, value):
        catgory_ids = Category.objects.get(pk=value).get_child_list()
        return queryset.filter(**{'block__category_id__in': catgory_ids})
