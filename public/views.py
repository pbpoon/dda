#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/23
from django.contrib import messages
from django.db import transaction
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
    order = None

    def get_initial(self):
        initial = super().get_initial()
        initial['order'] = self.order
        return initial

    def get_order(self, **kwargs):
        if kwargs.get('order_id'):
            # 取得model的某个field是ForeignKey的model
            return self.model._meta.get_field('order').remote_field.model.objects.get(pk=kwargs.get('order_id'))
        return self.object.order

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            self.object = self.get_object()
        else:
            self.object = None
        self.order = self.get_order(**kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return HttpResponse(render_to_string(self.template_name, {'form': form}))

    def post(self, *args, **kwargs):
        form = self.get_form()
        msg = '修改' if self.object else '添加'
        if form.is_valid():
            form.save()
            msg += '成功'
            messages.success(self.request, msg)
            return JsonResponse({'state': 'ok'})
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

    @transaction.atomic()
    def post(self, *args, **kwargs):
        self.object = self.get_object()
        form = self.state_form(self.request.POST)
        if form.is_valid():
            # 创建数据库事务保存点
            state = self.request.POST.get('state')
            sid = transaction.savepoint()
            is_done, msg = getattr(self, state)()
            if is_done:
                msg += ',成功设置状态为:{}'.format(state)
                messages.success(self.request, msg)
                self.object.state = state
                self.object.save()
                self.make_invoice()
                return redirect(self.get_success_url())
            # 回滚数据库到保存点
            transaction.savepoint_rollback(sid)
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
