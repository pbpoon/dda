#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/3
from .models import Assign
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
