#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django import forms

from stock.models import Location


class StateForm(forms.Form):
    state = forms.HiddenInput


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'
        widgets = {
            'warehouse': forms.HiddenInput,
        }


class AddExcelForm(forms.Form):
    file = forms.FileField(label='上传文件')


class FormUniqueTogetherMixin:

    def clean(self):
        data = self.cleaned_data
        product = data.get('product')
        order = data.get('order')
        if order and product:
            same_product_count = order.items.filter(product_id=product.id).count()
            if same_product_count > 1:
                raise forms.ValidationError('订单明细行，已有 {} 产品.不允许有相同的产品规格!'.format(str(product)))
        return data
