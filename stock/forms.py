#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/20

from product.models import Slab
from django import forms


class SlabEditForm(forms.ModelForm):
    part_number = forms.ChoiceField(label='夹号', choices=[(i, "第 {} 夹".format(i)) for i in range(1, 11)])

    class Meta:
        model = Slab
        fields = ['part_number', 'line', 'long', 'height', 'kl1', 'kh1', 'kl2', 'kh2']