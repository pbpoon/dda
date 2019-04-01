#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/11
from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib.admin.widgets import SELECT2_TRANSLATIONS
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.safestring import mark_safe


class Select2CreateModal(autocomplete.ModelSelect2):
    autocomplete_function = 'select2_crate_modal'

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        i18n_name = SELECT2_TRANSLATIONS.get(translation.get_language())
        i18n_file = ('admin/js/vendor/select2/i18n/%s.js' % i18n_name,) if i18n_name else ()
        return forms.Media(
            js=(
                   'admin/js/vendor/jquery/jquery%s.js' % extra,
                   'autocomplete_light/jquery.init.js',
                   'admin/js/vendor/select2/select2.full%s.js' % extra,
               ) + i18n_file + (
                   'autocomplete_light/autocomplete.init.js',
                   'autocomplete_light/forward.js',
                   'autocomplete_light/select2_create_modal.js',  # 后期改的
                   'autocomplete_light/jquery.post-setup.js',
               ),
            css={
                'screen': (
                    'admin/css/vendor/select2/select2%s.css' % extra,
                    'admin/css/autocomplete.css',
                    'css/materialize-select2.css',  # 后期自己加上
                    'autocomplete_light/select2.css',
                ),
            },
        )


class AutocompleteWidget(forms.TextInput):
    url = None

    class Media:
        js = ('js/autocomplete.js',)

    def __init__(self, url=None, onAutocomplete_function=None, *args, **kwargs):
        self.url = url
        self.onAutocomplete_function = onAutocomplete_function if onAutocomplete_function else "set_product"
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

    def render(self, *args, **kwargs):
        html = super().render(*args, **kwargs)
        html += """
        <script>
    function set_product(val) {
    $('input[name=product]').val(val);

    $.ajax({
        url: '/product/product_info',
        method: 'GET',
        data: $('#item_form').serialize(),
        success: function (data) {
            $('input[name=piece]').val(data['piece']);
            $('input[name=quantity]').val(data['quantity']);
        }
    })
}


var DATA;//用来保存get到的数据
// 实例化autocomplete组件
var $ap = $('input.autocomplete').autocomplete({
    onAutocomplete: function (input) {
        // alert("aa" + DATA[input]['id'] + input);

        %(onAutocomplete_function)s(DATA[input]['id'])
    },
    activeIndex: function (i) {
        alert(i)

    }

});

function get_autocomplete(url) {
    var $form = $('form');

    $.ajax({
        url: url,
        data: $form.serialize(),
        method: 'POST',
        success: function (data) {
            $ap.autocomplete("updateData", data);
            $ap.autocomplete("open");
            DATA = data
        }
    })
}
</script>
        """ % {'onAutocomplete_function': self.onAutocomplete_function}

        return mark_safe(html)


class DatePickerWidget(forms.DateInput):
    def build_attrs(self, base_attrs, extra_attrs=None):
        data = super().build_attrs(base_attrs, extra_attrs)
        if data.get('class'):
            data['class'] += ' datepicker'
        else:
            data['class'] = 'datepicker'
        return data


class SwitchesWidget(forms.CheckboxInput):
    template_name = 'public/checkbox.html'


class RadioWidget(forms.RadioSelect):
    option_template_name = 'public/input_option.html'


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


class DateTimePickerWidget(forms.SplitDateTimeWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(date_attrs={'class': 'datepicker'}, time_attrs={'class': 'timepicker'}, *args, **kwargs)


class ChipsWidget(forms.TextInput):
    template_name = 'public/chips.html'

    def format_value(self, value):
        import json
        if value == '' or value is None:
            return None
        string = [{'tag': i.name} for i in value]
        return string
