#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/29

from django import forms

from product.models import DraftPackageListItem, PackageListItem, Slab


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


class PackageListItemForm(forms.ModelForm):
    slab = forms.ModelChoiceField(queryset=Slab.objects.none(), required=False, widget=forms.HiddenInput)
    piece = forms.IntegerField(max_value=30, label='件数', widget=forms.NumberInput(), initial=1)
    long = forms.IntegerField(label='长', widget=forms.NumberInput(), min_value=0)
    height = forms.IntegerField(label='高', widget=forms.NumberInput(), min_value=0)
    kl1 = forms.IntegerField(label='长1', widget=forms.NumberInput(), min_value=0, required=False)
    kh1 = forms.IntegerField(label='高1', widget=forms.NumberInput(), min_value=0, required=False)
    kl2 = forms.IntegerField(label='长2', widget=forms.NumberInput(), min_value=0, required=False)
    kh2 = forms.IntegerField(label='高2', widget=forms.NumberInput(), min_value=0, required=False)
    part_number = forms.ChoiceField(label='夹号', choices=[(i, "第 {} 夹".format(i)) for i in range(1, 11)])

    class Meta:
        model = PackageListItem
        fields = ('order', 'slab', 'part_number', 'long', 'height', 'piece',
                  'kl1', 'kh1', 'kl2', 'kh2', 'line',)
        widgets = {
            'order': forms.HiddenInput(),
        }

    def save(self, commit=True):
        cd = self.cleaned_data
        instance = super().save(commit=False)
        piece = self.cleaned_data.pop('piece') + 1
        try:
            max_line = max(i.line for i in instance.order.items.filter(part_number=instance.part_number))
        except Exception as e:
            max_line = 0
        data = {
            'part_number': cd.get('part_number'),
            'long': cd.get('long'),
            'height': cd.get('height'),
            'kl1': cd.get('kl1'),
            'kh1': cd.get('kh1'),
            'kl2': cd.get('kl2'),
            'kh2': cd.get('kh2'),
        }
        if commit:
            if piece and piece > 1:
                for i in range(max_line + 1, max_line + piece):
                    instance.pk = None
                    instance.line = i
                    data.update({'line': i})
                    slab = Slab.objects.create(**data)
                    instance.slab = slab
                    instance.save()
            else:
                data.update({'line': max_line + 1})
                slab = Slab.objects.create(**data)
                instance.slab = slab
                instance.line = data['line']
                instance.save()
            instance.order.save()
        return instance


class PackageListItemEditForm(forms.ModelForm):
    # slab = forms.ModelChoiceField(queryset=Slab.objects.none(), required=False, widget=forms.HiddenInput)
    # piece = forms.IntegerField(max_value=30, label='件数', widget=forms.NumberInput(), initial=1)
    long = forms.IntegerField(label='长', widget=forms.NumberInput(), min_value=0)
    height = forms.IntegerField(label='高', widget=forms.NumberInput(), min_value=0)
    kl1 = forms.IntegerField(label='长1', widget=forms.NumberInput(), min_value=0, required=False)
    kh1 = forms.IntegerField(label='高1', widget=forms.NumberInput(), min_value=0, required=False)
    kl2 = forms.IntegerField(label='长2', widget=forms.NumberInput(), min_value=0, required=False)
    kh2 = forms.IntegerField(label='高2', widget=forms.NumberInput(), min_value=0, required=False)
    part_number = forms.ChoiceField(label='夹号', choices=[(i, "第 {} 夹".format(i)) for i in range(1, 11)])

    class Meta:
        model = PackageListItem
        fields = ('order', 'slab', 'part_number', 'line', 'long', 'height',
                  'kl1', 'kh1', 'kl2', 'kh2')
        widgets = {
            'order': forms.HiddenInput(),
            'slab': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        slab = kwargs.get('instance').slab
        self.fields['slab'].initial = slab
        self.fields['long'].initial = slab.long
        self.fields['height'].initial = slab.height
        self.fields['kl1'].initial = slab.kl1
        self.fields['kh1'].initial = slab.kh1
        self.fields['kl2'].initial = slab.kl2
        self.fields['kh2'].initial = slab.kh2

    def save(self, commit=True):
        instance = super().save(commit=False)
        cd = self.cleaned_data
        for k, v in cd.items():
            if k not in ('slab', 'part_number', 'line') and v is not None:
                setattr(instance.slab, k, v)
                instance.slab.save()
        if commit:
            instance.save()
            instance.order.save()
        return instance


class PackageListItemMoveForm(forms.Form):
    options = forms.ChoiceField(label='选项')
    select_slab_ids = forms.CharField(required=False, widget=forms.HiddenInput)


class PackageListImportForm(forms.Form):
    package_list = forms.HiddenInput()
    excel_file = forms.FileField(label='导入的表格文件', required=True)

    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        print(file)
        return file
