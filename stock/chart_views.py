#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/20
from chartjs.views import lines, pie, columns
from django.db.models import Sum, Count

from product.models import Product
from .models import Stock


class StockProductTypeChartMixin(pie.HighChartPieView):

    def get_providers(self):
        return ['block', 'semi_slab', 'slab']

    def get_data(self):
        Stock.objects.annotate(quantity_total=Sum('quantity'), count_total=Count('product')).values('product__type')