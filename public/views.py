#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/23
from datetime import datetime
from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseDeleteView, ModelFormMixin, ProcessFormView, FormMixin
from wechatpy.enterprise import WeChatClient

from public.forms import StateForm, ConfirmOptionsForm
from public.widgets import SwitchesWidget, RadioWidget
from .permissions_mixin_views import DynamicPermissionRequiredMixin, ViewPermissionRequiredMixin

STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('cancel', '取消'),
    ('done', '完成'),
)


class GetItemsMixin:
    def get_context_data(self, **kwargs):
        if self.object:
            items = self.object.items.all()
            kwargs.update({'object_list': items})
        return super().get_context_data(**kwargs)


class OrderFormInitialEntryMixin:
    def get_initial(self):
        initial = super().get_initial()
        initial.update({'entry': self.request.user.id})
        return initial


class ModalEditMixin(DynamicPermissionRequiredMixin, OrderFormInitialEntryMixin, ModelFormMixin, View):
    template_name = 'item_form.html'

    def handle_no_permission(self):
        path = self.request.META.get('HTTP_REFERER')
        return HttpResponse(render_to_string('no_premission_modal.html', {'return_path': path}))

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return HttpResponse(render_to_string(self.template_name, {'form': form}))

    def post(self, *args, **kwargs):
        path = self.request.META.get('HTTP_REFERER')
        form = self.get_form()
        msg = '修改' if self.object else '添加'
        if form.is_valid():
            form.save()
            msg += '成功'
            messages.success(self.request, msg)
            # return redirect(path)
            return JsonResponse({'state': 'ok', 'url': path})
        msg += '失败'
        return HttpResponse(render_to_string(self.template_name, {'form': form, 'error': msg}))

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            self.object = self.get_object()
        else:
            self.object = None
        return super().dispatch(request, *args, **kwargs)


class OrderItemEditMixin(ModalEditMixin):
    model = None
    order = None

    def get_initial(self):
        initial = super().get_initial()
        initial['order'] = self.order
        return initial

    def get_order(self, **kwargs):
        if kwargs.get('pk'):
            self.object = self.get_object()
        else:
            self.object = None
        if kwargs.get('order_id'):
            # 取得model的某个field是ForeignKey的model
            return self.model._meta.get_field('order').remote_field.model.objects.get(pk=kwargs.get('order_id'))
        return self.object.order

    def dispatch(self, request, *args, **kwargs):
        self.order = self.get_order(**kwargs)
        return super().dispatch(request, *args, **kwargs)


class OrderItemDeleteMixin(DynamicPermissionRequiredMixin, BaseDeleteView):
    model = None

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER')


# 状态流程
class StateChangeMixin(DynamicPermissionRequiredMixin):
    state_form = StateForm
    model_permission = ['view']

    def handle_no_permission(self):
        path = self.request.META.get('HTTP_REFERER')
        return HttpResponse(render_to_string('no_permissions.html', {'return_path': path}))

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

    def has_change_permission(self):
        meta = self.model._meta
        perms = ['%s.change_%s' % (meta.app_label.lower(), meta.model_name.lower())]
        # perms = list(
        #     map(lambda x: x % (meta.app_label.lower(), meta.model_name.lower()),
        #         ('%s.' + i + '_%s' for i in self.model_permission)))
        return self.request.user.has_perms(perms)

    @transaction.atomic()
    def post(self, *args, **kwargs):
        if not self.has_change_permission():
            return self.handle_no_permission()
        self.object = self.get_object()
        form = self.state_form(self.request.POST)
        state = self.request.POST.get('state')
        if self.object.state == state:
            messages.error(self.request, '该订单状态已为%s' % (state))
            return redirect(self.get_success_url())
        if form.is_valid():
            # 创建数据库事务保存点
            sid = transaction.savepoint()
            is_done, msg = getattr(self, state)()
            if is_done:
                msg += ' 成功设置状态为:{}'.format(dict(STATE_CHOICES).get(state))
                messages.success(self.request, msg)
                # self.object.state = state
                # self.object.save()
                # self.make_invoice()
                return redirect(self.get_success_url())
            # 回滚数据库到保存点
            transaction.savepoint_rollback(sid)
            msg += ' 设置状态为:%s 失败' % (dict(STATE_CHOICES).get(state))
            messages.error(self.request, msg)
        return redirect(self.get_success_url())

    def confirm(self):
        raise ValueError('define confirm')

    def cancel(self):
        raise ValueError('define cancel')

    def draft(self):
        raise ValueError('define draft')



# 前端modal form 选项
class ModalOptionsMixin(BaseDetailView):
    model = None
    template_name = 'item_form.html'
    form_class = ConfirmOptionsForm

    def get_options(self):
        raise ValueError('pls define get_options')

    def get_form(self):
        form = self.form_class()
        form.fields['options'] = forms.ChoiceField(widget=RadioWidget(), choices=self.get_options())
        return form

    def get_content(self):
        return ''

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get(self, *args, **kwargs):
        context = {}
        self.object = self.get_object()
        context['content'] = self.get_content()
        context['form'] = self.get_form()
        return HttpResponse(render_to_string(self.template_name, context))

    def run_option(self, option):
        if hasattr(self, option):
            return getattr(self, option)()
        else:
            return getattr(self, 'do_option')(option)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        url = self.get_success_url()
        option = self.request.POST.get('options')
        is_done, msg = self.run_option(option)
        if is_done:
            messages.success(self.request, msg)
            return JsonResponse({'state': 'ok', 'msg': msg, 'url': url})
        messages.error(self.request, msg)
        return JsonResponse({'state': 'ok', 'msg': msg, 'url': url})


class FilterListView(ViewPermissionRequiredMixin, ListView):
    filter_class = None
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.filter_class:
            self.filter = self.filter_class(self.request.GET, queryset=qs)
            return self.filter.qs.distinct()
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter if self.filter_class else None
        return context


class ContentTypeEditMixin:
    model = None
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
        # initial['entry'] = self.request.user.id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # form.fields['content'].widget.attrs = {'multiple': True}
        form.fields['content_type'].widget = forms.HiddenInput()
        form.fields['object_id'].widget = forms.HiddenInput()
        # form.fields['entry'].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'state': 'ok'})


class SentWxMsgMixin:
    app_name = None
    user_ids = '@all'


    def get_url(self):
        print(self.request)
        return "%s" % (self.request.build_absolute_uri())

    def get_title(self):
        raise ValueError('define get_title')

    def get_description(self):
        raise ValueError('define get_description')

    def sent_msg(self):
        from action.models import WxConf
        if not self.app_name:
            return False
        try:
            wx_conf = WxConf(app_name=self.app_name)
            print(wx_conf,'in')
            client = WeChatClient(wx_conf.corp_id, wx_conf.Secret)
            print(client, '222')
            print(self.get_title(),'title')
            client.message.send_text_card(agent_id=wx_conf.AgentId, user_ids=self.user_ids, title=self.get_title(),
                                          description=self.get_description(),
                                          url=self.get_url())
            print('out')
        except Exception as e:
            pass
        return True
