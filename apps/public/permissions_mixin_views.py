#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/4
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from braces.views import PermissionRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string


class ModalHandleNoPermissionMixin(LoginRequiredMixin):

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            path = self.request.META.get('HTTP_REFERER')
            return HttpResponse(render_to_string('no_permissions.html', {'return_path': path}))
        return super().handle_no_permission()


class ModelPermissionRequiredMixin(ModalHandleNoPermissionMixin):
    model_permission = None

    def get_permission_required(self):
        meta = self.model._meta
        perms = list(
            map(lambda x: x % (meta.app_label.lower(), meta.model_name.lower()),
                ('%s.' + i + '_%s' for i in self.model_permission)))
        return perms


class DynamicPermissionRequiredMixin(ModelPermissionRequiredMixin, PermissionRequiredMixin):
    model_permission = ('add', 'change')


class ViewPermissionRequiredMixin(DynamicPermissionRequiredMixin):
    model_permission = ('view',)


class PostPermissionRequiredMixin(ModelPermissionRequiredMixin):

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        perms = self.get_permission_required()
        return self.request.user.has_perms(perms)

    def post(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().post(request, *args, **kwargs)
