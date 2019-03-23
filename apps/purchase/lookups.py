#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/8
from django.contrib.auth.models import User
from selectable.base import ModelLookup
from selectable.registry import registry

from partner.models import Partner
from .models import PurchaseOrder


class PurchaseOrderLookup(ModelLookup):
    model = User
    search_fields = ('name__icontains',)


registry.register(PurchaseOrderLookup)
