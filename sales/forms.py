#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/3
from django import forms
from django.urls import reverse, reverse_lazy

from partner.models import City, Area
from product.models import Product, PackageList
from sales.models import SalesOrder, SalesOrderItem
from stock.models import Warehouse
from dal import autocomplete as dal_autocomplete


class AutocompleteWidget(forms.TextInput):
    url = None

    class Media:
        js = ('js/autocomplete.js',)

    def __init__(self, url=None, *args, **kwargs):
        self.url = url
        super().__init__(*args, **kwargs)

    def build_attrs(self, *args, **kwargs):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(*args, **kwargs)

        if self.url is not None:
            attrs['class'] = 'autocomplete'
            attrs['onkeyup'] = 'get_autocomplete("{}")'.format(self.url)

        return attrs

    def _get_url(self):
        if self._url is None:
            return None

        if '/' in self._url:
            return self._url

        return reverse(self._url)

    def _set_url(self, url):
        self._url = url

    url = property(_get_url, _set_url)


class SalesOrderForm(forms.ModelForm):
    is_default_address = forms.BooleanField(label='默认地址', widget=forms.CheckboxInput)
    partner_autocomplete = forms.CharField(widget=AutocompleteWidget(url='get_product_list'), label='客户')

    class Meta:
        model = SalesOrder
        fields = ('date', 'handler', 'partner', 'partner_autocomplete', 'province', 'city', 'area')
        # exclude = ('state', 'order')
        widgets = {
            'entry': forms.HiddenInput,
            'partner': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_default_address'].initial = True
        self.fields['city'].queryset = City.objects.none()
        self.fields['area'].queryset = Area.objects.none()
        self.fields['city'].widget.att = {'class': 'city'}
        self.fields['area'].widget.att = {'class': 'dist'}
        self.fields['province'].widget.att = {'class': 'prov'}


class SalesOrderItemForm(forms.ModelForm):
    product_autocomplete = forms.CharField(label='产品编号', widget=AutocompleteWidget(url='get_product_list'))
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
            'package_list': forms.HiddenInput,
            'location': forms.HiddenInput,
            'product': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        get_product_list = reverse_lazy('get_product_list')
        # self.fields['product_autocomplete'].widget.attrs = {'class': 'autocomplete',
        #                                                     'onkeyup': 'get_autocomplete("{}")'.format(
        #                                                         get_product_list)}
        self.fields['warehouse'].widget.attrs = {'onchange': 'get_autocomplete("{}")'.format(get_product_list)}
        qs = Product.objects.filter(stock__isnull=False).exclude(type='semi_slab')
        self.fields['product'].queryset = qs
        instance = kwargs.get('instance')
        if instance:
            self.fields['uom'].required = False
            self.fields[
                'product_autocomplete'].initial = instance.product.name + instance.product.get_type_display()
            # self.fields['product_autocomplete'].widget = forms.TextInput(attrs={'disable': True})
            self.fields['warehouse'].required = False
            self.fields['warehouse'].widget = forms.HiddenInput()
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
            instance.quantity = instance.quantity
        if commit:
            instance.save()
        return instance


class SalesOrderItemQuickForm(forms.ModelForm):
    slab_id_list = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = SalesOrderItem
        fields = (
            'order', 'product', 'piece', 'quantity', 'uom', 'price', 'package_list', 'slab_id_list', 'location')

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
