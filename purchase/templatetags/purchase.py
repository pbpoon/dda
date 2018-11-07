#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import template

register = template.Library()


@register.filter
def model_name(obj):
    try:
        return obj._meta.model_name
    except AttributeError:
        return None
