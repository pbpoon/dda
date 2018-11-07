#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import forms
from .models import BlockCheckInOrder


class BlockCheckOrderForm(forms.ModelForm):
    class Meta:
        model = BlockCheckInOrder
        fields = '__all__'
        widgets = {
            'entry': forms.HiddenInput,
            'purchase_order': forms.HiddenInput,
            'order': forms.HiddenInput,
        }
