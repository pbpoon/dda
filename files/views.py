from django import forms
from django.views.generic.edit import ModelFormMixin, BaseCreateView, CreateView

from public.views import ContentTypeEditMixin
from .models import Files


class FilesCreateView(ContentTypeEditMixin, CreateView):
    model = Files
    fields = '__all__'

    def get_initial(self):
        initial = super().get_initial()
        initial['entry'] = self.request.user.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['entry'].widget = forms.HiddenInput()
        return form
