#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/3
from django import forms
from django.urls import reverse, reverse_lazy

from partner.models import City
from product.models import Product, PackageList
from public.forms import FormUniqueTogetherMixin
from public.widgets import SwitchesWidget, AutocompleteWidget, RadioWidget
from sales.models import SalesOrder, SalesOrderItem, Customer
from stock.models import Warehouse
from dal import autocomplete


class SalesOrderForm(forms.ModelForm):
    is_default_address = forms.BooleanField(label='默认地址', required=False, widget=SwitchesWidget,
                                            help_text='此项开启后，下面地址所选无效。发货地址将会用客户默认地址')

    class Meta:
        model = SalesOrder
        fields = (
            'date', 'partner', 'is_default_address', 'province', 'city', 'handler', 'entry')
        widgets = {
            'date': forms.DateInput(attrs={'class': 'datepicker'}),
            'entry': forms.HiddenInput,
            'partner': autocomplete.ModelSelect2(url='customer_autocomplete',
                                                 attrs={'class': ' browser-default', 'data-minimum-input-length': 1,
                                                        'data-html': True, 'data-create-url':''}),
            'province': autocomplete.ModelSelect2(url='get_province',
                                                  attrs={'class': 'browser-default'}),
            'city': autocomplete.ModelSelect2(url='get_city',
                                              forward=['province'],
                                              attrs={'class': ' browser-default'})

            # 非常重要'class': 'browser-default'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not kwargs.get('instance'):
            # self.fields['city'].queryset = City.objects.none()
            self.fields['handler'].initial = kwargs['initial'].get('entry')
            self.fields['is_default_address'].initial = True

    def clean(self):
        cd = self.cleaned_data
        return cd

    def save(self, commit=True):
        is_default_address = self.cleaned_data.get('is_default_address')
        instance = super().save(commit=False)
        if is_default_address:
            instance.province = instance.partner.province
            instance.city = instance.partner.city
        if commit:
            instance.save()
        return instance


class SalesOrderItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    warehouse = forms.ModelChoiceField(label='出货仓库', queryset=Warehouse.objects.filter(is_activate=True, ),
                                       required=True)

    class Meta:
        model = SalesOrderItem
        # exclude = ('line',)
        fields = (
            'order', 'warehouse', 'product', 'piece', 'quantity', 'uom', 'price',
            'package_list',
            'location')

        widgets = {
            'order': forms.HiddenInput,
            'package_list': forms.HiddenInput,
            'location': forms.HiddenInput,
            'product': autocomplete.ModelSelect2(url='get_product_list',
                                                 attrs={'class': 'browser-default'},
                                                 forward=['warehouse']),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].widget.attrs = {'min': 0.0}
        instance = kwargs.get('instance')
        if instance:
            # self.fields['product'].widget.attrs = {'disabled': True}
            self.fields['uom'].required = False
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


class SalesOrderItemQuickForm(FormUniqueTogetherMixin, forms.ModelForm):
    slab_id_list = forms.CharField(widget=forms.HiddenInput(), required=False)

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
        product = cd.get('product')
        if product.type == 'slab':
            slab_id_list = cd.get('slab_id_list')
            slab_id_list = slab_id_list.split(',')
            instance.package_list = PackageList.make_package_from_list(product_id=product.id, lst=slab_id_list)
        if commit:
            instance.save()
        return instance


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('is_company', 'sex', 'name', 'phone', 'province', 'city', 'entry', 'is_activate', 'company')
        widgets = {
            'sex': RadioWidget(),
            'is_company': SwitchesWidget,
            'is_activate': SwitchesWidget,
            'entry': forms.HiddenInput(),
            'province': autocomplete.ModelSelect2(url='get_province',
                                                  attrs={'class': 'browser-default'}),
            'city': autocomplete.ModelSelect2(url='get_city',
                                              forward=['province'],
                                              attrs={'class': ' browser-default'}),
            'company': autocomplete.ModelSelect2(url='customer_company_autocomplete',
                                                 attrs={'class': 'browser-default'})
        }


class SalesOrderCreateByCustomerForm(SalesOrderForm):
    class Meta:
        model = SalesOrder
        fields = (
            'date', 'partner', 'is_default_address', 'province', 'city', 'handler', 'entry')
        widgets = {
            'date': forms.DateInput(attrs={'class': 'datepicker'}),
            'entry': forms.HiddenInput,
            # 'partner': autocomplete.ModelSelect2(url='customer_autocomplete',
            #                                      attrs={'class': ' browser-default', 'data-minimum-input-length': 1,
            #                                             'data-html': True, }),
            'province': autocomplete.ModelSelect2(url='get_province',
                                                  attrs={'class': 'browser-default'}),
            'city': autocomplete.ModelSelect2(url='get_city',
                                              forward=['province'],
                                              attrs={'class': ' browser-default'})

            # 非常重要'class': 'browser-default'
        }
