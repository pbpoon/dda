#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/23
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render_to_response, redirect
from django.views import View
from django.views.generic.edit import BaseDeleteView

from public.forms import StateForm


# ajax编辑item
class OrderItemEditMixin(View):
    form_class = None
    template_name = 'item_form.html'
    model = None

    def get_initial(self):
        initial = {}
        order_id = self.request.GET.get('order_id', None)
        if order_id:
            initial['order'] = order_id
        return initial

    def get_item(self):
        item_id = self.request.GET.get('item_id', None) or self.request.POST.get('item_id', None)
        item = None
        if item_id:
            item = self.model.objects.get(pk=item_id)
        return item

    def get_form(self, *args, **kwargs):
        return self.form_class(*args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.get_form(initial=self.get_initial(), instance=self.get_item())
        item_id = self.request.GET.get('item_id', None)
        data = {'item_form': form}
        if item_id:
            data['item_id'] = item_id
        return render_to_response(self.template_name, data)

    def post(self, *args, **kwargs):
        item = self.get_item()
        # 如果有item就是编辑状态，否则是新建
        msg = ""
        if item:
            form = self.get_form(self.request.POST, instance=self.get_item())
            msg = '修改'
        else:
            form = self.get_form(self.request.POST)
            msg = '添加'
        if form.is_valid():
            form.save(commit=False)
            form.entry = self.request.user
            form.save()
            # path = self.request.META.get('HTTP_REFERER')
            msg += '成功'
            messages.success(self.request, msg)
            return JsonResponse({'status': 'SUCCESS'})
        msg += '失败'
        # messages.error(self.request, msg)
        return render_to_response(self.template_name, {'item_form': form, 'error': msg})


class OrderItemDeleteMixin(BaseDeleteView):
    model = None

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER')


# 状态流程
class StateChangeMixin:
    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_btn_visible(self, state):
        return {s: s != state for s in ('draft', 'confirm', 'cancel')}

    def get_context_data(self, **kwargs):
        state_form = StateForm()
        state = self.object.state
        kwargs.update({'state_form': state_form,
                       'btn_visible': self.get_btn_visible(state)})
        return super(StateChangeMixin, self).get_context_data(**kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        post = self.request.POST
        if 'draft' in post:
            return self.draft()
        elif 'confirm' in post:
            return self.confirm()
        elif 'cancel' in post:
            return self.cancel()
        return redirect(self.get_success_url())

    def confirm(self):
        pass
        return redirect(self.get_success_url())

    def cancel(self):
        pass
        return redirect(self.get_success_url())

    def draft(self):
        pass
        return redirect(self.get_success_url())
