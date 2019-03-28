#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/3/18
from django import forms

from public.widgets import SwitchesWidget, DateTimePickerWidget
from .models import Tasks
from dal import autocomplete


class TasksCreateForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())
    file = forms.FileField(required=False, label='附件', widget=forms.FileInput(attrs={'multiple': True}))
    time = forms.SplitDateTimeField(label='提醒时间', widget=DateTimePickerWidget())

    class Meta:
        model = Tasks
        fields = ('id', 'is_complete', 'name', 'time', 'handler', 'entry', 'content_type', 'object_id', 'file')
        widgets = {
            'name': autocomplete.ListSelect2(url='tasks_autocomplete_list',
                                             attrs={'class': 'browser-default'},
                                             forward=['id']),
            'is_complete': SwitchesWidget(),
            'entry': forms.HiddenInput(),
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get('name', None):
            namePK = self.initial['name']
            name = Tasks.objects.get(pk=namePK)
            self.fields['name'].widget = autocomplete.ListSelect2(url='tasks_autocomplete_list',
                                                                  attrs={'class': 'browser-default'},
                                                                  forward=['id'], extra_context={'values': [namePK],
                                                                                                 'choices': [name]})
