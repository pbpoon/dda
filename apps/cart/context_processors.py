#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/8

from .cart import Cart


def cart(request):
    return {'cart': Cart(request)}
