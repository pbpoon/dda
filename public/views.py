#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/23
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views import View
from django.views.generic.edit import BaseDeleteView, ModelFormMixin, ProcessFormView, FormMixin

from public.forms import StateForm


class GetItemsMixin:
    def get_context_data(self, **kwargs):
        if self.object:
            items = self.object.items.all()
            kwargs.update({'object_list': items})
        return super().get_context_data(**kwargs)


class OrderFormInitialEntryMixin:
    def get_initial(self):
        data = super().get_initial()
        data.update({'entry': self.request.user.id})
        return data


class OrderItemEditMixin(OrderFormInitialEntryMixin, ModelFormMixin, View):
    template_name = 'item_form.html'
    model = None

    def get_order_id(self):
        return self.request.GET.get('order_id', None) or self.request.POST.get('order', None)

    def get_initial(self):
        # 当是新建的item项目的时候，有个order_id的参数在js函数add_item()传入
        initial = super().get_initial()
        order_id = self.get_order_id()
        if order_id:
            initial['order'] = order_id
        return initial

    def dispatch(self, request, *args, **kwargs):
        pk = self.request.GET.get('item_id', None) or self.request.POST.get('item_id', None)
        if pk:
            self.kwargs.update({'pk': pk})
            self.object = self.get_object()
        else:
            self.object = None
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return HttpResponse(render_to_string(self.template_name, {'form': form}))

    def post(self, *args, **kwargs):
        form = self.get_form()
        msg = '修改' if self.object else '添加'
        if form.is_valid():
            form.save()
            # path = self.request.META.get('HTTP_REFERER')
            msg += '成功'
            messages.success(self.request, msg)
            return JsonResponse({'status': 'SUCCESS'})
        msg += '失败'
        return HttpResponse(render_to_string(self.template_name, {'form': form, 'error': msg}))


class OrderItemDeleteMixin(BaseDeleteView):
    model = None

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER')


# 状态流程
class StateChangeMixin:
    state_form = StateForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_btn_visible(self, state):
        return {s: s != state for s in ('draft', 'confirm', 'cancel')}

    def get_context_data(self, **kwargs):
        state_form = self.state_form()
        state = self.object.state
        kwargs.update({'state_form': state_form,
                       'btn_visible': self.get_btn_visible(state)})
        return super(StateChangeMixin, self).get_context_data(**kwargs)

    def make_invoice(self):
        return True

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        form = self.state_form(self.request.POST)
        if form.is_valid():
            state = self.request.POST.get('state')
            is_done, msg = getattr(self, state)()
            if is_done:
                msg += ',成功设置状态为:{}'.format(state)
                messages.success(self.request, msg)
                self.object.state = state
                self.object.save()
                self.make_invoice()
            msg += ',设置状态为:{} 失败'.format(state)
            messages.error(self.request, msg)
        return redirect(self.get_success_url())

    def confirm(self):
        raise ValueError('define confirm')

    def cancel(self):
        if self.object.state == 'draft':
            self.object.state = 'cancel'
            self.object.save()
            return True, ''
        return False, ''

    def draft(self):
        raise ValueError('define draft')
