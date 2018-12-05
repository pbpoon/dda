#!/usr/bin/env python
# -*- coding: utf-8 -*-
from decimal import Decimal
from django.conf import settings

from product.models import Product, Slab, PackageList


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product_id, piece=None, quantity=None, slab_id_list=None):
        product = Product.objects.get(pk=product_id)
        if product.type == 'slab':
            if not slab_id_list:
                return False
            piece = len(slab_id_list)
            quantity = sum(slab.get_quantity() for slab in Slab.objects.filter(id__in=slab_id_list))
        elif product.type == 'block':
            piece = 1
            quantity = quantity
        line = len(self.cart) + 1 if product_id not in self.cart else self.cart[product_id]['line']
        self.cart[product_id] = {'line': line, 'piece': piece, 'quantity': str(quantity),
                                 'slab_id_list': slab_id_list}
        self.save()

    def save(self):
        self.session.modified = True

    def get_select_slabs(self):
        lst = []
        for i in self.cart.values():
            lst.extend(i['slab_id_list'])
        return lst

    def remove(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clean(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def __iter__(self):
        product_id_list = self.cart.keys()
        products = Product.objects.filter(id__in=product_id_list)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
            if product.type == 'slab':
                cart[str(product.id)]['part'] = {s.part_number for s in
                                                 Slab.objects.filter(id__in=cart[str(product.id)]['slab_id_list'])}

        for item in cart.values():
            item['quantity'] = item['quantity']
            yield item

    def __len__(self):
        return len(self.cart)
