#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/4
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string


class DynamicPermissionRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    model_permission = ('add', 'change', 'delete')

    def get_permission_required(self):
        meta = self.model._meta
        perms = list(
            map(lambda x: x % (meta.app_label.lower(), meta.model_name.lower()),
                ('%s.' + i + '_%s' for i in self.model_permission)))
        return perms


class ViewPermissionRequiredMixin(DynamicPermissionRequiredMixin):
    model_permission = ('view',)

    def handle_no_permission(self):
        path = self.request.META.get('HTTP_REFERER')
        return HttpResponse(render_to_string('no_permissions.html', {'return_path': path}))
