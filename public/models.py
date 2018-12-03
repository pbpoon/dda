#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/25
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from public.fields import OrderField

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


class OrderAbstract(models.Model):
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
    invoices = GenericRelation('invoice.OrderInvoiceThrough')

    class Meta:
        abstract = True
        ordering = ['-created']

    def get_quantity(self):
        return sum(item.quantity for item in self.items.all() if item.quantity)

    def get_amount(self):
        return sum(item.get_amount() for item in self.items.all())
