#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/3
from django.db import models
from django.urls import reverse

from partner.models import Partner


class CustomerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='customer')

    def create(self, **kwargs):
        kwargs['type'] = 'customer'
        return super().create(**kwargs)


class Customer(Partner):
    objects = CustomerManager()

    class Meta:
        proxy = True
        app_label = 'partner'
        verbose_name = '客户'

    def save(self, *args, **kwargs):
        self.type = 'customer'
        super().save(*args, **kwargs)

    def get_last_order_address(self):
        last_order = self.sales_order.last()
        if last_order:
            return last_order.get_address()
        return None

    def get_orders(self):
        orders = self.sales_order.all()
        if orders.count() > 10:
            orders = orders[:10]
        return orders

    def get_update_url(self):
        return reverse('customer_update', args=[self.id])

    def get_delete_url(self):
        return reverse('customer_delete', args=[self.id])
