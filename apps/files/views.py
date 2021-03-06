from django import forms
from django.apps import apps
from django.http import JsonResponse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import ModelFormMixin, BaseCreateView, CreateView, BaseDeleteView

from public.permissions_mixin_views import DynamicPermissionRequiredMixin
from public.views import ContentTypeEditMixin, FilterListView, OrderItemDeleteMixin
from .models import Files


class FilesCreateView(DynamicPermissionRequiredMixin, ContentTypeEditMixin, CreateView):
    model = Files
    fields = '__all__'

    def get_initial(self):
        initial = super().get_initial()
        initial['entry'] = self.request.user.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['content'].widget.attrs = {'multiple': True}
        form.fields['entry'].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        files = self.request.FILES.getlist('content')
        cd = form.cleaned_data
        if len(files) > 1:
            for f in files:
                self.model.objects.create(content_type=cd['content_type'],
                                          object_id=cd['object_id'],
                                          content=f,
                                          desc=cd.get('desc'),
                                          entry=cd['entry'])
            return JsonResponse({'state': 'ok'})
        return super().form_valid(form)


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


class FilesDeleteView(OrderItemDeleteMixin):
    model = Files


class FilesDetailView(DynamicPermissionRequiredMixin, DetailView):
    model = Files
