#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django import forms

from .models import PurchaseOrderItem, PurchaseOrder
from material_widgets import forms as md_forms

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
        exclude = ('order', 'entry', 'state')


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        # fields = '__all__'
        exclude = ( 'product', 'entry')
        widgets = {
            'type': forms.HiddenInput(),
            'id': forms.HiddenInput(),
            'order':forms.HiddenInput()
        }


class StateForm(forms.Form):
    state = forms.BooleanField(widget=forms.HiddenInput)
