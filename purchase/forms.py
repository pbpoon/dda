#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django import forms

from product.models import Product
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
        exclude = ('entry',)
        widgets = {
            'type': forms.HiddenInput(),
            'id': forms.HiddenInput(),
            'order': forms.HiddenInput()
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if Product.objects.filter(name=name).exists():
            raise forms.ValidationError('已有编号为：{}#的荒料存在，请确保该编号为全新'.format(name))
        return name


