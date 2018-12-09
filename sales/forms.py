#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/3
from django import forms
from django.urls import reverse, reverse_lazy

from product.models import Product, PackageList
from sales.models import SalesOrder, SalesOrderItem
from stock.models import Warehouse
from dal import autocomplete
from django_select2.forms import Select2Widget


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        exclude = ('state', 'order')
        widgets = {
            'entry': forms.HiddenInput,
        }


class SalesOrderItemForm(forms.ModelForm):
    product_autocomplete = forms.CharField(label='产品编号')
    warehouse = forms.ModelChoiceField(label='出货仓库', queryset=Warehouse.objects.filter(is_activate=True, ),
                                       required=True)

    class Meta:
        model = SalesOrderItem
        # exclude = ('line',)
        fields = (
            'order', 'warehouse', 'product_autocomplete', 'product', 'piece', 'quantity', 'uom', 'price',
            'package_list',
            'location')

        widgets = {
            'order': forms.HiddenInput,
            'piece': forms.HiddenInput,
            'quantity': forms.HiddenInput,
            'uom': forms.HiddenInput,
            'package_list': forms.HiddenInput,
            'location': forms.HiddenInput,
            'product': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        get_product_list = reverse('get_product_list')
        self.fields['product_autocomplete'].widget.attrs = {'class': 'autocomplete',
                                                            'onkeyup': 'get_autocomplete("{}")'.format(
                                                                get_product_list)}
        self.fields['warehouse'].widget.attrs = {'onchange': 'get_autocomplete("{}")'.format(
            get_product_list)}

        qs = Product.objects.filter(stock__isnull=False).exclude(type='semi_slab')
        self.fields['product'].queryset = qs
        instance = kwargs.get('instance')
        if instance:
            self.fields['product'].widget = forms.HiddenInput,
            if instance.product.type == 'slab':
                self.fields['piece'].widget.attrs = {'disabled': True}
                self.fields['quantity'].widget.attrs = {'disabled': True}
                self.fields['uom'].widget.attrs = {'disabled': True}
            else:
                self.fields['piece'].required = True
                self.fields['quantity'].required = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        warehouse = self.cleaned_data.get('warehouse')
        if warehouse:
            instance.location = warehouse.get_main_location()
        if instance.product.type == 'slab':
            if not instance.package_list:
                instance.piece = 0
                instance.quantity = 0
        elif instance.product.type == 'block':
            instance.piece = 1
            instance.quantity = self.quantity
        if commit:
            instance.save()
        return instance


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
