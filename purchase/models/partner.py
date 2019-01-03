#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/3
from django.db import models
from partner.models import Partner


class SupplierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='supplier', is_invoice=False, is_production=False)


class Supplier(Partner):
    objects = SupplierManager()

    class Meta:
        proxy = True
