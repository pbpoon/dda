#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django import forms


class StateForm(forms.Form):
    state = forms.BooleanField(widget=forms.HiddenInput)
