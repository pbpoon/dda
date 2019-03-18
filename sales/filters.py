#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/29
import operator
from functools import reduce

import django_filters
from django.db.models import Q

from dal import autocomplete
from django.utils.html import format_html

from public.filters import StateOrderFilter
from .models import Customer


class CustomerAutocomplete(autocomplete.Select2QuerySetView):
    create_field = 'name'

    def create_object(self, text):
        phone = ''
        try:
            text, phone = text.split('/')
            # phone = int(text)
        except Exception as e:
            pass
        data = {self.create_field: text}
        if phone:
            phone = ''.join(phone.split())
            data.update({'phone': phone})
        """Create an object given a text."""
        return self.get_queryset().get_or_create(**data)[0]

    def get_result_label(self, item):
        return format_html('%s:%s:%s' % (item, item.get_address(), item.phone))

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Customer.objects.none()

        qs = Customer.objects.all()
        if self.q:
            lst = []
            for key in ['name__contains', 'phone__contains', 'company__name__contains',
                        'company__phone__contains', ]:
                q_obj = Q(**{key: self.q})
                lst.append(q_obj)
            qs = qs.filter(reduce(operator.or_, lst))

        return qs


class SalesOrderFilter(StateOrderFilter):
    partner = django_filters.CharFilter(label='客户资料', method='filter_by_partner', help_text='可输入姓名，电话，公司名称等信息来筛选')

    address = django_filters.CharFilter(label='发货地址', method='filter_by_address')

    class Meta:
        from .models import SalesOrder
        model = SalesOrder
        fields = ('state', 'partner', 'address')

    def __init__(self, data=None, *args, **kwargs):
        if not data:
            data = {'state': 'confirm'}
        super().__init__(data=data, *args, **kwargs)

    def filter_by_partner(self, queryset, name, value):
        lst = []
        if value:
            for key in ['partner__name__contains', 'partner__phone__contains', 'partner__company__name__contains',
                        'partner__company__phone__contains', ]:
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


class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label='客户资料', method='filter_by_partner', help_text='可输入姓名，电话，公司名称等信息来筛选')
    address = django_filters.CharFilter(label='发货地址', method='filter_by_address')

    def filter_by_partner(self, queryset, name, value):
        lst = []
        if value:
            for key in ['name__contains', 'phone__contains', 'company__name__contains',
                        'company__phone__contains', ]:
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
