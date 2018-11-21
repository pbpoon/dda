#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import forms

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


class KesOrderProduceItemForm(forms.ModelForm):
    class Meta:
        model = KesOrderProduceItem
        fields = ('order', 'raw_item', 'thickness', 'piece')
        widgets = {
            'order': forms.HiddenInput,
        }
