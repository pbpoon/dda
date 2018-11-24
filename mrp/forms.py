#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import forms
from django.urls import reverse, reverse_lazy

from product.models import Product
from .models import BlockCheckInOrder, KesOrderRawItem, KesOrderProduceItem


class BlockCheckOrderForm(forms.ModelForm):
    class Meta:
        model = BlockCheckInOrder
        fields = '__all__'
        widgets = {
            'entry': forms.HiddenInput,
            'purchase_order': forms.HiddenInput,
            'order': forms.HiddenInput,
        }


class KesOrderRawItemForm(forms.ModelForm):
    class Meta:
        model = KesOrderRawItem
        fields = '__all__'
        widgets = {
            'piece': forms.HiddenInput,
            'order': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('order')
        super(KesOrderRawItemForm, self).__init__(*args, **kwargs)
        if order and order.items.all():
            qs = Product.objects.filter(type='block', stock__isnull=False).exclude(
                pk__in=[int(item.product.id) for item in order.items.all()])
        else:
            qs = Product.objects.filter(type='block', stock__isnull=False)
        url = reverse_lazy('get_product_info')
        self.fields['product'].queryset = qs
        self.fields['product'].widget.attrs = {'onchange': 'set_onchange({},"{}","quantity")'.format('this.value', url)}


class KesOrderProduceItemForm(forms.ModelForm):
    class Meta:
        model = KesOrderProduceItem
        fields = ('order', 'raw_item', 'thickness', 'piece')
        widgets = {
            'order': forms.HiddenInput,
            'raw_item': forms.HiddenInput,
        }

    def clean_thickness(self):
        thickness = self.cleaned_data['thickness']
        raw_item = KesOrderRawItem.objects.get(id=self.cleaned_data['raw_item'].id)
        if thickness in {item.thickness for item in raw_item.produces.all()} and self.cleaned_data['product']:
            raise forms.ValidationError('该编号{}#已有相同的的厚度毛板存在！同一编号不允许有重复厚度的毛板行！'.format(raw_item.product))
        return thickness
