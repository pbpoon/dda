#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/29

from django import forms

from product.models import DraftPackageListItem


class DraftPackageListItemForm(forms.ModelForm):
    # line_form = forms.IntegerField(required=False)
    # line_to = forms.IntegerField(required=False)
    piece = forms.IntegerField(max_value=30, label='件数', widget=forms.NumberInput(), initial=1)
    part_number = forms.ChoiceField(label='夹号', choices=[(i, "第 {} 夹".format(i)) for i in range(1, 11)])

    class Meta:
        model = DraftPackageListItem
        fields = ('order', 'part_number', 'long', 'height', 'piece',
                  'kl1', 'kh1', 'kl2', 'kh2', 'line',)
        widgets = {
            'order': forms.HiddenInput(),
            # 'part_number': forms.ChoiceField(choices=[(i, i) for i in range(1, 10)]),
            # 'line_form': forms.NumberInput(attrs={'class': 'col s6'}),
            # 'line_to': forms.NumberInput(attrs={'class': 'col s6'})
        }

    def save(self, commit=True):

        instance = super().save(commit=False)
        piece = self.cleaned_data.pop('piece')
        if commit:
            instance.save()
            if piece and piece > 1:
                for i in range(1, piece):
                    instance.pk = None
                    instance.line = None
                    instance.save()
        return instance

