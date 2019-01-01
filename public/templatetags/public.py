#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def format_money(dollars, format=None):
    if not format:
        format = '¥'
    if dollars:
        dollars = round(float(dollars), 2)
        return "%s%s%s" % (format, intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])
    else:
        return ''


@register.filter
def format_percentage(number):
    if number:
        number = float(number) * 100
        value = str(number).split('.')[0]
        return '{}%'.format(value)


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


# 分页解释request path
@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()
