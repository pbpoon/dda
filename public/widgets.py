#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/11
from django import forms
from django.urls import reverse


class AutocompleteWidget(forms.TextInput):
    url = None

    class Media:
        js = ('js/autocomplete.js',)

    def __init__(self, url=None, *args, **kwargs):
        self.url = url
        super().__init__(*args, **kwargs)

    def build_attrs(self, *args, **kwargs):
        """Build HTML attributes for the widget."""
        attrs = super().build_attrs(*args, **kwargs)

        if self.url is not None:
            if attrs.get('class'):
                attrs['class'] = attrs['class'] + ' autocomplete'
            else:
                attrs['class'] = 'autocomplete'
            attrs['onkeyup'] = 'get_autocomplete("{}")'.format(self.url)

        return attrs

    def _get_url(self):
        if self._url is None:
            return None

        if '/' in self._url:
            return self._url

        return reverse(self._url)

    def _set_url(self, url):
        self._url = url

    url = property(_get_url, _set_url)


class CheckBoxWidget(forms.CheckboxInput):
    template_name = 'public/checkbox.html'