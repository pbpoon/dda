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


