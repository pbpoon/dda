from django import forms
from django.apps import apps
from django.views.generic import DetailView, ListView
from django.views.generic.edit import ModelFormMixin, BaseCreateView, CreateView

from public.views import ContentTypeEditMixin, FilterListView
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


class FilesListView(FilterListView):
    model = Files
    to_obj = None

    def get_to_obj(self):
        app_label_name = self.kwargs.get('app_label_name')
        object_id = self.kwargs.get('object_id')
        app_label, model_name = app_label_name.split('.')
        self.to_obj = apps.get_model(app_label=app_label, model_name=model_name).objects.get(pk=object_id)
        return self.to_obj

    def get_queryset(self):
        qs = super().get_queryset()
        if self.kwargs.get('app_label_name'):
            obj = self.get_to_obj()
            qs = obj.files.all()
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.to_obj:
            context['object'] = self.to_obj
        return context


class FilesDetailView(DetailView):
    model = Files
