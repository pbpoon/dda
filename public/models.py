#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/25
import collections

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from public.fields import OrderField
from public.middleware import current_user

STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('done', '完成'),
    ('cancel', '取消'),
)
INVOICE_USAGE_CHOICES = (
    ('货款', '货款'),
    ('加工费', '加工费'),
    ('运费', '运费'),
    ('装车费', '装车费'),
    ('佣金', '佣金'),
)


class HasChangedMixin:
    """ this mixin gives subclasses the ability to set fields for which they want to monitor if the field value changes """
    monitor_fields = []
    exclude_fields = ('created', 'updated', 'id', 'sales_order_item', 'purchase_order_item', 'package_list')

    def __init__(self, *args, **kwargs):
        # self.field_trackers = {}
        super().__init__(*args, **kwargs)
        if not self.monitor_fields:
            self.monitor_fields = [f.name for f in self._meta.fields]
        for field in self.monitor_fields:
            if field in self.exclude_fields:
                continue
            setattr(self, '__original_%s' % field, self.get_field_display(field))

    def get_user(self):
        return current_user.get_current_user()

    def get_field_display(self, field):
        if hasattr(self, 'get_%s_display' % field):
            return getattr(self, 'get_%s_display' % field)()
        return getattr(self, field, None)

    def changed_data(self):
        """
        :return: `list` of `str` the names of all monitor_fields which have changed
        """

        changed_data = {}
        for field in self.monitor_fields:
            if field in self.exclude_fields:
                continue
            orig = '__original_%s' % field
            if hasattr(self, 'line'):
                changed_data['行'] = getattr(self, 'line')
            if getattr(self, orig) != self.get_field_display(field):
                if getattr(self, orig, None) is None:
                    changed_data[self._meta.get_field(field).verbose_name] = '%s' % (
                        self.get_field_display(field))
                else:
                    changed_data[self._meta.get_field(field).verbose_name] = '%s => %s' % (
                        getattr(self, orig), self.get_field_display(field))
        return changed_data

    def all_data(self):
        data = {}
        for f in self._meta.fields:
            if f.name in self.monitor_fields:
                if f.name in self.exclude_fields:
                    continue
                data[f.verbose_name] = self.get_field_display(f.name)
        return data

    def ge_logs_title(self):
        data = {}
        data['状态'] = self.order.get_state_display()
        data['数量'] = getattr(self.order, 'quantity', None)
        data['金额'] = getattr(self.order, 'amount', None)
        return data

    def get_data(self):
        data = self.changed_data()
        if data:
            if not hasattr(self, 'order'):
                return data
            if self._meta.get_field('order').get_internal_type() == 'ForeignKey':
                title = self.ge_logs_title()
                title['明细行'] = data
                return title
        return data

    def format_logs(self, data):
        html = '<ul>'
        for k, v in data.items():
            if isinstance(v, dict):
                html += '<li>%s:%s</li>' % (k, self.format_logs(v))
            else:
                html += '<li>%s:%s</li>' % (k, v)
        html += '</ul>'
        return html

    def get_logs(self):
        data = self.get_data()
        if data:
            return self.format_logs(data)
        return data

    def create_comment(self, **kwargs):
        content = ''
        comment = kwargs.get('comment')
        if comment:
            content += comment
        logs = self.get_logs()
        if logs:
            if comment:
                comment += '<br>'
            content += '%s' % (logs)
        if content:
            self.comments.create(user=self.get_user(), content=content)


class OrderItemSaveCreateCommentMixin(HasChangedMixin):
    def save(self, *args, **kwargs):
        if not self.pk:
            comment = '创建'
        else:
            comment = '修改'
        super().save(*args, **kwargs)
        if comment:
            if self._meta.get_field('order').get_internal_type() == 'ForeignKey':
                comment += '明细行<br>%s' % (self.get_logs())
                self.order.create_comment(**{'comment': comment})
            else:
                comment += '订单'
                self.create_comment(**{'comment': comment})

    def delete(self, *args, **kwargs):
        if self._meta.get_field('order').get_internal_type() == 'ForeignKey':
            comment = '<s>删除明细行</s>:<br>%s' % (self.format_logs(self.all_data()))
            self.order.create_comment(**{'comment': comment})
        super().delete(*args, **kwargs)


class OrderAbstract(HasChangedMixin, models.Model):
    state = models.CharField('状态', choices=STATE_CHOICES, max_length=20, default='draft')
    order = OrderField(order_str=None, max_length=26, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='业务伙伴')
    date = models.DateField('日期')
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    handler = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='经办人',
                                related_name='%(class)s_handler')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')
    comments = GenericRelation('comment.Comment')
    invoices = GenericRelation('invoice.Invoice')
    files = GenericRelation('files.Files')

    # operation_logs = GenericRelation('comment.OperationLogs')

    class Meta:
        abstract = True
        ordering = ['-created']

    @property
    def invoice_usage(self):
        return self._get_invoice_usage()

    def _get_invoice_usage(self):
        raise ValueError('define invoice_usage')

    def get_quantity(self):
        return sum(item.quantity for item in self.items.all() if item.quantity)

    def get_amount(self):
        return sum(item.get_amount() for item in self.items.all())

    def get_total(self):
        """
        template使用方式
        {% for key, item in object.get_total.items %}
        {{ key }}:{% if item.part %}{{ item.part }}夹 / {% endif %}{{ item.piece }}件 / {{ item.quantity }}{{ item.uom }}<br>
        {% endfor %}
        """
        # if not self.items.all():
        #     return
        total = {}
        for item in self.items.all():
            if not item.product:
                continue
            d = collections.defaultdict(lambda: 0)
            a = total.setdefault(item.product.get_type_display(), d)
            a['piece'] += item.piece
            a['quantity'] += item.quantity
            a['part'] += item.package_list.get_part() if item.package_list else 0
            a['uom'] = item.uom
        return total

    def get_files(self):
        files = self.files.all()
        if files.count() > 10:
            files = files[:10]
        return files
