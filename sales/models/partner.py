#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/3
from django.db import models
from partner.models import Partner


class CustomerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='customer')


class Customer(Partner):
    objects = CustomerManager()

    class Meta:
        proxy = True
