from django import forms
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView, UpdateView

from public.views import ContentTypeEditMixin
from .models import Comment


class CommentEditMixin(ContentTypeEditMixin):
    def get_initial(self):
        initial = super().get_initial()
        initial['user'] = self.request.user.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['user'].widget = forms.HiddenInput()
        form.fields['content'].widget.attrs = {'class': 'materialize-textarea','rows': '10'}
        return form


class CommentCreateView(CommentEditMixin, CreateView):
    model = Comment
    fields = '__all__'


class CommentUpdateView(CommentEditMixin, UpdateView):
    model = Comment


class CommentReplyView(CreateView):
    pass
