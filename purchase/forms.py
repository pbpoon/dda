#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django import forms

from product.models import Block
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
        return cd
