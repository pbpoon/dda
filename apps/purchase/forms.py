#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from dal import autocomplete
from django import forms

from product.models import Block
from public.widgets import SwitchesWidget, RadioWidget
from purchase.models import Supplier
from sales.models import Customer
from .models import PurchaseOrderItem, PurchaseOrder

STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('cancel', '取消'),
)


class ImportFileForm(forms.Form):
    file = forms.FileField(label='选择文件')


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        exclude = ('order', 'state')
        widgets = {
            'entry': forms.HiddenInput,
            'province': autocomplete.ModelSelect2(url='get_province',
                                                  attrs={'class': 'browser-default'}),
            'city': autocomplete.ModelSelect2(url='get_city',
                                              forward=['province'],
                                              attrs={'class': ' browser-default'})
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        # fields = '__all__'
        exclude = ('uom', 'quantity', 'product')
        widgets = {
            'type': forms.HiddenInput,
            'order': forms.HiddenInput,
            'line': forms.HiddenInput,
            'piece': forms.HiddenInput,
            'quantity': forms.HiddenInput,
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if Block.objects.filter(name=name).exists():
            raise forms.ValidationError('已有编号为：{}#的荒料存在，请确保该编号为全新'.format(name))
        return name

    def clean(self):
        cd = self.cleaned_data
        name = cd.get('name')
        order = cd.get('order')
        if order.items.filter(name=name).exists():
            raise forms.ValidationError('本单已有编号为：{}#的荒料存在，请确保该编号不重复'.format(name))
        if not cd.get('batch'):
            if '-' in name:
                n = name.split('-')[0]
            else:
                n = name[:2]
            cd['batch'] = n
        return cd


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ('is_company', 'sex', 'name', 'phone', 'province', 'city', 'entry', 'is_activate')
        widgets = {
            'sex': RadioWidget(),
            'is_company': SwitchesWidget,
            'is_activate': SwitchesWidget,
            'entry': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['province'].widget.attrs = {'class': 'prov'}
        self.fields['city'].widget.attrs = {'class': 'city'}
