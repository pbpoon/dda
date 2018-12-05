#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/3
from django import forms

from product.models import Product
from sales.models import SalesOrder, SalesOrderItem


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        exclude = ('state', 'order')
        widgets = {
            'entry': forms.HiddenInput,
        }


class SalesOrderItemForm(forms.ModelForm):
    class Meta:
        model = SalesOrderItem
        exclude = ('line',)
        widgets = {
            'order': forms.HiddenInput,
            'package_list': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Product.objects.filter(stock__isnull=False).exclude(type='semi_slab')
        self.fields['product'].queryset = qs
