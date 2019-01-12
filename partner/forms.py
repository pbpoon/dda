#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/6
from django import forms
from partner.models import Partner, MainInfo
from public.widgets import SwitchesWidget, RadioWidget


class MainInfoForm(forms.ModelForm):
    name = forms.CharField(label='公司名称')

    class Meta:
        model = MainInfo
        fields = ('company', 'name', 'logo', 'address_detail')
        widgets = {
            'company': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('instance'):
            self.fields['name'].initial = kwargs.get('instance').company.name

    def save(self, commit=True):
        name = self.cleaned_data.get('name')
        instance = super().save(commit=False)
        if not instance.company:
            instance.company, _ = Partner.objects.get_or_create(name=name, is_company=True, type='supplier')
        else:
            instance.company.name = name
            instance.company.save()
        if commit:
            instance.save()
        return instance
