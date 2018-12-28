#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/3
from django.db.models import Q

from partner.models import Partner
from public.widgets import DatePickerWidget, CheckBoxWidget
from .models import Assign, Invoice, InvoiceItem
from django import forms


class AssignInvoiceForm(forms.ModelForm):
    class Meta:
        model = Assign
        exclude = ('created',)
        widgets = {
            'payment': forms.HiddenInput,
            'entry': forms.HiddenInput,
            'invoice': forms.HiddenInput,
        }


class InvoiceForm(forms.ModelForm):
    has_items = forms.BooleanField(label='添加订单明细行', initial=True, widget=CheckBoxWidget)
    item_text = forms.CharField(label='明细行额外内容', required=False)

    class Meta:
        model = Invoice
        fields = (
            'type', 'usage', 'partner', 'date', 'due_date', 'entry', 'content_type', 'object_id', 'has_items',
            'item_text')

        widgets = {
            'date': DatePickerWidget(),
            'due_date': DatePickerWidget(),
            'entry': forms.HiddenInput(),
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        partner = kwargs.pop('partner')
        super().__init__(*args, **kwargs)
        # p = Partner.objects.filter(pk=partner.id)
        lst = [i for i in Partner.invoices.all().values_list('id', flat=True)]
        lst.append(partner.id)
        qs = Partner.objects.filter(id__in=lst)
        # qs = Partner.invoices.all()
        self.fields['partner'].queryset = qs

    def save(self, commit=True):
        has_items = self.cleaned_data.get('has_items')
        item_text = self.cleaned_data.get('item_text')
        inv = super().save(commit=False)
        comment = '从 %s <a href="%s">%s</a> 手动创建本账单。' % (
            inv.from_order._meta.verbose_name, inv.from_order.get_absolute_url(), inv.from_order)
        if commit:
            inv.save()
            if has_items:
                comment += '<br>并添加原有订单的明细行。'
                if item_text:
                    comment += '<br>明细行额外内容为：%s' % (item_text)
                for item in inv.from_order.items.all():
                    InvoiceItem.objects.create(item='%s:%s' % (item_text, str(item.product)), quantity=item.quantity,
                                               uom=item.uom, price=0, order=inv)
            inv.create_comment(**{'comment': comment})
        return inv
