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

@register.filter
def percentage(value):
    return format(value, "%")

# template_filters.py

@register.filter(name='add_arg')
def template_args(instance, arg):
    """
    stores the arguments in a separate instance attribute
    """
    if not hasattr(instance, "_TemplateArgs"):
        setattr(instance, "_TemplateArgs", [])
    instance._TemplateArgs.append(arg)
    return instance


@register.filter(name='call')
def template_method(instance, method):
    """
    retrieves the arguments if any and calls the method
    """
    method = getattr(instance, method)
    if hasattr(instance, "_TemplateArgs"):
        to_return = method(*instance._TemplateArgs)
        delattr(instance, '_TemplateArgs')
        return to_return
    return method()

# 在模版里面按照下面的方法调用
# {{ instance|template_args:"value1"|template_args:"value2"|template_args:"value3"|template_method:"test_template_call" }}

# 输出结果
# value1, value2, value3
