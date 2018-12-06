#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/3
from django import forms

from product.models import Product, PackageList
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
        instance = kwargs.get('instance')
        if instance:
            self.fields['product'].queryset = qs.filter(pk=instance.product_id)
            if instance.product.type == 'slab':
                self.fields['piece'].widget.attrs = {'disabled': True}
                self.fields['quantity'].widget.attrs = {'disabled': True}
                self.fields['uom'].widget.attrs = {'disabled': True}
            else:
                self.fields['piece'].required = True
                self.fields['quantity'].required = True


class SalesOrderItemQuickForm(forms.ModelForm):
    slab_id_list = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = SalesOrderItem
        fields = ('order', 'product', 'piece', 'quantity', 'uom', 'price', 'package_list', 'slab_id_list', 'location')

        # exclude = ('line',)
        widgets = {
            'order': forms.HiddenInput,
            'package_list': forms.HiddenInput,
            'location': forms.HiddenInput,
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        cd = self.cleaned_data
        slab_id_list = cd.get('slab_id_list')
        product_id = cd.get('product').id
        slab_id_list = slab_id_list.split(',')
        instance.package_list = PackageList.make_package_from_list(product_id=product_id, lst=slab_id_list)
        if commit:
            instance.save()
        return instance
