#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/3
from django.db import models
from django.urls import reverse

from partner.models import Partner


class SupplierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='supplier')

    def create(self, **kwargs):
        kwargs['type'] = 'supplier'
        return super().create(**kwargs)


class Supplier(Partner):
    objects = SupplierManager()

    class Meta:
        proxy = True
        verbose_name = '供应商'

    def save(self, *args, **kwargs):
        self.type = 'supplier'
        super().save(*args, **kwargs)

    def get_orders(self):
        orders = self.purchase_order.all()
        if orders.count() > 10:
            orders = orders[:10]
        return orders

    def get_update_url(self):
        return reverse('supplier_update', args=[self.id])
