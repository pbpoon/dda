#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def prepend_dollars(dollars):
    if dollars:
        dollars = round(float(dollars), 2)
        return "$%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
    else:
        return ''
register = template.Library()


@register.filter
def model_name(obj):
    try:
        return obj._meta.model_name
    except AttributeError:
        return None


@register.filter
def label_name(obj):
    try:
        return obj._meta.label_lower
    except AttributeError:
        return None

@register.filter
def verbose_name(obj):
    try:
        return obj._meta.verbose_name
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


@register.filter
def money(dollars):
    if dollars:
        dollars = round(float(dollars), 2)
        return "$%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
    else:
        return ''