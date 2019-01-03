from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from django.views.generic.edit import ModelFormMixin, BaseCreateView, CreateView
from .models import Files


class FilesEditMixin:
    model = Files
    template_name = 'item_form.html'
    fields = '__all__'
    to_obj = None

    def get_to_obj(self):
        if self.object:
            return self.object.object
        app_label_name = self.kwargs.get('app_label_name')
        object_id = self.kwargs.get('object_id')
        app_label, model_name = app_label_name.split('.')
        return apps.get_model(app_label=app_label, model_name=model_name).objects.get(pk=object_id)

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            self.object = self.get_object()
        else:
            self.object = None
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        self.to_obj = self.get_to_obj()
        initial = super().get_initial()
        initial['content_type'] = ContentType.objects.get_for_model(self.to_obj)
        initial['object_id'] = self.to_obj.id
        initial['entry'] = self.request.user.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # form.fields['content'].widget.attrs = {'multiple': True}
        form.fields['content_type'].widget = forms.HiddenInput()
        form.fields['object_id'].widget = forms.HiddenInput()
        form.fields['entry'].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'state': 'ok'})


class FilesCreateView(FilesEditMixin, CreateView):
    pass
