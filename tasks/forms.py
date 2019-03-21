#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/3/18
from django import forms

from public.widgets import SwitchesWidget, DateTimePickerWidget
from tasks.models import Tasks
from dal import autocomplete


class TasksCreateForm(forms.ModelForm):
    file = forms.FileField(required=False, label='附件', widget=forms.FileInput(attrs={'multiple': True}))
    time = forms.SplitDateTimeField(label='提醒时间', widget=DateTimePickerWidget())

    class Meta:
        model = Tasks
        fields = ('is_complete', 'name', 'time', 'handler', 'entry', 'content_type', 'object_id', 'file')
        widgets = {
            'name': autocomplete.ListSelect2(url='tasks_autocomplete_list', attrs={'class': 'browser-default'}),
            'is_complete': SwitchesWidget(),
            'entry': forms.HiddenInput(),
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }
