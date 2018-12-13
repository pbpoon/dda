#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/11
from django import forms
from django.urls import reverse
from django.core.exceptions import ValidationError


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


class OptionalChoiceWidget(forms.MultiWidget):
    def decompress(self, value):
        # this might need to be tweaked if the name of a choice != value of a choice
        if value:  # indicates we have a updating object versus new one
            if value in [x[0] for x in self.widgets[0].choices]:
                return [value, ""]  # make it set the pulldown to choice
            else:
                return ["", value]  # keep pulldown to blank, set freetext
        return ["", ""]  # default for new object


class OptionalChoiceField(forms.MultiValueField):
    def __init__(self, choices, max_length=80, *args, **kwargs):
        """ sets the two fields as not required but will enforce that (at least) one is set in compress """
        fields = (forms.ChoiceField(choices=choices, required=False),
                  forms.CharField(required=False))
        self.widget = OptionalChoiceWidget(widgets=[f.widget for f in fields])
        super(OptionalChoiceField, self).__init__(required=False, fields=fields, *args, **kwargs)

    def compress(self, data_list):
        """ return the choicefield value if selected or charfield value (if both empty, will throw exception """
        if not data_list:
            raise ValidationError('Need to select choice or enter text for this field')
        return data_list[0] or data_list[1]


"""
使用方法
class DemoForm(forms.ModelForm):
    name = OptionalChoiceField(choices=(("","-----"),("1","1"),("2","2")))
    value = forms.CharField(max_length=100)
    class Meta:
        model = Dummy
"""
