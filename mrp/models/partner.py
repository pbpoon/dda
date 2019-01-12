#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/3
from django.db import models
from django.db.models import Q
from django.urls import reverse

from partner.models import Partner


class MrpSupplierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(Q(type='production') | Q(type='service'))


class MrpSupplier(Partner):
    objects = MrpSupplierManager()

    class Meta:
        proxy = True
        verbose_name = '生产/服务商资料'
        app_label = 'partner'

    def get_update_url(self):
        return reverse('pro_ser_supplier_update', args=[self.id])
