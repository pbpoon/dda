#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django import forms
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
        exclude = ('order', 'state', 'entry')


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        exclude = ('order', 'product', 'entry')
        widgets = {
            'type': forms.HiddenInput(),
        }


class StateForm(forms.Form):
    state = forms.BooleanField(widget=forms.HiddenInput)
